from TTS.api import TTS
import os
import sqlite3
from pathlib import Path

# Initialize TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

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

def convert_to_audio(transcript, filename):
    """
    Convert transcript to audio using local TTS and store in database
    """
    try:
        # Generate audio using local TTS
        audio_path = os.path.join('static', 'audio', filename)
        tts.tts_to_file(text=transcript, file_path=audio_path)

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
