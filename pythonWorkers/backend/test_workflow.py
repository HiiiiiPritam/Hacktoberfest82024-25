#!/usr/bin/env python3
"""
Test Orkes workflow creation and execution
"""
import asyncio
import sys
import os
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orkes_client import orkes_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_workflow_operations():
    """Test workflow operations with Orkes"""
    print("=== Testing Orkes Workflow Operations ===")
    
    try:
        print("[1] Testing workflow start...")
        
        # Test data
        workflow_input = {
            "topic": "Test Topic",
            "duration": 5,
            "voice": "nova",
            "run_id": "test_run_123"
        }
        
        try:
            workflow_id = await orkes_client.start_workflow("video_generation_workflow", workflow_input)
            print(f"[OK] Workflow started with ID: {workflow_id}")
            
            # Wait a moment for workflow to initialize
            await asyncio.sleep(3)
            
            print("[2] Testing workflow status...")
            status = await orkes_client.get_workflow_status(workflow_id)
            print(f"[OK] Workflow status: {status.get('status', 'UNKNOWN')}")
            
            # Print task statuses
            if "tasks" in status:
                print(f"[INFO] Found {len(status['tasks'])} tasks:")
                for task in status["tasks"]:
                    task_type = task.get("taskType", "unknown")
                    task_status = task.get("status", "unknown") 
                    print(f"  - {task_type}: {task_status}")
            else:
                print("[INFO] No tasks found in workflow status")
            
            return True
            
        except Exception as workflow_error:
            print(f"[ERROR] Workflow operation failed: {workflow_error}")
            
            # Check if it's because the workflow definition doesn't exist
            if "not found" in str(workflow_error).lower() or "does not exist" in str(workflow_error).lower():
                print("[INFO] This suggests the 'video_generation_workflow' doesn't exist in Orkes")
                print("[INFO] You need to create the workflow definition in Orkes Conductor")
                return False
            else:
                raise workflow_error
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_workflow_definition():
    """Print the workflow definition that should be created in Orkes"""
    print("\n=== Workflow Definition Needed in Orkes ===")
    print("You need to create a workflow with:")
    print("Name: video_generation_workflow")
    print("Tasks:")
    print("1. generate_script")
    print("2. generate_images (depends on generate_script)")
    print("3. generate_audio (depends on generate_script)")  
    print("4. assemble_video (depends on generate_images, generate_audio)")
    print("\nExample workflow JSON:")
    
    workflow_def = {
        "name": "video_generation_workflow",
        "description": "Generate video content with AI",
        "version": 1,
        "tasks": [
            {
                "name": "generate_script",
                "taskReferenceName": "generate_script",
                "type": "SIMPLE"
            },
            {
                "name": "generate_images",
                "taskReferenceName": "generate_images", 
                "type": "SIMPLE",
                "inputParameters": {
                    "script": "${generate_script.output.script}"
                }
            },
            {
                "name": "generate_audio",
                "taskReferenceName": "generate_audio",
                "type": "SIMPLE", 
                "inputParameters": {
                    "script": "${generate_script.output.script}"
                }
            },
            {
                "name": "assemble_video",
                "taskReferenceName": "assemble_video",
                "type": "SIMPLE",
                "inputParameters": {
                    "script": "${generate_script.output.script}",
                    "images": "${generate_images.output.images}",
                    "audio": "${generate_audio.output.audio}"
                }
            }
        ],
        "inputParameters": ["topic", "duration", "voice", "run_id"],
        "schemaVersion": 2
    }
    
    import json
    print(json.dumps(workflow_def, indent=2))

if __name__ == "__main__":
    print("Testing Orkes Workflow...")
    
    success = asyncio.run(test_workflow_operations())
    
    if not success:
        print_workflow_definition()
    
    print("\nTest completed!")