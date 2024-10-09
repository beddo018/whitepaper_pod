import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
from arxiv import query, query_for_pdf
from transcript_generator import generate_transcript
from text_to_speech import convert_to_audio
import fitz  # PyMuPDF
import certifi
import ssl
import urllib.request
import os

ssl._create_default_https_context = ssl._create_unverified_context
urllib.request.urlopen('https://example.com', cafile=certifi.where())

app = Flask(__name__)

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

def split_text_into_chunks(text, chunk_size=1000):
    chunks = []
    sentences = text.split('. ')
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def run_nougat_on_pdf(pdf_path, output_dir):
    try:
        subprocess.run(["nougat", pdf_path, "-o", output_dir], check=True)
        # Read the output .mmd file
        output_file = output_dir + "/output.mmd"
        with open(output_file, "r") as file:
            nougat_output = file.read()
        return nougat_output
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to run NOUGAT: {e}")

def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append(image_bytes)
    return images

def describe_image(image_bytes):
    # Placeholder for image description logic
    # You can use a service like Google Cloud Vision to describe the image
    return "Description of the image"
    
def process_pdf_to_text_and_images(pdf_content):
    # Save the PDF content temporarily
    pdf_file_path = "/tmp/temp_pdf.pdf"
    try:
        with open(pdf_file_path, "wb") as pdf_file:
            pdf_file.write(pdf_content)
            print(f"PDF successfully saved to {pdf_file_path}")
    except Exception as e:
        print(f"Failed to save PDF: {str(e)}")
        raise

    # Process with NOUGAT
    nougat_output = run_nougat_on_pdf(pdf_file_path, "/tmp")

    # Extract images
    images = extract_images_from_pdf(pdf_file_path)
    image_descriptions = [describe_image(image) for image in images]

    # Combine text and image descriptions
    combined_output = nougat_output + "\n\n" + "\n".join(image_descriptions)
    return combined_output


def process_and_generate_transcript_with_nougat(paper_pdf_url):
    pdf_content = query_for_pdf(paper_pdf_url)
    if not pdf_content:
        raise Exception("Failed to retrieve the PDF content")

    # Process PDF and include NOUGAT-generated text
    extracted_text, image_descriptions = process_pdf_to_text_and_images(pdf_content)
    
    # Split text into manageable chunks
    text_chunks = split_text_into_chunks(extracted_text)
    
    # Generate a transcript for each chunk
    full_transcript = ""
    for chunk in text_chunks:
        transcript = generate_transcript({"title": "Sample Paper", "summary": chunk}, image_descriptions)
        full_transcript += transcript + "\n\n"

    return full_transcript

@app.route('/generate_podcast', methods=['POST'])
def generate_podcast():
    selected_paper_url = request.json.get('paper_id')
    selected_paper_title = request.json.get('paper_title').replace(' ', '_')  # Replace spaces for URL

    try:
        final_transcript = process_and_generate_transcript_with_nougat(selected_paper_url)
        filename = f"{selected_paper_title}_{int(time.time())}.mp3"
        audio_path = convert_to_audio(final_transcript, filename)
        audio_url = request.host_url + 'static/audio/' + filename

        result = {
            "title": selected_paper_title,
            "transcript": final_transcript,
            "audio_url": audio_url
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('static/audio', filename)

if __name__ == '__main__':
    app.run(debug=True)
