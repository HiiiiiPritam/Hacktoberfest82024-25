import asyncio
import logging
import threading
import os
from uuid import uuid4
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from orkes_client import orkes_client
from workers import ScriptWorker, ImageWorker, AudioWorker, VideoWorker
from utils.file_handler import FileHandler
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS so the Next.js frontend (localhost:3000) can call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    topic: str
    duration: int
    voice: str = "nova"

class RunResponse(BaseModel):
    run_id: str

class Run(BaseModel):
    run_id: str
    status: str
    steps: Dict[str, str]
    artifacts: List[str]
    workflow_id: Optional[str] = None
    orkes_status: Optional[str] = None

# In-memory store of runs
runs: Dict[str, Run] = {}

# Ordered pipeline steps - updated to match actual Orkes workflow
PIPELINE_STEPS = [
    "generate_script",
    "generate_images", 
    "generate_audio",
    "assemble_video"
]

# Global variables for worker management
worker_thread = None
workers_started = False

@app.on_event("startup")
async def startup_event():
    """Initialize file directories on startup"""
    FileHandler.ensure_directories()
    logger.info("Application started - directories initialized")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up resources on shutdown"""
    global worker_thread, workers_started
    
    if workers_started and orkes_client:
        logger.info("Stopping Orkes workers...")
        orkes_client.stop_workers()
        workers_started = False
        
    # Clean up temp files
    FileHandler.cleanup_temp_files()
    logger.info("Application shutdown complete")

@app.get("/health")
async def health_check():
    return {
        "ok": True,
        "workers_started": workers_started,
        "temp_dir_exists": os.path.exists(Config.TEMP_DIR),
        "output_dir_exists": os.path.exists(Config.OUTPUT_DIR)
    }

@app.post("/runs", response_model=RunResponse)
async def create_run(run_request: RunRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid4())
    steps = {name: "PENDING" for name in PIPELINE_STEPS}
    run = Run(run_id=run_id, status="QUEUED", steps=steps, artifacts=[])
    runs[run_id] = run

    # Start workers if not already started
    await ensure_workers_started()
    
    # Start Orkes workflow
    background_tasks.add_task(_start_orkes_workflow, run_id, run_request)
    
    return {"run_id": run_id}

@app.get("/runs/{run_id}", response_model=Run)
async def get_run_status(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run

@app.post("/runs/{run_id}/terminate")
async def terminate_run(run_id: str):
    """Terminate a running workflow"""
    run = runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    
    if run.workflow_id:
        try:
            orkes_client.terminate_workflow(run.workflow_id)
            run.status = "TERMINATED"
            logger.info(f"Terminated workflow {run.workflow_id} for run {run_id}")
        except Exception as e:
            logger.error(f"Failed to terminate workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to terminate workflow: {e}")
    else:
        run.status = "TERMINATED"
    
    return {"message": "Run terminated successfully"}

@app.get("/artifacts/{file_path:path}")
async def serve_artifact(file_path: str):
    """Serve generated artifacts (images, audio, project files)"""
    # Security check - only allow files from temp and output directories
    if not (file_path.startswith('temp/') or file_path.startswith('output/')):
        raise HTTPException(status_code=403, detail="Access denied")
    
    full_path = os.path.join(os.getcwd(), file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(full_path)

@app.get("/workflows/status")
async def get_workflow_status():
    """Get status of all running workflows"""
    active_runs = [run for run in runs.values() if run.status in ["QUEUED", "RUNNING"]]
    completed_runs = [run for run in runs.values() if run.status == "COMPLETED"]
    failed_runs = [run for run in runs.values() if run.status == "FAILED"]
    
    return {
        "workers_started": workers_started,
        "active_runs": len(active_runs),
        "completed_runs": len(completed_runs), 
        "failed_runs": len(failed_runs),
        "total_runs": len(runs)
    }


async def _start_orkes_workflow(run_id: str, run_request: RunRequest):
    """Start Orkes workflow for video generation"""
    try:
        run = runs.get(run_id)
        if not run:
            return
            
        # Start the workflow with input data
        workflow_input = {
            "topic": run_request.topic,
            "duration": run_request.duration,
            "voice": run_request.voice,
            "run_id": run_id
        }
        
        # Start the real Orkes workflow
        workflow_id = await orkes_client.start_workflow("video_generation_workflow", workflow_input)
        run.workflow_id = workflow_id
        
        logger.info(f"Started Orkes workflow {workflow_id} for run {run_id} with topic: {run_request.topic}")
        run.status = "RUNNING"
        
        # Monitor the real workflow progress
        await _monitor_workflow_progress(run_id, workflow_id)
        
    except Exception as e:
        logger.error(f"Failed to start workflow for run {run_id}: {e}")
        if run_id in runs:
            runs[run_id].status = "FAILED"

async def _monitor_workflow_progress(run_id: str, workflow_id: str):
    """Monitor real Orkes workflow progress"""
    run = runs.get(run_id)
    if not run:
        return
        
    try:
        max_wait_time = 10 * 60  # 10 minutes
        poll_interval = 5  # 5 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # Get workflow status from Orkes
                workflow_status = await orkes_client.get_workflow_status(workflow_id)
                run.orkes_status = workflow_status.get("status", "UNKNOWN")
                
                # Update individual task statuses
                if "tasks" in workflow_status:
                    for task in workflow_status["tasks"]:
                        task_type = task.get("taskType")
                        task_status = task.get("status", "UNKNOWN")
                        
                        if task_type in run.steps:
                            run.steps[task_type] = task_status
                
                # Check if workflow is complete
                if run.orkes_status == "COMPLETED":
                    run.status = "COMPLETED"
                    # Find generated artifacts
                    await _collect_artifacts(run_id, workflow_status)
                    logger.info(f"Workflow {workflow_id} completed for run {run_id}")
                    break
                elif run.orkes_status in ["FAILED", "TIMED_OUT", "TERMINATED"]:
                    run.status = "FAILED"
                    logger.error(f"Workflow {workflow_id} failed with status: {run.orkes_status}")
                    break
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                elapsed_time += poll_interval
                
            except Exception as poll_error:
                logger.error(f"Error polling workflow {workflow_id}: {poll_error}")
                await asyncio.sleep(poll_interval)
                elapsed_time += poll_interval
        
        # Timeout handling
        if elapsed_time >= max_wait_time:
            logger.warning(f"Workflow monitoring timed out for run {run_id}")
            run.status = "TIMEOUT"
        
    except Exception as e:
        logger.error(f"Workflow monitoring failed for run {run_id}: {e}")
        run.status = "FAILED"

async def _collect_artifacts(run_id: str, workflow_status: dict):
    """Collect artifacts from completed workflow"""
    run = runs.get(run_id)
    if not run:
        return
        
    artifacts = []
    
    # Look for output files in temp directory
    temp_dir = Config.TEMP_DIR
    if os.path.exists(temp_dir):
        for file_name in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file_name)
            if os.path.isfile(file_path):
                artifacts.append(f"temp/{file_name}")
    
    # Look for output files in output directory  
    output_dir = Config.OUTPUT_DIR
    if os.path.exists(output_dir):
        for file_name in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file_name)
            if os.path.isfile(file_path):
                artifacts.append(f"output/{file_name}")
    
    run.artifacts = artifacts
    logger.info(f"Collected {len(artifacts)} artifacts for run {run_id}")

async def ensure_workers_started():
    """Ensure Orkes workers are started"""
    global workers_started, worker_thread
    
    if not workers_started:
        logger.info("Starting Orkes workers...")
        
        # Add workers to the client
        orkes_client.add_worker(ScriptWorker())
        orkes_client.add_worker(ImageWorker())
        orkes_client.add_worker(AudioWorker())
        orkes_client.add_worker(VideoWorker())
        
        # Start workers in a separate thread
        worker_thread = threading.Thread(target=_start_workers_sync, daemon=True)
        worker_thread.start()
        
        workers_started = True
        logger.info("Orkes workers started successfully")

def _start_workers_sync():
    """Start workers synchronously in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(orkes_client.start_workers())
    except Exception as e:
        logger.error(f"Failed to start workers: {e}")
    finally:
        loop.close()
