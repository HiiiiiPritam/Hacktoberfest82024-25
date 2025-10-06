import os
import json
import aiofiles
import logging
from pathlib import Path
from typing import Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    @staticmethod
    def ensure_directories():
        """Create temp and output directories if they don't exist"""
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
    @staticmethod
    def get_temp_path(filename: str) -> str:
        """Get full path for temp file"""
        FileHandler.ensure_directories()
        return os.path.join(Config.TEMP_DIR, filename)
        
    @staticmethod
    def get_output_path(filename: str) -> str:
        """Get full path for output file"""
        FileHandler.ensure_directories()
        return os.path.join(Config.OUTPUT_DIR, filename)
        
    @staticmethod
    async def save_json(data: Any, filepath: str) -> str:
        """Save data as JSON file"""
        try:
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            logger.info(f"Saved JSON to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            raise
            
    @staticmethod
    async def load_json(filepath: str) -> Any:
        """Load JSON data from file"""
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            raise
            
    @staticmethod
    async def save_binary(data: bytes, filepath: str) -> str:
        """Save binary data to file"""
        try:
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(data)
            logger.info(f"Saved binary file to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save binary file: {e}")
            raise
            
    @staticmethod
    async def save_text(text: str, filepath: str) -> str:
        """Save text to file"""
        try:
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(text)
            logger.info(f"Saved text file to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save text file: {e}")
            raise
            
    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if file exists"""
        return os.path.exists(filepath)
        
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(filepath) if FileHandler.file_exists(filepath) else 0
        
    @staticmethod
    def cleanup_temp_files(pattern: Optional[str] = None):
        """Clean up temporary files"""
        try:
            temp_path = Path(Config.TEMP_DIR)
            if pattern:
                files = temp_path.glob(pattern)
            else:
                files = temp_path.glob('*')
                
            for file in files:
                if file.is_file():
                    file.unlink()
                    logger.info(f"Deleted temp file: {file}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")