import asyncio
import httpx
import logging
import os
import base64
from workers.base_worker import BaseWorker
from utils.file_handler import FileHandler
from config import Config

logger = logging.getLogger(__name__)

class ImageWorker(BaseWorker):
    def __init__(self):
        super().__init__("generate_images", poll_interval=1.0)
        
    def process_task(self, input_data: dict, task_id: str) -> dict:
        """Generate images for script scenes using Akash-deployed Stability AI model"""
        script = input_data.get('script')
        
        if not script or not script.get('scenes'):
            raise Exception('Script with scenes is required for image generation')
            
        logger.info(f"Generating images for {len(script['scenes'])} scenes using Akash SD-Turbo model")
        logger.info(f"Script title: '{script['title']}'")
        logger.info(f"Using Akash model endpoint: {Config.AKASH_IMAGE_MODEL_URL}")
        
        # Use asyncio to run async image generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            images = loop.run_until_complete(self._generate_images_for_script(script))
        finally:
            loop.close()
        
        successful_images = [img for img in images if img.get('filepath') and not img.get('error')]
        failed_images = [img for img in images if img.get('error')]
        
        logger.info(f"Image generation completed:")
        logger.info(f"  Successful: {len(successful_images)}/{len(script['scenes'])}")
        if failed_images:
            logger.info(f"  Failed: {len(failed_images)}")
        
        return {
            'images': images,
            'script': script,
            'statistics': {
                'totalScenes': len(script['scenes']),
                'successfulImages': len(successful_images),
                'failedImages': len(failed_images),
                'successRate': round((len(successful_images) / len(script['scenes'])) * 100)
            },
            'message': f"Generated {len(successful_images)}/{len(script['scenes'])} images using Akash SD-Turbo model"
        }
        
    async def _generate_images_for_script(self, script: dict) -> list:
        """Generate images for all scenes in the script using Akash SD-Turbo model"""
        images = []
        FileHandler.ensure_directories()
        
        # Test connection to Akash model first
        await self._test_akash_connection()
        
        for i, scene in enumerate(script['scenes']):
            filename = f"scene_{i + 1}.png"  # SD-Turbo outputs PNG by default
            
            try:
                logger.info(f"Generating scene {i + 1}/{len(script['scenes'])}: {scene['visualDescription'][:60]}...")
                
                image_result = await self._generate_image_akash(
                    scene['visualDescription'], 
                    filename
                )
                
                images.append({
                    'sceneIndex': i,
                    'filename': filename,
                    'filepath': image_result['filepath'],
                    'duration': scene['duration'],
                    'prompt': scene['visualDescription'],
                    'model': 'stabilityai/sd-turbo'
                })
                
                # Small delay between requests to avoid overwhelming the model
                await asyncio.sleep(2)
                
            except Exception as image_error:
                logger.error(f"Failed to generate image for scene {i + 1}: {image_error}")
                
                images.append({
                    'sceneIndex': i,
                    'filename': f"placeholder_{i + 1}.png",
                    'filepath': None,
                    'duration': scene['duration'],
                    'prompt': scene['visualDescription'],
                    'error': str(image_error)
                })
        
        logger.info(f"Generated {len([img for img in images if img.get('filepath')])}/{len(script['scenes'])} images")
        return images
        
    async def _generate_image_akash(self, prompt: str, filename: str, width: int = 1024, height: int = 576) -> dict:
        """Generate a single image using Akash-deployed SD-Turbo model"""
        try:
            # Clean the prompt for SD-Turbo (it works better with clean, descriptive prompts)
            clean_prompt = prompt.strip()
            
            # Prepare the request payload for your Akash SD-Turbo model
            payload = {
                "prompt": clean_prompt,
                "width": width,
                "height": height
            }
            
            logger.info(f"Requesting image from Akash SD-Turbo: {clean_prompt[:60]}...")
            
            # Retry logic for network/API issues
            max_retries = 3
            response = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Akash model attempt {attempt}/{max_retries}")
                    
                    async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for model inference
                        response = await client.post(
                            f"{Config.AKASH_IMAGE_MODEL_URL}/generate-image",
                            json=payload,
                            headers={
                                'Content-Type': 'application/json',
                                'User-Agent': 'VideoGenerator-Akash/1.0'
                            }
                        )
                        
                    if response.status_code == 200:
                        logger.info(f"Akash model success on attempt {attempt}")
                        break
                    else:
                        error_text = response.text if response else "No response"
                        raise Exception(f"HTTP {response.status_code}: {error_text}")
                        
                except Exception as retry_error:
                    logger.warning(f"Akash model attempt {attempt} failed: {retry_error}")
                    
                    if attempt == max_retries:
                        raise retry_error
                    
                    # Wait before retry (exponential backoff)
                    delay = attempt * 3
                    logger.info(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
            
            # Parse the response from your Akash model
            result = response.json()
            
            if not result.get('success', False):
                raise Exception(f"Akash model generation failed: {result.get('error', 'Unknown error')}")
            
            # Decode the base64 image data
            image_data = base64.b64decode(result['image'])
            
            # Save image to temp directory
            filepath = FileHandler.get_temp_path(filename)
            await FileHandler.save_binary(image_data, filepath)
            
            logger.info(f"Image saved from Akash SD-Turbo: {filename}")
            return {
                'filepath': filepath,
                'prompt': clean_prompt,
                'filename': filename,
                'model': 'stabilityai/sd-turbo',
                'source': 'akash-network'
            }
            
        except Exception as e:
            logger.error(f"Akash SD-Turbo model error for '{prompt}': {e}")
            
            if 'timeout' in str(e).lower():
                raise Exception('Akash model timeout. The model may be busy, please try again.')
            
            raise Exception(f"Akash SD-Turbo model error: {e}")

    async def _test_akash_connection(self):
        """Test connection to Akash-deployed SD-Turbo model"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{Config.AKASH_IMAGE_MODEL_URL}/health")
                
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Akash model health check passed: {health_data}")
                return True
            else:
                raise Exception(f"Health check failed with status {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Akash model health check failed: {e}")
            raise Exception(f"Cannot connect to Akash SD-Turbo model at {Config.AKASH_IMAGE_MODEL_URL}: {e}")
            
    async def test_akash_connection(self):
        """Test Akash SD-Turbo connection with image generation"""
        try:
            result = await self._generate_image_akash(
                'A futuristic cityscape with vibrant colors and clean architecture', 
                'test_akash_image.png', 
                512, 
                512
            )
            logger.info('Akash SD-Turbo connection test successful')
            return result
        except Exception as e:
            logger.error(f'Akash SD-Turbo connection test failed: {e}')
            raise