import anthropic
from dotenv import load_dotenv
import os
from prompts.prompts import build_system_prompt, build_user_prompt
from paper_example import paper

load_dotenv()

# Initialize Anthropic client with minimal configuration
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

def generate_transcript(paper, options, image_descriptions=None):
    # Using the new SDK style (Anthropic class)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        temperature=0.7,
        system=build_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(paper, options)
            }
        ]
    )

    return response.content[0].text

### FOR TESTING LOCALLY
if __name__ == "__main__":
    options = { "length_minutes" : 10, "listener_expertise_level" : 'Intermediate', "number_of_speakers" : 3 }
    transcript = generate_transcript(paper,options)
    print(transcript)