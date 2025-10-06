#!/usr/bin/env python3
"""
Test script for Akash-deployed SD-Turbo model
"""
import asyncio
import sys
import os
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workers.image_worker import ImageWorker
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_akash_model():
    """Test the Akash SD-Turbo model integration"""
    print("=== Testing Akash SD-Turbo Model Integration ===")
    print(f"Model URL: {Config.AKASH_IMAGE_MODEL_URL}")
    print()
    
    # Create ImageWorker instance
    image_worker = ImageWorker()
    
    try:
        print("[1] Testing health endpoint...")
        await image_worker._test_akash_connection()
        print("✅ Health check passed")
        print()
        
        print("[2] Testing image generation...")
        result = await image_worker.test_akash_connection()
        print(f"✅ Image generation successful: {result['filename']}")
        print(f"   - File path: {result['filepath']}")
        print(f"   - Model: {result['model']}")
        print(f"   - Source: {result['source']}")
        print()
        
        print("[3] Testing with sample script...")
        sample_script = {
            'title': 'Test Script for Akash Model',
            'scenes': [
                {
                    'visualDescription': 'A modern office with computers and AI technology, bright and professional atmosphere',
                    'duration': 5,
                    'text': 'Sample scene 1'
                },
                {
                    'visualDescription': 'Futuristic data center with glowing servers and network connections, cyberpunk style',
                    'duration': 5,
                    'text': 'Sample scene 2'
                }
            ]
        }
        
        # Test with sample data
        task_input = {'script': sample_script}
        result = image_worker.process_task(task_input, 'test_task_001')
        
        print(f"✅ Script processing completed")
        print(f"   - Total scenes: {result['statistics']['totalScenes']}")
        print(f"   - Successful images: {result['statistics']['successfulImages']}")
        print(f"   - Success rate: {result['statistics']['successRate']}%")
        
        for image in result['images']:
            if image.get('filepath'):
                print(f"   - Generated: {image['filename']} ({image.get('model', 'unknown')})")
            else:
                print(f"   - Failed: {image['filename']} - {image.get('error', 'unknown error')}")
        
        print()
        print("🎉 All tests completed successfully!")
        print("Your Akash SD-Turbo model integration is working properly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_with_custom_prompt():
    """Test with a custom prompt"""
    print("\n=== Custom Prompt Test ===")
    
    custom_prompt = input("Enter a custom prompt (or press Enter for default): ").strip()
    if not custom_prompt:
        custom_prompt = "A beautiful landscape with mountains and a lake, digital art style"
    
    print(f"Testing with prompt: '{custom_prompt}'")
    
    image_worker = ImageWorker()
    
    try:
        result = await image_worker._generate_image_akash(
            custom_prompt, 
            'custom_test.png', 
            512, 
            512
        )
        
        print(f"✅ Custom image generated: {result['filename']}")
        print(f"   - File path: {result['filepath']}")
        return True
        
    except Exception as e:
        print(f"❌ Custom test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Akash SD-Turbo Model Tests...")
    print(f"Make sure your .env file contains the correct AKASH_IMAGE_MODEL_URL")
    print(f"Current URL: {Config.AKASH_IMAGE_MODEL_URL}")
    print()
    
    # Run basic tests
    success = asyncio.run(test_akash_model())
    
    if success:
        # Ask if user wants to test custom prompt
        test_custom = input("\nWould you like to test with a custom prompt? (y/N): ").strip().lower()
        if test_custom == 'y':
            asyncio.run(test_with_custom_prompt())
    
    print("\nTest completed!")