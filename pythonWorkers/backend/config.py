import os
from dotenv import load_dotenv
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings

load_dotenv()

class Config:
    # Orkes Configuration
    ORKES_KEY_ID = os.getenv("ORKES_KEY_ID")
    ORKES_KEY_SECRET = os.getenv("ORKES_KEY_SECRET") 
    ORKES_SERVER_URL = os.getenv("ORKES_SERVER_URL")
    
    # AI Services Configuration
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    
    # Akash Deployed Model Configuration
    AKASH_IMAGE_MODEL_URL = os.getenv("AKASH_IMAGE_MODEL_URL", "http://localhost:8080")
    AKASH_MEDIA_ASSEMBLER_URL = os.getenv("AKASH_MEDIA_ASSEMBLER_URL", "http://localhost:9090")
    
    # Video Configuration
    VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", 1024))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", 576))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", 30))
    DEFAULT_VIDEO_DURATION = int(os.getenv("DEFAULT_VIDEO_DURATION", 30))
    
    # Directories
    TEMP_DIR = "temp"
    OUTPUT_DIR = "output"

def get_conductor_config():
    """Get Orkes Conductor configuration"""
    configuration = Configuration(
        server_api_url=Config.ORKES_SERVER_URL,
        debug=False,
    )
    # Set authentication settings properly
    configuration.authentication_settings = AuthenticationSettings(
        key_id=Config.ORKES_KEY_ID,
        key_secret=Config.ORKES_KEY_SECRET
    )
    return configuration