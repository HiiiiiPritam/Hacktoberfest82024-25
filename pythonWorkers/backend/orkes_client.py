import asyncio
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient
from conductor.client.orkes.orkes_task_client import OrkesTaskClient
from conductor.client.worker.worker_interface import WorkerInterface
from config import get_conductor_config
import logging

logger = logging.getLogger(__name__)

class OrkesClient:
    def __init__(self):
        self.configuration = get_conductor_config()
        self.workflow_client = OrkesWorkflowClient(self.configuration)
        self.task_client = OrkesTaskClient(self.configuration)
        self.task_handler = None
        self.workers = []
        
    def add_worker(self, worker: WorkerInterface):
        """Add a worker to the client"""
        self.workers.append(worker)
        
    async def start_workers(self):
        """Start polling for tasks"""
        try:
            self.task_handler = TaskHandler(
                workers=self.workers,
                configuration=self.configuration,
                scan_for_annotated_workers=False,
                import_modules=[]
            )
            
            logger.info(f"Starting {len(self.workers)} workers...")
            self.task_handler.start_processes()
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting workers: {e}")
            raise
            
    def stop_workers(self):
        """Stop all workers"""
        if self.task_handler:
            self.task_handler.stop_processes()
            logger.info("All workers stopped")

    async def start_workflow(self, workflow_name: str, input_data: dict, version: int = 1):
        """Start a workflow execution"""
        try:
            workflow_id = self.workflow_client.execute_workflow(
                name=workflow_name,
                input=input_data,
                version=version
            )
            logger.info(f"Started workflow {workflow_name} with ID: {workflow_id}")
            return workflow_id
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            raise
            
    async def get_workflow_status(self, workflow_id: str):
        """Get workflow execution status"""
        try:
            return self.workflow_client.get_workflow(workflow_id)
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            raise
            
    def terminate_workflow(self, workflow_id: str):
        """Terminate a workflow"""
        try:
            self.workflow_client.terminate_workflow(workflow_id, reason="Terminated by user")
            logger.info(f"Terminated workflow: {workflow_id}")
        except Exception as e:
            logger.error(f"Error terminating workflow: {e}")
            raise

# Global client instance
orkes_client = OrkesClient()