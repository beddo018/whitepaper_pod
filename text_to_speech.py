from google.cloud import texttospeech
import os
import sqlite3
import requests

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/woddeb/Documents/coral-ethos-432720-e0-f50d927c6e12.json'

# Initialize Google Cloud TTS client
client = texttospeech.TextToSpeechClient()

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
    synthesis_input = texttospeech.SynthesisInput(ssml=transcript)

    # Voice selection for character 'host' and 'expert'
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D"  # Choose appropriate voice
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    request = texttospeech.SynthesizeSpeechRequest(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    response = client.synthesize_speech(request=request)

    audio_content = response.audio_content

    cursor.execute('''
    INSERT INTO audio_files (transcript, audio)
    VALUES (?, ?)
    ''', (transcript, audio_content))
    conn.commit()

    audio_path = os.path.join('static', 'audio', filename)
    with open(audio_path, 'wb') as audio_file:
        audio_file.write(audio_content)

    return audio_path

def close_connection():
    conn.close()
