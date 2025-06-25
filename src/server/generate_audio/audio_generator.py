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

#hardcoded transcript for testing
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
        # Initialize database
        self._init_database()
        # Create audio directory
        self._create_audio_directory()
        
        # voice IDs for 10 distinct speakers
        # https://elevenlabs.io/app/default-voices
        self.voice_mapping = {
        'female_speaker_1': '9BWtsMINqrJLrRacOk9x',  #Aria
        'female_speaker_2': 'EXAVITQu4vr4xnSDxMaL', #Sarah
        'female_speaker_3': 'Xb7hH8MSUJpSbSDYk0k2', #Alice
        'female_speaker_4': 'XrExE9yKIg1WjnnlVkGX', #Matilda
        'female_speaker_5': 'pFZP5JQG7iQjIQuC4Bku', #Lily
        'male_speaker_1': 'JBFqnCBsd6RMkjVDRZzb', #George
        'male_speaker_2': 'TX3LPaxmHKxFdv7VOQHJ', #Liam
        'male_speaker_3': 'bIHbv24MWmeRgasZH58o', #Will
        'male_speaker_4': 'iP95p4xoKVk53GoZ742B', #Chris
        'male_speaker_5': 'pqHfZKP75CvOlQylNhV4', #Bill
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
        
 
    def _init_database(self):
        """Initialize SQLite database for storing audio files"""
        print(f"Initializing database at: {self.db_path}")  # Add this
        
        try:
            # Check if directory exists
            import os
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
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
            
            # Verify table was created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_files'")
            result = cursor.fetchone()
            print(f"Table exists: {result is not None}")  # Add this
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            print(f"Database error: {str(e)}")  # Add this for immediate feedback
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
            voice_id = self.voice_mapping.get(speaker, self.voice_mapping['female_speaker_1'])
            
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
        
        Args:
            audio_segments: List of audio data in bytes format
            filename: Base filename for output (without extension)
            
        Returns:
            str: Path to the combined audio file
        """
        # Input validation
        if not audio_segments:
            raise ValueError("No audio segments provided")
        
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        # Clean filename to avoid path issues
        filename = filename.strip().replace('/', '_').replace('\\', '_')
        
        print(f"Processing {len(audio_segments)} audio segments for file: {filename}")
        
        # Ensure audio directory exists
        audio_dir = 'audio'
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
            print(f"Created audio directory: {audio_dir}")
        
        temp_files = []  # Keep track of temp files for cleanup
        
        try:
            combined_audio = AudioSegment.empty()
            
            for i, audio_bytes in enumerate(audio_segments):
                print(f"Processing segment {i+1}/{len(audio_segments)}")
                
                # Validate audio bytes
                if not audio_bytes:
                    print(f"Warning: Empty audio bytes for segment {i+1}, skipping")
                    continue
                
                if not isinstance(audio_bytes, bytes):
                    raise TypeError(f"Segment {i+1} is not bytes type: {type(audio_bytes)}")
                
                print(f"Segment {i+1} size: {len(audio_bytes)} bytes")
                
                # Create temporary file for each segment
                temp_file = None
                try:
                    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    temp_file.write(audio_bytes)
                    temp_file.flush()  # Ensure data is written to disk
                    temp_file_path = temp_file.name
                    temp_file.close()  # Close file handle before reading
                    
                    temp_files.append(temp_file_path)  # Track for cleanup
                    
                    print(f"Created temp file: {temp_file_path}")
                    
                    # Verify temp file was created and has content
                    if not os.path.exists(temp_file_path):
                        raise FileNotFoundError(f"Temp file was not created: {temp_file_path}")
                    
                    temp_file_size = os.path.getsize(temp_file_path)
                    if temp_file_size == 0:
                        raise ValueError(f"Temp file is empty: {temp_file_path}")
                    
                    print(f"Temp file size: {temp_file_size} bytes")
                    
                    # Try to load audio segment with multiple format attempts
                    segment = None
                    load_successful = False
                    
                    # Try different formats in order of likelihood
                    formats_to_try = [
                        ('mp3', 'MP3'),
                        ('mp4', 'MP4/AAC'),
                        ('wav', 'WAV'),
                        ('m4a', 'M4A'),
                        ('aac', 'AAC')
                    ]
                    
                    for format_name, format_description in formats_to_try:
                        try:
                            segment = AudioSegment.from_file(temp_file_path, format=format_name)
                            print(f"Successfully loaded segment {i+1} as {format_description}")
                            load_successful = True
                            break
                        except Exception as format_error:
                            print(f"Failed to load segment {i+1} as {format_description}: {str(format_error)}")
                            continue
                    
                    # If no format worked, try without specifying format (let pydub auto-detect)
                    if not load_successful:
                        try:
                            segment = AudioSegment.from_file(temp_file_path)
                            print(f"Successfully loaded segment {i+1} with auto-detection")
                            load_successful = True
                        except Exception as auto_error:
                            print(f"Auto-detection failed for segment {i+1}: {str(auto_error)}")
                    
                    if not load_successful:
                        raise ValueError(f"Could not load audio segment {i+1} in any supported format")
                    
                    # Validate loaded segment
                    if segment is None or len(segment) == 0:
                        print(f"Warning: Loaded segment {i+1} has zero duration, skipping")
                        continue
                    
                    print(f"Segment {i+1} duration: {len(segment)}ms, channels: {segment.channels}, frame_rate: {segment.frame_rate}")
                    
                    # Add small pause between segments (0.5 seconds)
                    if i > 0 and len(combined_audio) > 0:
                        pause = AudioSegment.silent(duration=500)
                        combined_audio += pause
                        print(f"Added 500ms pause after segment {i}")
                    
                    # Add segment to combined audio
                    combined_audio += segment
                    print(f"Added segment {i+1} to combined audio")
                    
                except Exception as segment_error:
                    print(f"Error processing segment {i+1}: {str(segment_error)}")
                    # Don't raise here, just log and continue with other segments
                    logger.error(f"Failed to process segment {i+1}: {str(segment_error)}")
                    continue
                
                finally:
                    # Clean up temp file immediately after processing
                    if temp_file and not temp_file.closed:
                        temp_file.close()
            
            # Check if we have any audio to save
            if len(combined_audio) == 0:
                raise ValueError("No valid audio segments were processed")
            
            print(f"Combined audio duration: {len(combined_audio)}ms")
            
            # Save combined audio
            output_path = os.path.join(audio_dir, f"{filename}.mp3")
            
            # Ensure we don't overwrite existing files
            counter = 1
            original_output_path = output_path
            while os.path.exists(output_path):
                base_name = f"{filename}_{counter}"
                output_path = os.path.join(audio_dir, f"{base_name}.mp3")
                counter += 1
            
            if output_path != original_output_path:
                print(f"File exists, saving as: {output_path}")
            
            # Export with specific parameters for better compatibility
            combined_audio.export(
                output_path, 
                format="mp3",
                bitrate="192k",  # Good quality bitrate
                parameters=["-ac", "2"]  # Ensure stereo output
            )
            
            # Verify output file was created
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Output file was not created: {output_path}")
            
            output_size = os.path.getsize(output_path)
            if output_size == 0:
                raise ValueError(f"Output file is empty: {output_path}")
            
            print(f"Combined audio saved successfully: {output_path} ({output_size} bytes)")
            logger.info(f"Combined audio saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to combine audio segments: {str(e)}"
            print(f"ERROR: {error_msg}")
            logger.error(error_msg)
            raise
        
        finally:
            # Clean up all temporary files
            for temp_file_path in temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        print(f"Cleaned up temp file: {temp_file_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not delete temp file {temp_file_path}: {cleanup_error}")


    # Additional helper method for debugging audio data
    def debug_audio_bytes(self, audio_bytes: bytes, segment_number: int) -> dict:
        """
        Debug helper to analyze audio bytes data
        
        Args:
            audio_bytes: Raw audio data
            segment_number: Segment number for logging
            
        Returns:
            dict: Debug information about the audio data
        """
        debug_info = {
            'segment_number': segment_number,
            'size_bytes': len(audio_bytes) if audio_bytes else 0,
            'is_bytes': isinstance(audio_bytes, bytes),
            'is_empty': not bool(audio_bytes),
            'first_16_bytes': None,
            'likely_format': 'unknown'
        }
        
        if audio_bytes and len(audio_bytes) >= 16:
            debug_info['first_16_bytes'] = audio_bytes[:16].hex()
            
            # Check for common audio format signatures
            if audio_bytes.startswith(b'ID3') or audio_bytes[0:2] == b'\xff\xfb':
                debug_info['likely_format'] = 'mp3'
            elif audio_bytes.startswith(b'ftyp'):
                debug_info['likely_format'] = 'mp4/m4a'
            elif audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:12]:
                debug_info['likely_format'] = 'wav'
            elif audio_bytes.startswith(b'\xff\xf1') or audio_bytes.startswith(b'\xff\xf9'):
                debug_info['likely_format'] = 'aac'
        
        print(f"Debug info for segment {segment_number}: {debug_info}")
        return debug_info


    # Example usage with enhanced error handling
    def test_combine_audio_segments(self):
        """
        Test function to demonstrate proper usage
        """
        # Mock audio segments (you would get these from ElevenLabs API)
        audio_segments = [
            b'mock_audio_data_1',  # Replace with actual audio bytes
            b'mock_audio_data_2',
            b'mock_audio_data_3'
        ]
        
        filename = "test_podcast_episode"
        
        try:
            # Debug each segment first
            for i, segment in enumerate(audio_segments):
                self.debug_audio_bytes(segment, i+1)
            
            # Combine segments
            output_path = self._combine_audio_segments(audio_segments, filename)
            print(f"Success! Combined audio saved to: {output_path}")
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
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