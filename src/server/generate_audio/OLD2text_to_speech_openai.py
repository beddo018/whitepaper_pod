#!/usr/bin/env python3
# elevenlabs_podcast_tts.py
# Requires: pip install elevenlabs pydub
# Make sure `ffmpeg` is installed and in your PATH (Linux: sudo apt install ffmpeg)

import os
import io
from elevenlabs.client import set_api_key, generate, voices as list_voices
from pydub import AudioSegment

# 1. Set your ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise RuntimeError("❌ Please set the ELEVENLABS_API_KEY environment variable before running this script.")
set_api_key(ELEVENLABS_API_KEY)

# 2. List voices (optional)
print("🎙️ Available voices:")
for v in list_voices():
    print(f"  • {v.name}  (ID: {v.voice_id})")
print()

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
        "text": "Welcome to AlignML, the podcast where..."
    },
    # Add more segments from your transcript
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
    audio_bytes = generate(
        text=text,
        voice=cfg["voice_id"],
        model="eleven_monolingual_v1"
    )

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    combined += audio + AudioSegment.silent(duration=500)

# 6. Save to file
output_path = "alignml_seat_episode.mp3"
combined.export(output_path, format="mp3")
print(f"✅ Podcast saved as {output_path}")
