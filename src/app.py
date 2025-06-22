import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
from src.server.generate_transcript.arxiv import query, query_for_pdf
from src.server.generate_transcript.transcript_generator import generate_transcript
from src.server.generate_audio.text_to_speech_openai import convert_to_audio
from src.server.generate_transcript.pdf_processor import process_pdf
from celery import Celery

# Check if we're in development mode
DEV_MODE = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG') == '1'

# Initialize Flask app with React's build folder as static folder
if DEV_MODE:
    # In development, we only serve API routes - React is served by Vite
    app = Flask(__name__)
    print("Running in DEVELOPMENT mode - React hot-reload available on http://localhost:8080")
else:
    # In production, serve from built dist folder
    app = Flask(__name__,
                static_folder='client/dist',
                template_folder='client/dist')
    print("Running in PRODUCTION mode - serving built React app")

# Initialize Celery
celery = Celery('whitepaper_pod', 
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Ensure required directories exist
Path('src/client/static/audio').mkdir(parents=True, exist_ok=True)
Path('tmp').mkdir(exist_ok=True)

print(f"Static folder: {app.static_folder}")

# Only serve React app in production mode
if not DEV_MODE:
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        """
        Serve React app for all non-API routes.
        """
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path):  # Serve the requested file if it exists
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')  # Default to index.html

@app.route('/api/search_papers', methods=['POST'])
def search_papers():
    query_string = request.json.get('query_string')
    query_params = f"search_query={query_string}&max_results=10"
    papers = query(query_params)
    
    if not papers:
        return jsonify({"error": "No papers found for the given query."}), 404
    
    return jsonify(papers)

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file uploads"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.endswith('.pdf'):
        # For now, just return a mock response
        # In a real implementation, you'd save the file and process it
        return jsonify({
            "success": True,
            "filename": file.filename,
            "title": file.filename.replace('.pdf', ''),
            "message": "PDF uploaded successfully"
        })
    
    return jsonify({"error": "Invalid file type"}), 400

@celery.task
def process_paper_async(paper_url, paper_title):
    try:
        pdf_content = query_for_pdf(paper_url)
        if not pdf_content:
            raise Exception("Failed to retrieve the PDF content")

        text, image_descriptions = process_pdf(pdf_content)
        transcript = generate_transcript({
            "title": paper_title,
            "summary": text
        }, image_descriptions)

        filename = f"{paper_title.replace(' ', '_')}.mp3"
        audio_path = convert_to_audio(transcript, filename)

        return {
            "title": paper_title,
            "transcript": transcript,
            "audio_url": f"/static/audio/{filename}"
        }
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        raise

@app.route('/api/generate_podcast', methods=['POST'])
def generate_podcast():
    selected_paper_url = request.json.get('paper_id')
    selected_paper_title = request.json.get('paper_title')

    try:
        task = process_paper_async.delay(selected_paper_url, selected_paper_title)
        return jsonify({"task_id": task.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/task_status/<task_id>')
def task_status(task_id):
    task = process_paper_async.AsyncResult(task_id)
    if task.ready():
        if task.successful():
            return jsonify(task.result)
        else:
            return jsonify({"error": str(task.result)}), 500
    return jsonify({
        "status": "processing",
        "current_step": "Processing document...",
        "progress": 50
    })

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('src/client/static/audio', filename)

if __name__ == '__main__':
    app.run(debug=True)