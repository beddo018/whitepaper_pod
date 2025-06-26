import time
import os
import socket
import logging
from pathlib import Path
from flask import Flask, render_template, send_from_directory, jsonify, request, send_file
from src.server.generate_transcript.arxiv import query, query_for_pdf
from src.server.generate_transcript.transcript_generator import generate_transcript
from src.server.generate_audio.audio_generator import TTSMiddleware
from src.server.generate_transcript.pdf_processor import process_pdf
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    task_routes={
        'src.app.process_paper_async': {'queue': 'celery'}
    },
    imports=['src.app']
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
def process_paper_async(paper_url, paper_title, podcast_settings=None):
    try:
        pdf_content = query_for_pdf(paper_url)
        print(pdf_content)
        if not pdf_content:
            raise Exception("Failed to retrieve the PDF content")

        text, image_descriptions = process_pdf(pdf_content)
        options = {
            "length_minutes" : 5, 
            "listener_expertise_level" : 
            "Intermediate", "number_of_speakers" : 3 
        };

        transcript = generate_transcript({
            "title": paper_title,
            "summary": text
<<<<<<< transcript-generation
        }, options, image_descriptions)

        filename = f"{paper_title.replace(' ', '_')}.mp3"
        audio_path = convert_to_audio(transcript, filename)
=======
        }, image_descriptions, podcast_settings)
                # Generate audio
        filename = f"{paper_title.replace(' ', '_')}_{int(time.time())}"
        tts_middleware = TTSMiddleware()
        audio_path = tts_middleware.convert_to_audio(transcript, filename) #transcript needs to be a list of dicts
>>>>>>> main

        return {
            "title": paper_title,
            "transcript": transcript,
            "audio_url": f"/static/audio/{filename}",
            "audio_path": audio_path
        }
    except Exception as e:
        print(f"Error processing paper: {str(e)}")
        raise

@app.route('/api/generate_podcast', methods=['POST'])
def generate_podcast():
    if not request.json:
        return jsonify({"error": "No JSON data provided"}), 400

    selected_paper_url = request.json.get('paper_id')
    selected_paper_title = request.json.get('paper_title')
    podcast_settings = request.json.get('settings')  # Get podcast settings

    if not selected_paper_url or not selected_paper_title:
        return jsonify({"error": "Missing paper_id or paper_title"}), 400

    try:
        task = process_paper_async.delay(selected_paper_url, selected_paper_title, podcast_settings)
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
    return send_from_directory('src/audio', filename)

@app.route('/convert-to-audio', methods=['POST'])
def convert_text_to_audio():
    try:
        data = request.get_json()

        if not data or 'transcript' not in data or 'filename' not in data:
            return jsonify({'error': 'Missing transcript or filename'}), 400

        transcript = data['transcript']
        filename = data['filename']

        tts_middleware = TTSMiddleware()

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

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return start_port  # Fallback to original port if all attempts fail

if __name__ == '__main__':
    # Allow port override via environment variable
    default_port = int(os.environ.get('FLASK_PORT', 5000))
    port = find_available_port(start_port=default_port)
    print(f"🚀 Starting Flask server on port {port}")
    if port != default_port:
        print(f"⚠️  Port {default_port} was busy, using port {port} instead")
        print(f"📝 Update your Vite proxy config if needed: target: 'http://localhost:{port}'")
    app.run(debug=True, port=port)
