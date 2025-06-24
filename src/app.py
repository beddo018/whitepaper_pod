import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
from server.generate_transcript.arxiv import query, query_for_pdf
from server.generate_transcript.transcript_generator import generate_transcript
from server.generate_audio.text_to_speech_openai import convert_to_audio
from server.generate_transcript.pdf_processor import process_pdf
from server.generate_audio.TTSMiddleware import TTSMiddleware
import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from flask import current_app, jsonify
from elevenlabs import ElevenLabs
from pydub import AudioSegment
import tempfile
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from celery import Celery
import os
from pathlib import Path

# Initialize Flask app with correct template and static folders
app = Flask(__name__, 
           template_folder='client/templates',
           static_folder='client/static')

# Initialize Celery
celery = Celery('whitepaper_pod', broker='redis://localhost:6379/0')

# Ensure required directories exist
Path('src/client/static/audio').mkdir(parents=True, exist_ok=True)
Path('tmp').mkdir(exist_ok=True)

def create_tts_middleware(app):
    """
    Factory function to create and configure TTS middleware
    """
    # Configure ElevenLabs API key and voice mapping
    app.config['ELEVENLABS_API_KEY'] = 'YOUR_API_KEY'  # Replace with actual API key
    app.config['VOICE_MAPPING'] = {
        'speaker_1': 'iP95p4xoKVk53GoZ742B',  # Replace with actual voice IDs
        'speaker_2': 'EXAVITQu4vr4xnSDxMaL',
        'speaker_3': '9BWtsMINqrJLrRacOk9x',
        'speaker_4': 'XrExE9yKIg1WjnnlVkGX',
        'speaker_5': 'onwK4e9ZLuTAKqWW03F9',
    }
    
    # Create and initialize middleware
    tts_middleware = TTSMiddleware(app)
    
    return tts_middleware

# Initialize TTS middleware
tts_middleware = create_tts_middleware(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_papers', methods=['POST'])
def search_papers():
    query_string = request.json.get('query_string')
    query_params = f"search_query={query_string}&max_results=10"
    papers = query(query_params)
    
    if not papers:
        return jsonify({"error": "No papers found for the given query."}), 404
    
    return jsonify(papers)

@celery.task
def process_paper_async(paper_url, paper_title):
    """
    Asynchronous task to process a paper
    """
    try:
        # Get PDF content
        pdf_content = query_for_pdf(paper_url)
        if not pdf_content:
            raise Exception("Failed to retrieve the PDF content")

        # Process PDF
        text, image_descriptions = process_pdf(pdf_content)
        
        # Generate transcript
        transcript = generate_transcript({
            "title": paper_title,
            "summary": text
        }, image_descriptions)

        # Generate audio
        filename = f"{paper_title.replace(' ', '_')}_{int(time.time())}.mp3"
        audio_path = convert_to_audio(transcript, filename)

        return {
            "title": paper_title,
            "transcript": transcript,
            "audio_url": f"/static/audio/{filename}"
        }
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        raise

@app.route('/generate_podcast', methods=['POST'])
def generate_podcast():
    if not request.json:
        return jsonify({"error": "No JSON data provided"}), 400
    
    selected_paper_url = request.json.get('paper_id')
    selected_paper_title = request.json.get('paper_title')
    
    if not selected_paper_url or not selected_paper_title:
        return jsonify({"error": "Missing paper_id or paper_title"}), 400

    try:
        # Start async processing
        task = process_paper_async.delay(selected_paper_url, selected_paper_title)
        return jsonify({"task_id": task.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/task_status/<task_id>')
def task_status(task_id):
    task = process_paper_async.AsyncResult(task_id)
    if task.ready():
        if task.successful():
            return jsonify(task.result)
        else:
            return jsonify({"error": str(task.result)}), 500
    return jsonify({"status": "processing"})

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('src/client/static/audio', filename)

@app.route('/convert-to-audio', methods=['POST'])
def convert_text_to_audio():
    try:
        data = request.get_json()
        
        if not data or 'transcript' not in data or 'filename' not in data:
            return jsonify({'error': 'Missing transcript or filename'}), 400
        
        transcript = data['transcript']
        filename = data['filename']
        
        # Convert to audio using middleware
        audio_path = tts_middleware.convert_to_audio(transcript, filename)
        
        # Return success response with file path
        return jsonify({
            'success': True,
            'message': 'Audio generated successfully',
            'filename': filename,
            'audio_path': audio_path
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Route error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download-audio/<filename>')
def download_audio(filename):
    """Download generated audio file"""
    try:
        audio_path = os.path.join('audio', f"{filename}.mp3")
        if os.path.exists(audio_path):
            return send_file(audio_path, as_attachment=True)
        else:
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)