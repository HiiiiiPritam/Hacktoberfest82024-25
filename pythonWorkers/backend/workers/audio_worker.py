import asyncio
import httpx
import json
import logging
from urllib.parse import quote
from workers.base_worker import BaseWorker
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)

class AudioWorker(BaseWorker):
    def __init__(self):
        super().__init__("generate_audio", poll_interval=1.0)
        
    def process_task(self, input_data: dict, task_id: str) -> dict:
        """Generate audio for script scenes using TTS services"""
        script = input_data.get('script')
        
        if not script or not script.get('scenes'):
            raise Exception('Script with scenes is required for audio generation')
            
        logger.info(f"Generating audio for {len(script['scenes'])} scenes")
        logger.info(f"Script title: '{script['title']}'")
        
        # Use asyncio to run async audio generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_files = loop.run_until_complete(self._generate_audio_for_script(script))
        finally:
            loop.close()
        
        successful_audio = [audio for audio in audio_files if audio.get('filepath') and not audio.get('error')]
        failed_audio = [audio for audio in audio_files if audio.get('error')]
        placeholder_audio = [audio for audio in audio_files if audio.get('isPlaceholder')]
        
        logger.info(f"Audio generation completed:")
        logger.info(f"  Successful: {len(successful_audio)}/{len(script['scenes'])}")
        if placeholder_audio:
            logger.info(f"  Placeholders: {len(placeholder_audio)}")
        if failed_audio:
            logger.info(f"  Failed: {len(failed_audio)}")
        
        return {
            'audioFiles': audio_files,
            'script': script,
            'statistics': {
                'totalScenes': len(script['scenes']),
                'successfulAudio': len(successful_audio),
                'placeholderAudio': len(placeholder_audio),
                'failedAudio': len(failed_audio),
                'successRate': round((len(successful_audio) / len(script['scenes'])) * 100)
            },
            'message': f"Generated audio for {len(successful_audio)}/{len(script['scenes'])} scenes ({len(placeholder_audio)} placeholders)"
        }
        
    async def _generate_audio_for_script(self, script: dict) -> list:
        """Generate audio for all scenes in the script"""
        audio_files = []
        FileHandler.ensure_directories()
        
        for i, scene in enumerate(script['scenes']):
            filename = f"audio_scene_{i + 1}.mp3"
            
            try:
                audio_result = await self._generate_speech(scene['text'], filename)
                
                audio_files.append({
                    'sceneIndex': i,
                    'filename': audio_result['filename'],
                    'filepath': audio_result['filepath'],
                    'text': scene['text'],
                    'duration': audio_result['duration'],
                    'isPlaceholder': audio_result.get('isPlaceholder', False),
                    'isRealAudio': audio_result.get('isRealAudio', False)
                })
                
                # Small delay between requests
                await asyncio.sleep(0.5)
                
            except Exception as audio_error:
                logger.error(f"Failed to generate audio for scene {i + 1}: {audio_error}")
                
                audio_files.append({
                    'sceneIndex': i,
                    'filename': f"placeholder_audio_{i + 1}.mp3",
                    'filepath': None,
                    'text': scene['text'],
                    'duration': self._estimate_audio_duration(scene['text']),
                    'error': str(audio_error)
                })
        
        logger.info(f"Generated audio for {len([audio for audio in audio_files if audio.get('filepath')])}/{len(script['scenes'])} scenes")
        return audio_files
        
    async def _generate_speech(self, text: str, filename: str, voice: str = 'nova') -> dict:
        """Generate speech from text using Google Translate TTS"""
        try:
            logger.info(f"Generating speech for: {text[:50]}...")
            
            # Clean the text for audio generation
            clean_text = ''.join(c for c in text if c.isalnum() or c in ' -,.!?').strip()
            
            # Limit text length to avoid API issues
            audio_text = clean_text
            if len(audio_text) > 200:
                audio_text = audio_text[:200].strip()
            
            # Use Google Translate TTS (free and reliable)
            encoded_text = quote(audio_text)
            audio_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl=en&client=tw-ob"
            
            logger.info(f"Audio URL: {audio_url[:100]}...")
            
            # Retry logic for network/API issues
            max_retries = 3
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Audio attempt {attempt}/{max_retries}")
                    
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(audio_url, headers={
                            'User-Agent': 'VideoGenerator/1.0'
                        })
                    
                    if response.status_code == 200:
                        logger.info(f"Audio success on attempt {attempt}")
                        logger.info(f"Response: {response.status_code} | Size: {len(response.content)} bytes")
                        break
                    else:
                        raise Exception(f"HTTP {response.status_code}")
                        
                except Exception as retry_error:
                    logger.info(f"Audio attempt {attempt} failed: {retry_error}")
                    
                    if attempt == max_retries:
                        logger.info("All audio attempts failed, using fallback...")
                        return await self._generate_speech_fallback(text, filename)
                    
                    # Wait before retry
                    delay = attempt
                    logger.info(f"Waiting {delay}s before audio retry...")
                    await asyncio.sleep(delay)
            
            # Save audio file
            filepath = FileHandler.get_temp_path(filename)
            await FileHandler.save_binary(response.content, filepath)
            
            logger.info(f"Real audio generated: {filename}")
            return {
                'filepath': filepath,
                'filename': filename,
                'text': clean_text,
                'duration': self._estimate_audio_duration(clean_text),
                'isRealAudio': True
            }
            
        except Exception as e:
            logger.error(f"TTS error for '{text}': {e}")
            raise Exception(f"TTS API error: {e}")
            
    async def _generate_speech_fallback(self, text: str, filename: str) -> dict:
        """Fallback method - creates a text file when TTS fails"""
        try:
            logger.info("Using fallback audio method (TTS API failed)...")
            
            # Create a text file as placeholder
            audio_filename = filename.replace('.mp3', '_placeholder.txt')
            filepath = FileHandler.get_temp_path(audio_filename)
            
            tts_data = {
                'text': text,
                'duration': self._estimate_audio_duration(text),
                'timestamp': asyncio.get_event_loop().time(),
                'note': 'TTS API failed. This is a text placeholder.',
                'originalFilename': filename
            }
            
            await FileHandler.save_text(json.dumps(tts_data, indent=2), filepath)
            
            logger.info(f"Created audio placeholder: {audio_filename}")
            return {
                'filepath': filepath,
                'filename': audio_filename,
                'text': text,
                'duration': self._estimate_audio_duration(text),
                'isPlaceholder': True
            }
            
        except Exception as e:
            raise Exception(f"Audio fallback failed: {e}")
            
    def _estimate_audio_duration(self, text: str) -> float:
        """Estimate audio duration based on text length"""
        # Rough estimate: ~150 words per minute, ~5 characters per word
        characters_per_second = 12.5  # 150 WPM / 60 seconds * 5 chars
        duration = max(2, len(text) / characters_per_second)
        return round(duration * 10) / 10  # Round to 1 decimal
        
    async def test_tts_connection(self):
        """Test TTS connection"""
        try:
            result = await self._generate_speech('Hello, this is a test of the TTS system.', 'test_audio.mp3')
            logger.info('TTS connection test successful')
            return result
        except Exception as e:
            logger.error(f'TTS connection test failed: {e}')
            raise