import logging

transcript_example = """[
    {
        "speaker": "female_speaker_1",
        "text": "Good morning and welcome to The Business Hour. I'm Jennifer Adams, and today we're discussing entrepreneurship in the digital age."
    },
    {
        "speaker": "male_speaker_1",
        "text": "Hello everyone, I'm Tom Wilson. We're joined today by Maria Gonzalez, founder of three successful startups and author of 'Digital Disruption'."
    },
    {
        "speaker": "female_speaker_2",
        "text": "Thanks for having me, Jennifer and Tom. I'm excited to share some insights about building businesses in today's rapidly changing landscape."
    },
    {
        "speaker": "female_speaker_1",
        "text": "Maria, you started your first company right out of college. What inspired you to take that entrepreneurial leap so early?"
    },
    {
        "speaker": "male_speaker_2",
        "text": "I saw a gap in the market for mobile solutions for small businesses. Instead of waiting for someone else to fill it, I decided to take action. The worst that could happen was failure, and I figured I was young enough to recover from that."
    },
    {
        "speaker": "male_speaker_1",
        "text": "That's a great attitude. Can you tell us about the biggest challenges you faced in those early days?"
    },
    {
        "speaker": "male_speaker_2",
        "text": "Funding was definitely the biggest hurdle. Traditional investors weren't convinced that mobile-first solutions would take off. I had to bootstrap the company for the first two years while working part-time to pay the bills."
    }
]"""

rules = f"""
Include the speaker's gender in their "speaker" title - for example "female_speaker_1" instead of "speaker_1".
    
Do not include anything exept for the List, starting with '[' and ending with ']'

The podcast should have a clear conclusion / sign-off like a normal episode of a podcast.
"""

def build_system_prompt():
    
    system_prompt = f"""You generate podcast scripts that helps listeners understand published scientific papers. The listener will select a paper for you to read, analyze, and explain. They will also tell you what their experience level with the topic is and how many speakers the podcast should have. 

    It may include 1 narrator explaining the topic or it may be an interview style with 1 host and 1, 2 or 3 subject experts as guests being interviewed about the subject. Each expert will have a name and personality. 
    
    The user will also determine a target length of the podcast. The postcast should end naturally within 10% of the requested length when translated to audio at a standard speaking speed.

    Await the specific settings and paper from the user prompts coming next.

    The most important goals are that the listener understands the paper at the end of the podcast and that they are entertained and engaged throughout.

    The transcript should be output as a VALID JSON array of objects like this example: 
    
    {transcript_example}

    {rules}

    The paper may contain images, in that case, they will be translated to image descriptions and appended at the end of the paper. This may not be where they appear organically in the paper.

    CRITICAL: Ensure your response is valid JSON. Do not include any text before the opening '[' or after the closing ']'. Make sure all strings are properly quoted and escaped. Do not truncate the response mid-sentence or mid-object.

    return the transcript and only the transcript in this format as your response. Do not include any other text in your response.
    """
    
    return system_prompt

def build_user_prompt(paper, options, image_descriptions=None):

    logging.debug(options)

    length_minutes = options["length_minutes"]
    listener_expertise_level = options["listener_expertise_level"]
    number_of_speakers = options["number_of_speakers"]

    user_prompt = f"""Convert the following research paper to a podcast per systems instructions and listener specifications.

Listener Specifications:
    - Keep the podcast with 10% of {length_minutes} minutes.
    - Assume that the listener has the experience level on this topic equivalent to a {listener_expertise_level}
    - Include {number_of_speakers} speakers, including one host. In the case of 1 speaker, the host is a subject matter expert explaining the topic.

Paper:

Title: {paper['title']}

Summary: {paper['summary']}"""
    
    if image_descriptions:
        image_context = "\n\n".join([f"Page {desc['page']}, Image {desc['image']}: {desc['description']}" for desc in image_descriptions])
        user_prompt += f"\n\nImage Descriptions:\n{image_context}"

    return user_prompt 