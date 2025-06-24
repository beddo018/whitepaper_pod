import os
from dotenv import load_dotenv
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from flask import current_app, jsonify
from elevenlabs import ElevenLabs, VoiceSettings, text_to_speech, play
from pydub import AudioSegment
import tempfile
import json
from transcript import sample_transcript_list

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

class TTSMiddleware:
    """
    Text-to-Speech middleware using ElevenLabs API
    Converts text segments with different speakers to combined audio file
    """
    
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.db_path = 'podcast_audio.db'
        
        # Placeholder voice IDs for 5 distinct speakers
        self.voice_mapping = {
        'speaker_1': 'iP95p4xoKVk53GoZ742B',  
        'speaker_2': 'EXAVITQu4vr4xnSDxMaL',
        'speaker_3': '9BWtsMINqrJLrRacOk9x',
        'speaker_4': 'XrExE9yKIg1WjnnlVkGX',
        'speaker_5': 'onwK4e9ZLuTAKqWW03F9',  
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        self.app = app
        
        # Initialize ElevenLabs client
        api_key = os.getenv('ELEVENLABS_API_KEY')
        self.client = ElevenLabs(api_key=api_key)
        
        # Update voice mapping from config if provided
        voice_config = app.config.get('VOICE_MAPPING', {})
        self.voice_mapping.update(voice_config)
        
        # Initialize database
        self._init_database()
        
        # Create audio directory
        self._create_audio_directory()
    
    def _init_database(self):
        """Initialize SQLite database for storing audio files"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    transcript TEXT,
                    audio BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def _create_audio_directory(self):
        """Create audio directory if it doesn't exist"""
        try:
            audio_dir = 'audio'
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
                logger.info(f"Created audio directory: {audio_dir}")
        except Exception as e:
            logger.error(f"Failed to create audio directory: {str(e)}")
            raise
    
    def _parse_transcript(self, transcript: str) -> List[Dict]:
        """
        Parse transcript into speaker segments
        Expected format: JSON string with speaker segments
        Example: [{"speaker": "speaker_1", "text": "Hello world"}, ...]
        """
        try:
            if isinstance(transcript, str):
                segments = json.loads(transcript)
            else:
                segments = transcript
                
            # Validate segments structure
            for segment in segments:
                if not isinstance(segment, dict) or 'speaker' not in segment or 'text' not in segment:
                    raise ValueError("Invalid transcript format")
            
            return segments
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse transcript: {str(e)}")
            raise ValueError(f"Invalid transcript format: {str(e)}")
    
    def _generate_speech_segment(self, text: str, speaker: str) -> bytes:
        """
        Generate speech for a single text segment using ElevenLabs API
        """
        try:
            # Get voice ID for speaker, default to speaker_1 if not found
            voice_id = self.voice_mapping.get(speaker, self.voice_mapping['speaker_1'])
            
            # Generate speech using ElevenLabs API
            audio = elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_flash_v2_5",  # You can change this model as needed
                output_format="mp3_44100_128",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                )
            )
            
            #for testing
            play(audio)
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            logger.info(f"Generated speech for speaker {speaker}, text length: {len(text)}")
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate speech for speaker {speaker}: {str(e)}")
            raise
    
    def _combine_audio_segments(self, audio_segments: List[bytes], filename: str) -> str:
        """
        Combine multiple audio segments into a single MP3 file
        """
        try:
            combined_audio = AudioSegment.empty()
            
            for i, audio_bytes in enumerate(audio_segments):
                # Create temporary file for each segment
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_file_path = temp_file.name
                
                try:
                    # Load audio segment
                    segment = AudioSegment.from_mp3(temp_file_path)
                    
                    # Add small pause between segments (0.5 seconds)
                    if i > 0:
                        pause = AudioSegment.silent(duration=500)
                        combined_audio += pause
                    
                    combined_audio += segment
                    
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file_path)
            
            # Save combined audio
            output_path = os.path.join('audio', f"{filename}.mp3")
            combined_audio.export(output_path, format="mp3")
            
            logger.info(f"Combined audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to combine audio segments: {str(e)}")
            raise
    
    def _save_to_database(self, filename: str, transcript: str, audio_path: str):
        """
        Save audio file information to database
        """
        try:
            # Read audio file as binary
            with open(audio_path, 'rb') as audio_file:
                audio_blob = audio_file.read()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audio_files (filename, transcript, audio)
                VALUES (?, ?, ?)
            ''', (filename, transcript, audio_blob))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved audio file to database: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save to database: {str(e)}")
            raise
    
    def convert_to_audio(self, transcript: list[dict], filename: str) -> str:
        """
        Main middleware function to convert transcript to audio
        
        Args:
            transcript: JSON string or list of speaker segments
            filename: Base filename for the output audio file
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            logger.info(f"Starting audio conversion for file: {filename}")
            
            # Parse transcript into segments
            segments = transcript
            
            if not segments:
                raise ValueError("No segments found in transcript")
            
            # Generate speech for each segment
            audio_segments = []
            for segment in segments:
                speaker = segment['speaker']
                text = segment['text']
                
                if not text.strip():
                    logger.warning(f"Empty text for speaker {speaker}, skipping")
                    continue
                
                try:
                    audio_bytes = self._generate_speech_segment(text, speaker)
                    audio_segments.append(audio_bytes)
                except Exception as e:
                    logger.error(f"Failed to generate speech for segment: {str(e)}")
                    # Continue with other segments instead of failing completely
                    continue
            
            if not audio_segments:
                raise ValueError("No audio segments were generated successfully")
            
            # Combine audio segments
            audio_path = self._combine_audio_segments(audio_segments, filename)
            
            # Save to database
            transcript_str = json.dumps(segments) if isinstance(transcript, list) else transcript
            self._save_to_database(filename, transcript_str, audio_path)
            
            logger.info(f"Audio conversion completed successfully: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            raise

if __name__ == "__main__":
    tts = TTSMiddleware()
    audio_path = tts.convert_to_audio(sample_transcript_list, "my_podcast")
    print(audio_path)