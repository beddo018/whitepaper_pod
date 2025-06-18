import os
from openai import OpenAI
import sqlite3
from pathlib import Path
import re

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure audio directory exists
audio_dir = Path('static/audio')
audio_dir.mkdir(parents=True, exist_ok=True)

# Database setup
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

def extract_ssml_speakers(ssml_text):
    """
    Extract speaker roles from SSML text
    """
    speakers = set()
    # Look for voice tags in SSML
    voice_tags = re.findall(r'<voice name="([^"]+)">', ssml_text)
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
            'host': 'alloy',
            'expert': 'nova',
            'panelist1': 'echo',
            'panelist2': 'fable'
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
                segment_path = f"tmp/{speaker}_{filename}"
                response.stream_to_file(segment_path)
                audio_segments.append(segment_path)
        
        # Combine audio segments
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for segment in audio_segments:
            audio = AudioSegment.from_file(segment)
            combined += audio
            os.remove(segment)  # Clean up segment file
        
        # Save final audio
        audio_path = os.path.join('static', 'audio', filename)
        combined.export(audio_path, format="mp3")

        # Store in database
        with open(audio_path, 'rb') as audio_file:
            audio_blob = audio_file.read()
            cursor.execute('''
            INSERT INTO audio_files (transcript, audio)
            VALUES (?, ?)
            ''', (transcript, audio_blob))
            conn.commit()

        return audio_path
    except Exception as e:
        print(f"Error converting to audio: {str(e)}")
        raise

def close_connection():
    conn.close()