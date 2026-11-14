## Loading Libraries

# Generating and playing audio.
from elevenlabs.client import ElevenLabs
import subprocess

# Getting from the environment. 
from dotenv import load_dotenv
import os

##


## Load the API key from the environment and initialise ElevenLabs.

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=api_key)

##


## Functions for calling their API.

def TextToSpeech(text, voiceId="JBFqnCBsd6RMkjVDRZzb", modelId="eleven_v4", outputFormat="mp3_44100_128"):
    return elevenlabs.text_to_speech.convert(text=text, voice_id=voiceId, model_id= modelId, output_format=outputFormat)


def MusicFromPrompt(prompt, musicLength_ms, modelId="music_v2_5"):
    return elevenlabs.music.compose(prompt=prompt, music_length_ms=musicLength_ms, model_id=modelId)

##


## Function for playing audio.

def PlayAudio(audioFile, fileFormat="mp3", ffplayFilePath=r"C:\ffmpeg\bin\ffplay.exe"):
    process = subprocess.Popen(
        [ffplayFilePath, "-nodisp", "-autoexit", "-loglevel", "error", "-f", fileFormat, "-i", "pipe:0"],
        stdin=subprocess.PIPE
    )

    try:
        for chunk in audioFile:
            if chunk:
                process.stdin.write(chunk)
        process.stdin.close()
        process.wait()
    except Exception:
        process.kill()
        raise

##


## Main Test Area

music = MusicFromPrompt("Upbeat music", 5_000)
PlayAudio(music)