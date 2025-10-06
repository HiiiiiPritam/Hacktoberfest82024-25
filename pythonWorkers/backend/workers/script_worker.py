import json
import logging
import cohere
from workers.base_worker import BaseWorker
from config import Config

logger = logging.getLogger(__name__)

class ScriptWorker(BaseWorker):
    def __init__(self):
        super().__init__("generate_script", poll_interval=1.0)
        self.client = None
        
    def _get_client(self):
        """Initialize Cohere client lazily to avoid pickling issues"""
        if self.client is None:
            self.client = cohere.Client(api_key=Config.COHERE_API_KEY)
        return self.client
        
    def process_task(self, input_data: dict, task_id: str) -> dict:
        """Generate video script using Cohere AI"""
        topic = input_data.get('topic')
        duration = input_data.get('duration', 30)
        
        # Parse duration if it's a string (e.g., "30s" -> 30)
        if isinstance(duration, str):
            duration = int(duration.replace('s', ''))
        elif not isinstance(duration, int):
            duration = int(duration) if duration else 30
        
        if not topic:
            raise Exception('Topic is required for script generation')
            
        logger.info(f"Generating script for topic: '{topic}' ({duration}s)")
        
        try:
            script = self._generate_script(topic, duration)
            logger.info(f"Script generated successfully: '{script['title']}'")
            logger.info(f"Generated {len(script['scenes'])} scenes")
            
            return {
                'script': script,
                'topic': topic,
                'duration': duration,
                'scenesCount': len(script['scenes']),
                'message': f"Successfully generated script: '{script['title']}'"
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            logger.info("Using fallback script generator...")
            
            # Fallback script generation
            script = self._generate_fallback_script(topic, duration)
            return {
                'script': script,
                'topic': topic,
                'duration': duration,
                'scenesCount': len(script['scenes']),
                'message': f"Generated fallback script: '{script['title']}'"
            }
            
    def _generate_script(self, topic: str, duration: int = 30) -> dict:
        """Generate script using Cohere AI"""
        prompt = f"""Create a {duration}-second engaging video script about "{topic}".

Requirements:
- Hook viewers in first 3 seconds
- Clear, concise content for {duration} seconds total
- Call to action at the end
- Break into scenes with timestamps
- Include visual descriptions for each scene

Return ONLY valid JSON in this exact format:
{{
  "title": "Video Title",
  "totalDuration": {duration},
  "scenes": [
    {{
      "startTime": 0,
      "duration": 5,
      "text": "Hook text here",
      "visualDescription": "Detailed visual description for image generation"
    }},
    {{
      "startTime": 5,
      "duration": 20,
      "text": "Main content text",
      "visualDescription": "Visual description for main content"
    }},
    {{
      "startTime": 25,
      "duration": 5,
      "text": "Call to action",
      "visualDescription": "Visual for call to action"
    }}
  ]
}}"""

        client = self._get_client()
        response = client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=2048,
            temperature=0.7
        )
        text = response.generations[0].text
        
        # Clean up response to ensure valid JSON
        text = text.replace('```json\n', '').replace('```\n', '').replace('```', '').strip()
        
        try:
            script_data = json.loads(text)
            logger.info(f"Script generated successfully: {script_data.get('title', 'Unknown Title')}")
            return script_data
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Cohere response as JSON: {e}")
            
    def _generate_fallback_script(self, topic: str, duration: int) -> dict:
        """Generate a fallback script without API"""
        num_scenes = max(2, min(5, duration // 3))
        scene_duration = duration // num_scenes
        scenes = []
        
        for i in range(num_scenes):
            start_time = i * scene_duration
            is_first = i == 0
            is_last = i == num_scenes - 1
            
            if is_first:
                text = f"Welcome! Today we're exploring {topic}. Get ready for an amazing journey!"
                visual_description = f"Engaging opening scene with vibrant colors, showing {topic} in an exciting way"
            elif is_last:
                text = f"Thanks for watching! Don't forget to like and subscribe for more content about {topic}!"
                visual_description = f"Call to action scene with subscribe button and social media icons, {topic} themed background"
            else:
                text = f"Let's dive deeper into {topic} and discover what makes it so fascinating and important."
                visual_description = f"Educational scene showing detailed aspects of {topic} with infographics and visual elements"
            
            scenes.append({
                "startTime": start_time,
                "duration": duration - start_time if is_last else scene_duration,
                "text": text,
                "visualDescription": visual_description
            })
        
        script = {
            "title": f"{topic}: A Complete Guide",
            "totalDuration": duration,
            "scenes": scenes
        }
        
        logger.info(f"Fallback script generated successfully: {script['title']}")
        return script