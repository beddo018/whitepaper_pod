import pdfplumber
import pytesseract
from PIL import Image
import io
import os
from pathlib import Path

from server.generate_transcript.image_processor import process_pdf_images

def extract_text_from_pdf(pdf_content):
    """
    Extract text from PDF using pdfplumber
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_images_from_pdf(pdf_content):
    """
    Extract and process images from PDF
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            images = []
            for page in pdf.pages:
                for image in page.images:
                    img = Image.open(io.BytesIO(image['stream'].get_data()))
                    text = pytesseract.image_to_string(img)
                    if text.strip():  # Only add if text was found
                        images.append(text)
        return images
    except Exception as e:
        print(f"Error extracting images from PDF: {str(e)}")
        raise
   
def process_pdf(pdf_content):
    text = extract_text_from_pdf(pdf_content)
    image_descriptions = process_pdf_images(pdf_content)
    return text, image_descriptions