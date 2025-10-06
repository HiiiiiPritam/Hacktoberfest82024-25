#!/usr/bin/env python3
"""
Start all Orkes workers (like the Node.js version)
"""
import os
import sys
import asyncio
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_workers():
    """Start all workers like in the Node.js version"""
    print("=== Starting Video Generation Workers ===")
    
    try:
        from orkes_client import orkes_client
        from workers import ScriptWorker, ImageWorker, AudioWorker, VideoWorker
        
        print("[INFO] Importing workers...")
        
        # Create worker instances
        script_worker = ScriptWorker()
        image_worker = ImageWorker()
        audio_worker = AudioWorker()
        video_worker = VideoWorker()
        
        print("[OK] Worker instances created")
        
        # Add workers to client
        orkes_client.add_worker(script_worker)
        orkes_client.add_worker(image_worker) 
        orkes_client.add_worker(audio_worker)
        orkes_client.add_worker(video_worker)
        
        print(f"[OK] Added {len(orkes_client.workers)} workers to Orkes client")
        print("[INFO] Worker task definitions:")
        for worker in orkes_client.workers:
            print(f"  - {worker.get_task_definition_name()}")
        
        print("\n[INFO] Starting workers...")
        print("[INFO] Workers are now polling for tasks...")
        print("[INFO] You can now start workflows from another terminal")
        print("[INFO] Press Ctrl+C to stop workers")
        
        # Start workers (this will block)
        await orkes_client.start_workers()
        
    except KeyboardInterrupt:
        print("\n[INFO] Received shutdown signal")
    except Exception as e:
        print(f"[ERROR] Failed to start workers: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[INFO] Stopping workers...")
        orkes_client.stop_workers()
        print("[INFO] All workers stopped")

if __name__ == "__main__":
    print("Starting Orkes Workers...")
    asyncio.run(start_workers())