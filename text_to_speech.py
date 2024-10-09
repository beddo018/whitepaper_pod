from elevenlabs import generate, save
import os
import sqlite3

# Database setup
conn = sqlite3.connect('audio_files.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript TEXT,
    audio BLOB
)
''')
conn.commit()

def convert_to_audio(transcript, filename):
    # Generate audio using ElevenLabs
    audio_content = generate(text=transcript, voice="Rachel", model="eleven_monolingual_v1")

    # Save audio to file
    audio_path = os.path.join('static', 'audio', filename)
    save(audio_content, audio_path)

    # Store audio in the database
    with open(audio_path, 'rb') as audio_file:
        audio_blob = audio_file.read()
        cursor.execute('''
        INSERT INTO audio_files (transcript, audio)
        VALUES (?, ?)
        ''', (transcript, audio_blob))
        conn.commit()

    return audio_path

def close_connection():
    conn.close()
