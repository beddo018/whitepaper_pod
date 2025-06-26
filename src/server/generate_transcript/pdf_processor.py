import pdfplumber
import os
from openai import OpenAI
import base64
from PIL import Image
import io

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_image(image):
    """
    Analyze an image using OpenAI's Vision API
    Returns a detailed description of the image content
    """
    try:
        # Convert image to base64
        base64_image = encode_image_to_base64(image)
        
        # Use chat.completions API for vision (responses API doesn't support vision yet)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in analyzing scientific figures, charts, and diagrams. Provide detailed descriptions that would be helpful for someone listening to a podcast about the paper."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this figure from a scientific paper. Describe what it shows, its key findings, and any important patterns or relationships you notice."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
                
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        # Return a generic description instead of failing completely
        return "This figure contains scientific data that would be discussed in the podcast."

def process_pdf(pdf_content):
    """
    Main function to process PDF and return both text and image descriptions
    """
    try:
        # Extract text and images in a single PDF parsing operation
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            image_descriptions = []
            
            for page_num, page in enumerate(pdf.pages):
                # Extract text from page
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Extract and process images from page
                for img_num, image in enumerate(page.images):
                    try:
                        img = Image.open(io.BytesIO(image['stream'].get_data()))
                        description = analyze_image(img)
                        image_descriptions.append({
                            'page': page_num + 1,
                            'image': img_num + 1,
                            'description': description
                        })
                    except Exception as e:
                        print(f"Error processing image on page {page_num + 1}: {str(e)}")
                        continue
        
        return text, image_descriptions
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        raise

# if __name__ == "__main__":
#     paper = process_pdf(content)
#     print(paper)