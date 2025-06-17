import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
from arxiv import query, query_for_pdf
from transcript_generator import generate_transcript
from text_to_speech_openai import convert_to_audio
from pdf_processor import process_pdf
from celery import Celery
import os
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Initialize Celery
celery = Celery('whitepaper_pod', broker='redis://localhost:6379/0')

# Ensure required directories exist
Path('static/audio').mkdir(parents=True, exist_ok=True)
Path('tmp').mkdir(exist_ok=True)

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
    selected_paper_url = request.json.get('paper_id')
    selected_paper_title = request.json.get('paper_title')

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
    return send_from_directory('static/audio', filename)

if __name__ == '__main__':
    app.run(debug=True)