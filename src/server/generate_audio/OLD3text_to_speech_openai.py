import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import generate, play
from elevenlabs import voices as list_voices
import sqlite3
from pathlib import Path
import re
from pydub import AudioSegment

load_dotenv()


# Initialize ElevenLabs client
elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Ensure directories exist
audio_dir = Path('src/client/static/audio')
tmp_dir = Path('tmp')
audio_dir.mkdir(parents=True, exist_ok=True)
tmp_dir.mkdir(exist_ok=True)



# 3. Define voices + descriptions
VOICE_CONFIG = {
    "Riley Thompson": {
        "voice_id":     "voice_id_host",
        "description":  "Warm, clear, and engaging host tone"
    },
    "Dr. Elena Garcia": {
        "voice_id":     "voice_id_elena",
        "description":  "Measured, thoughtful, with a calm authority"
    },
    "Prof. James Liu": {
        "voice_id":     "voice_id_james",
        "description":  "Analytical, precise, slight academic cadence"
    },
    "Dr. Maria Nguyen": {
        "voice_id":     "voice_id_maria",
        "description":  "Energetic, confident, tech-savvy engineer vibe"
    },
    "Alex Johnson": {
        "voice_id":     "voice_id_alex",
        "description":  "Grounded, conversational, systems-architect style"
    },
}

print("🔊 Voice descriptions:")
for name, cfg in VOICE_CONFIG.items():
    print(f"  • {name}: {cfg['description']} (ID: {cfg['voice_id']})")
print()

# 4. Define segments (replace with your full transcript)
SEGMENTS = [
    {
        "speaker": "Riley Thompson",
        "text": "Elena, give us the lay of the land. What gap in LLM fine-tuning does this paper illuminate?"
    },
    {
        "speaker": "Dr. Elena Garcia",
        "text": "Thanks, Riley. For years, folks have tackled catastrophic forgetting by freezing layers or replaying old data—basically ensuring the model doesn’t unlearn specific skills or facts."
    },
    {
        "speaker": "Prof. James Liu",
        "text": "Exactly. It’s an alignment blindspot. The standard view treats knowledge entanglement as purely “task performance vs. factual recall.” "
    },
    
]

# 5. Generate and combine audio
combined = AudioSegment.empty()

for idx, seg in enumerate(SEGMENTS):
    speaker = seg["speaker"]
    text = seg["text"]
    cfg = VOICE_CONFIG.get(speaker)
    if not cfg:
        raise KeyError(f"No voice config found for: {speaker}")

    print(f"🛠️ Generating audio for {speaker}...")
    audio_bytes = elevenlabs.generate(
        text=text,
        voice=cfg["voice_id"],
        model="eleven_monolingual_v1"
    )

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    combined += audio + AudioSegment.silent(duration=500)
    
    play(audio)

# 6. Save to file
output_path = "alignml_seat_episode.mp3"
combined.export(output_path, format="mp3")
print(f"✅ Podcast saved as {output_path}")

