import json
import logging
from datetime import datetime
from workers.base_worker import BaseWorker
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)

class VideoWorker(BaseWorker):
    def __init__(self):
        super().__init__("assemble_video", poll_interval=1.0)
        
    def process_task(self, input_data: dict, task_id: str) -> dict:
        """Assemble video from images, audio and script"""
        images = input_data.get('images')
        audio_files = input_data.get('audioFiles')
        script = input_data.get('script')
        
        if not images or not audio_files or not script:
            raise Exception('Images, audioFiles, and script are required for video assembly')
            
        logger.info(f"Assembling video: '{script['title']}'")
        logger.info(f"Scenes: {len(script['scenes'])}")
        logger.info(f"Images: {len(images)}")
        logger.info(f"Audio files: {len(audio_files)}")
        
        try:
            video_result = self._assemble_video(images, audio_files, script)
            logger.info("Video assembly completed successfully!")
            
            return {
                'videoPath': video_result['projectPath'],
                'previewPath': video_result['previewPath'], 
                'videoData': video_result['videoData'],
                'message': f"Video project created successfully: '{script['title']}'",
                'instructions': {
                    'projectFile': 'Check video_project.json for complete data',
                    'previewFile': 'Open video_preview.html in browser to see scenes',
                    'nextSteps': 'Integrate with actual video rendering library (FFmpeg/Editly)'
                }
            }
            
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            raise Exception(f"Video assembly failed: {e}")
            
    def _assemble_video(self, images: list, audio_files: list, script: dict) -> dict:
        """Assemble video components into project files"""
        try:
            logger.info("Starting video assembly...")
            
            # Ensure output directory exists
            FileHandler.ensure_directories()
            
            # For now, create a video project simulation
            # In production, you'd use FFmpeg or similar library here
            
            video_data = {
                'title': script['title'],
                'totalDuration': script['totalDuration'],
                'scenes': [
                    {
                        'sceneIndex': index,
                        'startTime': scene['startTime'],
                        'duration': scene['duration'],
                        'text': scene['text'],
                        'visualDescription': scene['visualDescription'],
                        'imagePath': images[index]['filepath'] if index < len(images) and images[index].get('filepath') else None,
                        'audioPath': audio_files[index]['filepath'] if index < len(audio_files) and audio_files[index].get('filepath') else None,
                        'hasImage': index < len(images) and bool(images[index].get('filepath')),
                        'hasAudio': index < len(audio_files) and bool(audio_files[index].get('filepath'))
                    }
                    for index, scene in enumerate(script['scenes'])
                ],
                'statistics': {
                    'totalScenes': len(script['scenes']),
                    'scenesWithImages': len([img for img in images if img.get('filepath')]),
                    'scenesWithAudio': len([audio for audio in audio_files if audio.get('filepath')]),
                    'placeholderAudio': len([audio for audio in audio_files if audio.get('isPlaceholder')])
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Save video project file
            project_file_path = FileHandler.get_output_path('video_project.json')
            with open(project_file_path, 'w') as f:
                json.dump(video_data, f, indent=2)
                
            # Create HTML preview
            html_preview = self._generate_video_preview(video_data)
            preview_path = FileHandler.get_output_path('video_preview.html')
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write(html_preview)
            
            logger.info("Video assembly completed")
            logger.info(f"Project file: {project_file_path}")
            logger.info(f"Preview file: {preview_path}")
            
            return {
                'projectPath': project_file_path,
                'previewPath': preview_path,
                'videoData': video_data
            }
            
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            raise
            
    def _generate_video_preview(self, video_data: dict) -> str:
        """Generate HTML preview of video scenes"""
        scenes = []
        
        for index, scene in enumerate(video_data['scenes']):
            image_display = (
                f'<img src="../temp/scene_{index + 1}.jpg" alt="Scene {index + 1}" style="max-width: 300px; height: auto;">'
                if scene['hasImage']
                else '<div style="width: 300px; height: 200px; background: #f0f0f0; display: flex; align-items: center; justify-content: center;">No Image Generated</div>'
            )
            
            audio_display = (
                f'<audio controls><source src="../temp/audio_scene_{index + 1}.mp3" type="audio/mpeg">Audio not supported</audio>'
                if scene['hasAudio']
                else '<p style="color: #888;">No Audio Generated</p>'
            )
            
            scene_html = f"""
            <div style="border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px;">
                <h3>Scene {index + 1} ({scene['startTime']}s - {scene['startTime'] + scene['duration']}s)</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start;">
                    <div>
                        <h4>Visual:</h4>
                        {image_display}
                        <p><strong>Description:</strong> {scene['visualDescription']}</p>
                    </div>
                    <div>
                        <h4>Audio:</h4>
                        {audio_display}
                        <p><strong>Text:</strong> "{scene['text']}"</p>
                        <p><strong>Duration:</strong> {scene['duration']}s</p>
                    </div>
                </div>
            </div>
            """
            scenes.append(scene_html)
        
        scenes_html = ''.join(scenes)
        timestamp = datetime.fromisoformat(video_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Video Preview: {video_data['title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .stats {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .stats div {{ display: inline-block; margin: 0 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{video_data['title']}</h1>
        <p><strong>Total Duration:</strong> {video_data['totalDuration']} seconds</p>
        <p><strong>Generated:</strong> {timestamp}</p>
    </div>
    
    <div class="stats">
        <h3>Statistics:</h3>
        <div><strong>Total Scenes:</strong> {video_data['statistics']['totalScenes']}</div>
        <div><strong>Images Generated:</strong> {video_data['statistics']['scenesWithImages']}</div>
        <div><strong>Audio Generated:</strong> {video_data['statistics']['scenesWithAudio']}</div>
        <div><strong>Audio Placeholders:</strong> {video_data['statistics']['placeholderAudio']}</div>
    </div>
    
    <div class="scenes">
        <h2>Scenes Preview:</h2>
        {scenes_html}
    </div>
    
    <div style="margin-top: 40px; padding: 20px; background: #e9ecef; border-radius: 8px;">
        <h3>🎥 Next Steps for Video Production:</h3>
        <ol>
            <li>Install a proper TTS service for audio generation</li>
            <li>Integrate FFmpeg with video rendering library</li>
            <li>Add transitions and effects between scenes</li>
            <li>Implement proper audio synchronization</li>
            <li>Add background music and sound effects</li>
        </ol>
    </div>
</body>
</html>"""