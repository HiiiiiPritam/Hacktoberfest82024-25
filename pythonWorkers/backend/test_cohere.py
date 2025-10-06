#!/usr/bin/env python3
"""
Test Cohere API connectivity
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
import cohere

def test_cohere_connection():
    """Test Cohere API connectivity"""
    print("=== Testing Cohere API Connectivity ===")
    print(f"API Key configured: {bool(Config.COHERE_API_KEY)}")
    print(f"Key length: {len(Config.COHERE_API_KEY) if Config.COHERE_API_KEY else 0}")
    print()
    
    if not Config.COHERE_API_KEY:
        print("[ERROR] Cohere API key not configured!")
        return False
    
    try:
        print("Testing connection...")
        client = cohere.Client(api_key=Config.COHERE_API_KEY)
        
        # Simple test request
        response = client.generate(
            model='command-r-plus',
            prompt='Say hello in one word.',
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.generations[0].text.strip()
        print(f"[OK] Connection successful! Response: '{result}'")
        return True
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("This could be due to:")
        print("1. Invalid API key")
        print("2. Network connectivity issues")
        print("3. Firewall/proxy blocking the connection")
        print("4. Cohere service temporarily unavailable")
        return False

def test_script_generation():
    """Test script generation with Cohere"""
    print("\n=== Testing Script Generation ===")
    
    try:
        from workers.script_worker import ScriptWorker
        
        worker = ScriptWorker()
        
        # Test with simple input
        input_data = {
            'topic': 'AI as a blessing',
            'duration': 3
        }
        
        print(f"Testing script generation for: '{input_data['topic']}' ({input_data['duration']}s)")
        
        result = worker.process_task(input_data, 'test_task_123')
        
        print(f"[OK] Script generation successful!")
        print(f"Title: {result['script']['title']}")
        print(f"Scenes: {result['scenesCount']}")
        print(f"Message: {result['message']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Script generation failed: {e}")
        return False

if __name__ == "__main__":
    success1 = test_cohere_connection()
    
    if success1:
        success2 = test_script_generation()
    else:
        print("\nSkipping script generation test due to connection issues.")
        success2 = False
    
    if success1 and success2:
        print("\n[SUCCESS] All Cohere tests passed!")
    elif success1:
        print("\n[WARNING] Cohere connection works but script generation has issues.")
    else:
        print("\n[ERROR] Cohere connectivity issues detected.")