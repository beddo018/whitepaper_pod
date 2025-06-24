import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Anthropic client with minimal configuration
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

def generate_transcript(paper, image_descriptions=None):
    prompt = f"""Convert the following AI/ML white paper into a podcast-style interview between an expert guest who represents the paper writers, and a tech enthusiast host who is a programmer but not an expert in AI or ML. Format the response in SSML, using different voices for the 'host' and 'expert' roles:

Title: {paper['title']}

Summary: {paper['summary']}

Interview Transcript in SSML:

Keep the podcast to 5 minutes."""


    if image_descriptions:
        image_context = "\n\n".join(image_descriptions)
        prompt += f"\n\nImage Descriptions:\n{image_context}"

    # Using the new SDK style (Anthropic class)
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1500,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in AI/ML. You're extremely good at distilling complex ideas from AI and ML white papers and contextualizing them within a broader or more concrete environment."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    # Access the response content correctly for SDK 0.35.0
    return response.content
