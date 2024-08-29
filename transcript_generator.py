import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_transcript(paper):
    messages = [
        {"role": "system", "content": "You are an expert in AI/ML. You're extremely good at distilling complex ideas from AI and ML white papers and contextualizing them within a broader or more concrete environment."},
        {"role": "user", "content": f"Convert the following AI/ML white paper into a podcast-style interview between an expert guest who represents the paper writers, and a tech enthusiast host who is a programmer but not an expert in AI or ML. Format the response in SSML, using different voices for the 'host' and 'expert' roles:\n\nTitle: {paper['title']}\n\nSummary: {paper['summary']}\n\nInterview Transcript in SSML:"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=1500,
        temperature=0.7
    )
    
    return response.choices[0].message['content'].strip()
