from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
import subprocess

ffplay_path = r"C:\ffmpeg\bin\ffplay.exe"

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=api_key)

audio = elevenlabs.text_to_speech.convert(
    text="The first move is what sets everything in motion.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # "George" - browse voices at elevenlabs.io/app/voice-library
    model_id="eleven_v4",
    output_format="mp3_44100_128",
)
# Start FFplay
process = subprocess.Popen(
    [
        ffplay_path,
        "-nodisp",
        "-autoexit",
        "-loglevel", "error",
        "-f", "mp3",
        "-i", "pipe:0"
    ],
    stdin=subprocess.PIPE
)

# Stream audio into FFplay
try:
    for chunk in audio:
        if chunk:
            process.stdin.write(chunk)

    process.stdin.close()
    process.wait()

except Exception:
    process.kill()
    raise

print("Audio playback finished!")
