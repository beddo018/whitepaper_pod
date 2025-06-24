import os
from openai import OpenAI
import sqlite3
from pathlib import Path
import re
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings, play

# hardcoded transcript, filename, and ssml_text
from transcript import transcript, filename, ssml_text

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure directories exist
audio_dir = Path('src/client/static/audio')
tmp_dir = Path('tmp')
audio_dir.mkdir(parents=True, exist_ok=True)
tmp_dir.mkdir(exist_ok=True)

# Database setup
def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        conn = sqlite3.connect('audio_files.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript TEXT,
            audio BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        return conn, cursor
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def extract_ssml_speakers(ssml_text):
    """
    Extract speaker roles from SSML text
    """
    speakers = set()
    # Look for voice tags in SSML
    voice_tags = re.findall(r'\*{3}(.+?)\*{3}', ssml_text)
    speakers.update(voice_tags)
    return list(speakers)

def convert_to_audio(transcript, filename):
    """
    Convert transcript to audio using OpenAI's TTS API
    Supports multiple voices and SSML
    """
    try:
        # Extract speakers from SSML
        speakers = extract_ssml_speakers(transcript)
        
        # Map speakers to OpenAI voices
        voice_mapping = {
            'host': 'iP95p4xoKVk53GoZ742B',
            speakers[0]: 'EXAVITQu4vr4xnSDxMaL',
            speakers[1]: '9BWtsMINqrJLrRacOk9x',
            speakers[2]: 'XrExE9yKIg1WjnnlVkGX',
            speakers[3]: 'onwK4e9ZLuTAKqWW03F9',
            speakers[4]: 'N2lVS1w4EtoT3dr4eOWO'
        }
        
        # Generate audio for each speaker
        audio_segments = []
        for speaker in speakers:
            # Extract text for this speaker
            speaker_pattern = f'<voice name="{speaker}">(.*?)</voice>'
            speaker_text = re.findall(speaker_pattern, transcript, re.DOTALL)
            
            if speaker_text:
                # Get OpenAI voice
                openai_voice = voice_mapping.get(speaker, 'alloy')
                
                # Generate audio for this segment
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=openai_voice,
                    input=speaker_text[0]
                )
                
                # Save segment
                segment_path = tmp_dir / f"{speaker}_{filename}"
                response.stream_to_file(str(segment_path))
                audio_segments.append(segment_path)
        
        # Combine audio segments
        combined = AudioSegment.empty()
        for segment in audio_segments:
            audio = AudioSegment.from_file(str(segment))
            combined += audio
            os.remove(segment)  # Clean up segment file
        
        # Save final audio
        audio_path = audio_dir / filename
        combined.export(str(audio_path), format="mp3")

        # Store in database
        conn, cursor = get_db_connection()
        try:
            with open(audio_path, 'rb') as audio_file:
                audio_blob = audio_file.read()
                cursor.execute('''
                INSERT INTO audio_files (transcript, audio)
                VALUES (?, ?)
                ''', (transcript, audio_blob))
                conn.commit()
        finally:
            conn.close()

        return str(audio_path)
    except Exception as e:
        print(f"Error converting to audio: {str(e)}")
        raise

def close_connection():
    """Close database connection - kept for backward compatibility"""
    pass  # Connection is now managed per function call