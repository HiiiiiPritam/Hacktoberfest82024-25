#!/usr/bin/env python3
"""
Server runner with proper error handling and logging
"""
import uvicorn
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server.log')
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'ORKES_KEY_ID',
        'ORKES_KEY_SECRET', 
        'ORKES_SERVER_URL',
        'COHERE_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env file")
        return False
    
    return True

def main():
    """Main server entry point"""
    logger.info("Starting FastAPI Video Generation Server...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check if dependencies are installed
    try:
        import fastapi
        import conductor
        import cohere
        logger.info("All dependencies verified")
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Start server
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()