import keyboard
import time
import re
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
from playwright.sync_api import sync_playwright

assistant_on = False

print("Loading Whisper...")
model = whisper.load_model("base")
print("Whisper loaded.")

p = sync_playwright().start()

browser = None
page = None


def ensure_browser():
    global browser, page

    if browser is None:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()


def execute_command(text):
    global page

    text = text.lower().strip()

    # OPEN YOUTUBE
    if "open youtube" in text:
        ensure_browser()
        page.goto("https://youtube.com")
        print("Opened YouTube")
        return

    # SEARCH
    match = re.search(r"search (?:for )?(.+)", text)

    if match:
        query = match.group(1).strip(" .,!?")

        ensure_browser()

        page.goto(
            f"https://duckduckgo.com/?q={query}",
            wait_until="domcontentloaded",
            timeout=60000
        )

        print(f"Searching: {query}")
        return

    # OPEN FIRST RESULT
    if "open first result" in text:

        if page:
            try:
                page.locator("a[href]").nth(0).click()
                print("Opened first result")
            except Exception as e:
                print("Could not open first result:", e)

        return

    # OPEN SECOND RESULT
    if "open second result" in text:

        if page:
            try:
                page.locator("a[href]").nth(1).click()
                print("Opened second result")
            except Exception as e:
                print("Could not open second result:", e)

        return

    # SCROLL DOWN
    if "scroll down" in text:
        if page:
            page.mouse.wheel(0, 1000)
            print("Scrolled down")
        return

    # SCROLL UP
    if "scroll up" in text:
        if page:
            page.mouse.wheel(0, -1000)
            print("Scrolled up")
        return

    # GO BACK
    if "go back" in text:
        if page:
            page.go_back()
            print("Went back")
        return

    # GO FORWARD
    if "go forward" in text:
        if page:
            page.go_forward()
            print("Went forward")
        return

    # TYPE
    match = re.search(r"type (.+)", text)

    if match:
        content = match.group(1)

        if page:
            page.keyboard.type(content)
            print(f"Typed: {content}")

        return

    # PRESS ENTER
    if "press enter" in text:

        if page:
            page.keyboard.press("Enter")
            print("Pressed Enter")

        return

    print("No command matched.")


def toggle():
    global assistant_on

    assistant_on = not assistant_on

    if assistant_on:
        print("\nAssistant ON")
    else:
        print("\nAssistant OFF")


keyboard.add_hotkey("f8", toggle)

print("F8 = Toggle Assistant")
print("ESC = Quit")

try:

    while True:

        if keyboard.is_pressed("esc"):
            break

        if assistant_on:

            print("\nSpeak after the beep...")
            time.sleep(1)
            print("BEEP")

            fs = 16000
            seconds = 6

            audio = sd.rec(
                int(seconds * fs),
                samplerate=fs,
                channels=1
            )

            sd.wait()

            write("temp.wav", fs, audio)

            result = model.transcribe(
                "temp.wav",
                fp16=False
            )

            text = result["text"].strip()

            if text:

                print("Heard:", text)

                try:
                    execute_command(text)

                except Exception as e:
                    print("Command Error:", e)

        else:
            time.sleep(0.1)

finally:

    if browser:
        browser.close()

    p.stop()

    print("Exiting...")