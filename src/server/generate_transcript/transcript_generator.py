import anthropic
from dotenv import load_dotenv
import os
import json
from src.server.generate_transcript.prompts.prompts import build_system_prompt, build_user_prompt
from src.server.generate_transcript.paper_example import paper

load_dotenv()

# Initialize Anthropic client with minimal configuration
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

def generate_transcript(paper, options, image_descriptions=None):
    # Using the new SDK style (Anthropic class)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0.7,
        system=build_system_prompt(),
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(paper, options, image_descriptions)
            }
        ]
    )

    # Parse the JSON response into structured segments
    try:
        transcript_text = response.content[0].text.strip()
        print(f"Raw transcript response length: {len(transcript_text)}")
        
        # Check if response was truncated
        if hasattr(response, 'stop_reason') and response.stop_reason == 'max_tokens':
            print("WARNING: Response was truncated due to max_tokens limit")
        
        # Remove any markdown code blocks if present
        if transcript_text.startswith('```json'):
            transcript_text = transcript_text[7:]
        if transcript_text.endswith('```'):
            transcript_text = transcript_text[:-3]
        
        # Try to find the JSON array boundaries
        start_idx = transcript_text.find('[')
        end_idx = transcript_text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            transcript_text = transcript_text[start_idx:end_idx + 1]
        
        # Try to parse the JSON
        try:
            segments = json.loads(transcript_text)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Problematic text: {transcript_text[max(0, e.pos-50):e.pos+50]}")
            
            # Try to fix common JSON issues
            # Remove any trailing commas
            transcript_text = transcript_text.replace(',]', ']').replace(',}', '}')
            
            # Try to complete any unterminated strings
            if transcript_text.count('"') % 2 != 0:
                # Find the last quote and add a closing quote
                last_quote = transcript_text.rfind('"')
                if last_quote != -1:
                    # Check if it's an unterminated string
                    if not transcript_text[last_quote:].strip().endswith('"'):
                        transcript_text = transcript_text[:last_quote+1] + '"' + transcript_text[last_quote+1:]
            
            # Try parsing again
            segments = json.loads(transcript_text)
        
        # Validate the structure
        if not isinstance(segments, list):
            raise ValueError("Transcript must be a list of segments")
        
        for segment in segments:
            if not isinstance(segment, dict) or 'speaker' not in segment or 'text' not in segment:
                raise ValueError("Each segment must have 'speaker' and 'text' fields")
        
        print(f"Successfully parsed {len(segments)} transcript segments")
        return segments
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse transcript JSON: {e}")
        print(f"Raw response: {response.content[0].text}")
        
        # Create a fallback transcript with a single speaker
        fallback_segments = [
            {
                "speaker": "female_speaker_1",
                "text": f"I'm sorry, but there was an issue generating the podcast transcript for '{paper.get('title', 'this paper')}'. The paper discusses {paper.get('summary', 'scientific research')[:200]}... Let me provide a brief overview of the key findings."
            }
        ]
        print("Using fallback transcript")
        return fallback_segments
        
    except Exception as e:
        print(f"Error processing transcript: {e}")
        raise

### FOR TESTING LOCALLY
if __name__ == "__main__":
    options = { "length_minutes" : 10, "listener_expertise_level" : 'Intermediate', "number_of_speakers" : 3 }
    transcript = generate_transcript(paper,options)
    print(transcript)