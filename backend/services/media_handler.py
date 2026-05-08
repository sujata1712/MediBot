# Voice & Image input handler for MediBot

import os
import sys
import base64
import tempfile
import sounddevice as sd
import scipy.io.wavfile as wav
from groq import Groq
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import VISION_MODEL, VOICE_MODEL
from prompts import VISION_PROMPT

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --------------------------------------------- Voice Recording ---------------------------------------------

def record_audio_from_mic(duration: int = 5) -> bytes:
    """Record from the default microphone and return raw WAV bytes."""

    SAMPLE_RATE = 16000
    duration = max(1, min(duration, 60))    # clamp 1–60s

    print(f"\n  Recording for {duration} seconds... speak now!")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    print(" Done recording.\n")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    wav.write(tmp_path, SAMPLE_RATE, audio)
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    os.remove(tmp_path)
    return audio_bytes


# --------------------------------------------- Voice Handler — Speech-to-text ---------------------------------------------

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Convert audio bytes → text using Groq Whisper."""
    transcription = client.audio.transcriptions.create(
        model = VOICE_MODEL,
        file = (filename, audio_bytes),
        language="en",
        response_format = "text",
    )
    return transcription.strip()


# --------------------------------------------- Image Handler — Vision-to-text ---------------------------------------------

def analyze_image(image_bytes: bytes, user_query: str = "") -> str:
    """Analyze a medical image and return a text description of visible symptoms or conditions."""

    # Encode image bytes to base64 for transmission
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    # Call the Groq API to analyze the image
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": VISION_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                {"type": "text",      "text": user_query or "Describe this medical image."},
            ]},
        ],
        max_tokens=512,
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()