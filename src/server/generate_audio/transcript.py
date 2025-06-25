sample_transcript_list = [
    {
        "speaker": "female_speaker_1",
        "text": "Good morning and welcome to The Business Hour." 
        # I'm Jennifer Adams, and today we're discussing entrepreneurship in the digital age."
    },
    {
        "speaker": "male_speaker_1",
        "text": "Hello everyone, I'm Tom Wilson." 
        # We're joined today by Maria Gonzalez, founder of three successful startups and author of 'Digital Disruption'."
    },
    # {
    #     "speaker": "female_speaker_2",
    #     "text": "Thanks for having me, Jennifer and Tom. I'm excited to share some insights about building businesses in today's rapidly changing landscape."
    # },
    # {
    #     "speaker": "female_speaker_1", 
    #     "text": "Maria, you started your first company right out of college. What inspired you to take that entrepreneurial leap so early?"
    # },
    # {
    #     "speaker": "male_speaker_2",
    #     "text": "I saw a gap in the market for mobile solutions for small businesses. Instead of waiting for someone else to fill it, I decided to take action. The worst that could happen was failure, and I figured I was young enough to recover from that."
    # },
    # {
    #     "speaker": "male_speaker_1",
    #     "text": "That's a great attitude. Can you tell us about the biggest challenges you faced in those early days?"
    # },
    # {
    #     "speaker": "male_speaker_2",
    #     "text": "Funding was definitely the biggest hurdle. Traditional investors weren't convinced that mobile-first solutions would take off. I had to bootstrap the company for the first two years while working part-time to pay the bills."
    # }
]


transcriptML = """*Host (Riley Thompson):** Welcome to “AlignML,” the podcast where we pull back the curtain on cutting-edge AI safety research. I’m your host, Riley Thompson. Today, we’re diving into a brand-new paper from arXiv—one that spotlights a subtle but critical side‐effect of fine-tuning large language models: the erosion of their ability to admit “I don’t know.”  

Joining me are four experts:  
- ***Dr. Elena Garcia***, a Safety Alignment Specialist  
- ***Prof. James Liu***, Theoretical ML Researcher  
- ***Dr. Maria Nguyen***, Applied NLP Engineer  
- ***Alex Johnson***, AI Systems Architect  

Let’s get started.

---

## Segment 1: The Overlooked Risk  
**Host:** Elena, give us the lay of the land. What gap in LLM fine-tuning does this paper illuminate?

**Dr. Elena Garcia (Safety Alignment):**  
Thanks, Riley. For years, folks have tackled catastrophic forgetting by freezing layers or replaying old data—basically ensuring the model doesn’t unlearn specific skills or facts. Yet almost nobody checked whether we also erode the safety safeguards we originally baked in. One critical safeguard: the model’s calibrated uncertainty—or its willingness to say, “I don’t know.” When that fades, you get overconfident hallucinations.  

**Prof. James Liu (Theory):**  
Exactly. It’s an alignment blindspot. The standard view treats knowledge entanglement as purely “task performance vs. factual recall.” But here, we see a third axis: safety alignment itself. If fine-tuning drifts too far, we lose that honest self-reporting.

---

## Segment 2: Diagnosing the Drift  
**Host:** Maria, how dramatic is this “ignorance drift” in practice?

**Dr. Maria Nguyen (Applied NLP):**  
Quite dramatic. In controlled experiments, models fine-tuned conventionally on domain-specific data would attempt answers even when prompts asked about completely unseen entities. Their calibration curves collapse. You might get a confident but bogus biography of a fictional person. That’s dangerous, especially in high-stakes applications.

**Alex Johnson (Systems Architect):**  
From a systems perspective, the ripple effect is huge. Once downstream apps trust those bad confidences, you get bad decisions—legal, medical, you name it. The paper quantifies this: a 30% drop in “I don’t know” responses after just a few epochs of vanilla fine-tuning.


"""

filename = "alignML"

ssml_text = """- **Dr. Elena Garcia**, a Safety Alignment Specialist  
- **Prof. James Liu**, Theoretical ML Researcher  
- **Dr. Maria Nguyen**, Applied NLP Engineer  
- **Alex Johnson**, AI Systems Architect  """