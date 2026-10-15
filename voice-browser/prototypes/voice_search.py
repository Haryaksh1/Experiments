import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import re
from playwright.sync_api import sync_playwright

# Load Whisper once
model = whisper.load_model("tiny")

# Record audio
fs = 16000
seconds = 5

print("Speak now...")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
sd.wait()

write("temp.wav", fs, audio)

# Transcribe
result = model.transcribe("temp.wav", fp16=False)
text = result["text"].lower().strip()

print("Heard:", text)

# Parse command
match = re.search(r"search (?:for )?(.+)", text)

if match:
    query = match.group(1)

    print("Searching for:", query)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        page.goto(
            f"https://duckduckgo.com/?q={query}",
            wait_until="domcontentloaded",
            timeout=60000
        )

        input("Press Enter to close...")

        browser.close()

else:
    print("No search command detected.")