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
        
        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
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
                            "text": "Please analyze this figure from a scientific paper. Describe what it shows, its key findings, and any important patterns or relationships. Format your response as if you were explaining it to someone in a podcast."
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
        raise

def process_pdf_images(pdf_content):
    """
    Process all images from a PDF using OpenAI's Vision API
    """
    try:
        import pdfplumber
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            image_descriptions = []
            for page_num, page in enumerate(pdf.pages):
                for img_num, image in enumerate(page.images):
                    # Convert image to PIL Image
                    img = Image.open(io.BytesIO(image['stream'].get_data()))
                    
                    # Analyze image
                    description = analyze_image(img)
                    image_descriptions.append({
                        'page': page_num + 1,
                        'image': img_num + 1,
                        'description': description
                    })
        
        return image_descriptions
    except Exception as e:
        print(f"Error processing PDF images: {str(e)}")
        raise