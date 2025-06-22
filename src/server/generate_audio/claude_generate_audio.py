import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from flask import Flask, request, jsonify, current_app
from functools import wraps
import tempfile
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings, play
import uuid
from dotenv import load_dotenv

load_dotenv()



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PodcastMiddleware:
    """
    Flask middleware for converting text podcast scripts to audio using ElevenLabs TTS API.
    Handles dynamic voice generation, multi-speaker conversion, and audio file management.
    """
    
    def __init__(self, app: Flask, api_key: str, audio_folder: str = "audio"):
        self.app = app
        self.api_key = os.getenv("ELEVENLABS_API_KEY")  # Placeholder for API key
        self.audio_folder = audio_folder
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        
        # Voice mapping for different speaker types with descriptions
        self.voice_profiles = {
            "host": {
                "description": "A professional, warm, and engaging voice suitable for podcast hosting",
                "gender": "male",
                "age": "middle_aged",
                "accent": "american"
            },
            "expert_male": {
                "description": "An authoritative, intelligent male voice for academic experts",
                "gender": "male", 
                "age": "middle_aged",
                "accent": "american"
            },
            "expert_female": {
                "description": "A confident, knowledgeable female voice for researchers",
                "gender": "female",
                "age": "young_adult", 
                "accent": "american"
            },
            "narrator": {
                "description": "A clear, neutral voice for narration and transitions",
                "gender": "male",
                "age": "middle_aged",
                "accent": "british"
            }
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the middleware with Flask app."""
        self.app = app
        self._setup_audio_folder()
        self._initialize_elevenlabs_client()
        
        # Register the middleware route
        app.add_url_rule('/generate-podcast', 'generate_podcast', 
                        self.generate_podcast_endpoint, methods=['POST'])
    
    def _setup_audio_folder(self):
        """Create audio folder if it doesn't exist."""
        try:
            if not os.path.exists(self.audio_folder):
                os.makedirs(self.audio_folder)
                logger.info(f"Created audio folder: {self.audio_folder}")
        except Exception as e:
            logger.error(f"Failed to create audio folder: {e}")
            raise
    
    def _initialize_elevenlabs_client(self):
        """Initialize ElevenLabs client with API key."""
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info("ElevenLabs client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs client: {e}")
            raise
    
    def parse_podcast_script(self, text: str) -> List[Dict]:
        """
        Parse podcast script to extract speakers and their dialogue.
        
        Args:
            text (str): The podcast script text
            
        Returns:
            List[Dict]: List of segments with speaker and text
        """
        segments = []
        
        # Regex pattern to match speaker names and their dialogue
        # Matches patterns like "**Speaker Name:**" or "*Speaker Name:**"  
        pattern = r'\*{1,2}([^*]+?):\*{0,2}\s*(.*?)(?=\*{1,2}[^*]+?:\*{0,2}|$)'
        
        matches = re.findall(pattern, text, re.DOTALL)
        
        for speaker_raw, dialogue in matches:
            # Clean up speaker name
            speaker = speaker_raw.strip()
            
            # Clean up dialogue text
            dialogue = re.sub(r'\*+', '', dialogue).strip()
            dialogue = re.sub(r'\n+', ' ', dialogue)
            dialogue = re.sub(r'\s+', ' ', dialogue)
            
            if dialogue:  # Only add if there's actual dialogue
                segments.append({
                    'speaker': speaker,
                    'text': dialogue
                })
        
        logger.info(f"Parsed {len(segments)} dialogue segments")
        return segments
    
    def classify_speaker_type(self, speaker_name: str) -> str:
        """
        Classify speaker type based on name/title for voice selection.
        
        Args:
            speaker_name (str): The speaker's name/title
            
        Returns:
            str: Speaker type classification
        """
        speaker_lower = speaker_name.lower()
        
        if 'host' in speaker_lower:
            return 'host'
        elif any(title in speaker_lower for title in ['dr.', 'prof.', 'professor']):
            # Determine gender based on common names or use alternating pattern
            if any(name in speaker_lower for name in ['elena', 'maria', 'sarah', 'jennifer', 'lisa']):
                return 'expert_female'
            else:
                return 'expert_male'
        elif 'narrator' in speaker_lower:
            return 'narrator'
        else:
            # Default classification based on common names
            if any(name in speaker_lower for name in ['elena', 'maria', 'sarah', 'jennifer', 'lisa']):
                return 'expert_female'
            else:
                return 'expert_male'
    
    def generate_voice_for_speaker(self, speaker_name: str, speaker_type: str) -> Optional[Voice]:
        """
        Generate or select a voice for a specific speaker using ElevenLabs voice generation.
        
        Args:
            speaker_name (str): Name of the speaker
            speaker_type (str): Type/classification of the speaker
            
        Returns:
            Optional[Voice]: Generated or selected voice object
        """
        try:
            profile = self.voice_profiles.get(speaker_type, self.voice_profiles['expert_male'])
            
            # For this example, we'll use predefined voice IDs as placeholders
            # In production, you would use ElevenLabs voice generation or voice cloning
            voice_id_mapping = {
                'host': 'VOICE_ID_HOST',
                'expert_male': 'VOICE_ID_EXPERT_MALE', 
                'expert_female': 'VOICE_ID_EXPERT_FEMALE',
                'narrator': 'VOICE_ID_NARRATOR'
            }
            
            voice_id = voice_id_mapping.get(speaker_type, 'VOICE_ID_DEFAULT')
            
            # Create voice object with custom settings
            voice = Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=0.75,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            logger.info(f"Generated voice for {speaker_name} ({speaker_type})")
            return voice
            
        except Exception as e:
            logger.error(f"Failed to generate voice for {speaker_name}: {e}")
            return None
    
    def convert_text_to_speech(self, text: str, voice: Voice) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text (str): Text to convert
            voice (Voice): Voice object to use
            
        Returns:
            Optional[bytes]: Audio data in bytes
        """
        try:
            if self.client is None:
                logger.error("ElevenLabs client is not initialized")
                return None
                
            audio_bytes = self.client.text_to_speech.convert(
                text=text,
                voice=voice,
                model="eleven_turbo_v2_5"
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Text-to-speech conversion failed: {e}")
            return None
    
    def combine_audio_segments(self, audio_segments: List[Tuple[str, bytes]], 
                             output_filename: str) -> str:
        """
        Combine multiple audio segments into a single MP3 file.
        
        Args:
            audio_segments (List[Tuple[str, bytes]]): List of (speaker, audio_bytes) tuples
            output_filename (str): Name for the output file
            
        Returns:
            str: Path to the combined audio file
        """
        try:
            combined_audio = AudioSegment.empty()
            
            for speaker, audio_bytes in audio_segments:
                # Create temporary file for audio bytes
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_file.flush()
                    
                    # Load audio segment
                    segment = AudioSegment.from_mp3(temp_file.name)
                    
                    # Add a small pause between speakers (0.5 seconds)
                    if len(combined_audio) > 0:
                        pause = AudioSegment.silent(duration=500)
                        combined_audio += pause
                    
                    combined_audio += segment
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
            
            # Save combined audio
            output_path = os.path.join(self.audio_folder, output_filename)
            combined_audio.export(output_path, format="mp3", bitrate="192k")
            
            logger.info(f"Combined audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to combine audio segments: {e}")
            raise
    
    def generate_podcast_audio(self, script_text: str, 
                             podcast_title: str) -> Dict:
        """
        Main method to convert podcast script to audio.
        
        Args:
            script_text (str): The podcast script
            podcast_title (str): Optional title for the podcast
            
        Returns:
            Dict: Result containing file path and metadata
        """
        try:
            # Parse the script
            segments = self.parse_podcast_script(script_text)
            
            if not segments:
                raise ValueError("No dialogue segments found in script")
            
            # Generate voices for unique speakers
            speaker_voices = {}
            audio_segments = []
            
            for segment in segments:
                speaker = segment['speaker']
                text = segment['text']
                
                # Generate voice for new speakers
                if speaker not in speaker_voices:
                    speaker_type = self.classify_speaker_type(speaker)
                    voice = self.generate_voice_for_speaker(speaker, speaker_type)
                    
                    if voice is None:
                        logger.warning(f"Failed to generate voice for {speaker}, skipping segment")
                        continue
                        
                    speaker_voices[speaker] = voice
                
                # Convert text to speech
                audio_bytes = self.convert_text_to_speech(text, speaker_voices[speaker])
                
                if audio_bytes:
                    audio_segments.append((speaker, audio_bytes))
                    logger.info(f"Generated audio for {speaker}: {len(text)} characters")
                else:
                    logger.warning(f"Failed to generate audio for {speaker}")
            
            if not audio_segments:
                raise ValueError("No audio segments were generated successfully")
            
            # Generate output filename
            if podcast_title:
                safe_title = re.sub(r'[^\w\-_\. ]', '', podcast_title)
                filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            else:
                filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            
            # Combine audio segments
            output_path = self.combine_audio_segments(audio_segments, filename)
            
            return {
                'success': True,
                'file_path': output_path,
                'filename': filename,
                'segments_processed': len(audio_segments),
                'speakers': list(speaker_voices.keys()),
                'duration_estimate': f"{len(audio_segments) * 10} seconds"  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Podcast generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_podcast_endpoint(self):
        """Flask endpoint for podcast generation."""
        try:
            data = request.get_json()
            
            if not data or 'script' not in data:
                return jsonify({'error': 'Script text is required'}), 400
            
            script_text = data['script']
            podcast_title = data.get('title', None)
            
            # Generate podcast audio
            result = self.generate_podcast_audio(script_text, podcast_title)
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"Endpoint error: {e}")
            return jsonify({'error': 'Internal server error'}), 500


def create_podcast_middleware(app: Flask, api_key: str, audio_folder: str = "audio"):
    """
    Factory function to create podcast middleware.
    
    Args:
        app (Flask): Flask application instance
        api_key (str): ElevenLabs API key
        audio_folder (str): Folder to save audio files
        
    Returns:
        PodcastMiddleware: Configured middleware instance
    """
    return PodcastMiddleware(app=app, api_key=api_key, audio_folder=audio_folder)
