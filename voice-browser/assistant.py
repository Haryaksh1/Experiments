"""VoiceBrowser, control a Chromium browser with your voice.

F8  = toggle listening on/off
ESC = quit
"""
import re
import time
from urllib.parse import quote_plus

WHISPER_MODEL = "base"      # tiny = faster, small = more accurate
SAMPLE_RATE = 16000
RECORD_SECONDS = 5
SILENCE_THRESHOLD = 0.02    # raise if background noise triggers commands, lower if quiet speech is skipped
SCROLL_PIXELS = 800
# Nudges Whisper toward command words ("Open Your" -> "Open YouTube").
WHISPER_HINT = ("Voice commands for a web browser. Search for, open YouTube, open Google, new tab, "
                "close tab, close browser, open the first result, second result, scroll down, "
                "scroll up, go back, go forward, refresh.")

ORDINALS = {
    "first": 1, "one": 1, "second": 2, "two": 2, "third": 3, "three": 3,
    "fourth": 4, "four": 4, "fifth": 5, "five": 5, "sixth": 6, "six": 6,
    "seventh": 7, "seven": 7, "eighth": 8, "eight": 8, "ninth": 9, "nine": 9,
    "tenth": 10, "ten": 10,
}
NUM = r"(\d+|" + "|".join(ORDINALS) + r")(?:st|nd|rd|th)?"
PAGE_WORD = r"(?:result|link|web ?page|page|web ?site|site|one)\b"

# Commands can appear anywhere in the sentence ("open browser and search for cats").
# Order matters: first match wins, so search beats open.
COMMANDS = [
    ("type",       r"^type (.+)"),
    ("search",     r"\bsearch (?:for )?(.+)"),
    ("result",     rf"\b(?:open|click) (?:the )?{NUM} {PAGE_WORD}"),
    ("result",     rf"\b(?:open|click) (?:the )?{PAGE_WORD} (?:number )?{NUM}"),
    ("new_tab",    r"\bnew tab\b"),
    ("close_browser", r"\bclose (?:the )?(?:browser|chrome|window)\b"),
    ("close_tab",  r"\bclose (?:the |this )?tab\b"),
    ("open",       r"\b(?:open|go to) (?:the )?(.+)"),
    ("click",      r"\bclick (?:on )?(.+)"),
    ("scroll",     r"\bscroll (down|up)\b"),
    ("back",       r"\bback\b"),
    ("forward",    r"\bforward\b"),
    ("refresh",    r"\b(?:refresh|reload)\b"),
    ("enter",      r"\bpress enter\b|^enter$"),
]
NEW_TAB = r"\b(?:in |and )?(?:open )?(?:a )?new tab\b"
BROWSER_WORDS = {"browser", "chrome", "google chrome", "chromium", "web browser"}


def parse(text):
    """Turn a transcript into (action, argument), or (None, None)."""
    text = text.strip().strip(" .,!?")
    for action, pattern in COMMANDS:
        m = re.search(pattern, text, re.I)
        if not m:
            continue
        arg = m.group(1).strip(" .,!?") if m.groups() else None
        if action == "result":
            arg = int(arg) if arg.isdigit() else ORDINALS[arg.lower()]
        elif action == "open":
            if arg.lower() in BROWSER_WORDS:
                return "open", "https://duckduckgo.com"
            if len(arg.lower().replace(" dot ", ".").split()) > 3:  # a sentence, not a site name, so search it instead
                return "search", arg
            arg = to_url(arg)
        elif action == "scroll":
            arg = arg.lower()
        return action, arg
    return None, None


def parse_steps(text):
    """Like parse, but "new tab and search cats" / "open youtube in a new tab" -> [new_tab, <command>]."""
    if not re.search(NEW_TAB, text, re.I):
        action, arg = parse(text)
        return [(action, arg)] if action else []
    action, arg = parse(re.sub(NEW_TAB, " ", text, flags=re.I))
    return [("new_tab", None)] + ([(action, arg)] if action else [])


def to_url(spoken):
    """'YouTube' -> https://youtube.com, 'google dot co dot in' -> https://google.co.in"""
    site = spoken.lower().replace(" dot ", ".").replace(" ", "")
    if site.startswith("http"):
        return site
    if "." not in site:
        site += ".com"
    return "https://" + site


class Browser:
    def __init__(self, playwright):
        self.pw = playwright
        self.browser = None
        self.context = None
        self.page = None

    def ensure(self):
        """Launch (or relaunch if the user closed it) and return the active page."""
        if self.browser is None or not self.browser.is_connected():
            self.browser = self.pw.chromium.launch(headless=False)
            self.context = self.browser.new_context(no_viewport=True)
            self.page = None
        if self.page is None or self.page.is_closed():
            open_pages = [p for p in self.context.pages if not p.is_closed()]
            self.page = open_pages[-1] if open_pages else self.context.new_page()
        self.page.bring_to_front()
        return self.page

    def has_page(self):
        return (self.browser is not None and self.browser.is_connected()
                and any(not p.is_closed() for p in self.context.pages))

    def run(self, action, arg):
        nav_actions = {"search", "open", "new_tab"}
        if action not in nav_actions and not self.has_page():
            print("No page open. Say 'open <site>' or 'search <something>' first.")
            return
        page = self.ensure()

        if action == "search":
            page.goto(f"https://duckduckgo.com/?q={quote_plus(arg)}", wait_until="domcontentloaded")
            print(f"Searching: {arg}")
        elif action == "open":
            try:
                page.goto(arg, wait_until="domcontentloaded", timeout=15000)
                print(f"Opened {arg}")
            except Exception:
                query = re.sub(r"^https?://|\.com$", "", arg)
                print(f"Couldn't open {arg}, searching '{query}' instead")
                self.run("search", query)
        elif action == "result":
            # DuckDuckGo-specific selector, breaks if DDG changes its markup
            links = page.locator('[data-testid="result-title-a"]')
            try:
                links.first.wait_for(timeout=5000)  # results render after page load
            except Exception:
                pass
            if links.count() < arg:
                print(f"Only {links.count()} results on this page.")
                return
            links.nth(arg - 1).click()
            print(f"Opened result {arg}")
        elif action == "click":
            target = page.get_by_role("link", name=re.compile(re.escape(arg), re.I))
            if target.count() == 0:
                target = page.get_by_text(arg, exact=False)
            if target.count() == 0:
                print(f"Nothing on the page matches '{arg}'.")
                return
            target.first.click()
            print(f"Clicked '{arg}'")
        elif action == "scroll":
            page.mouse.wheel(0, SCROLL_PIXELS if arg == "down" else -SCROLL_PIXELS)
            print(f"Scrolled {arg}")
        elif action == "back":
            page.go_back()
            print("Went back")
        elif action == "forward":
            page.go_forward()
            print("Went forward")
        elif action == "refresh":
            page.reload()
            print("Refreshed")
        elif action == "new_tab":
            self.page = self.context.new_page()
            print("Opened new tab")
        elif action == "close_tab":
            page.close()
            self.page = None
            print("Closed tab")
        elif action == "close_browser":
            self.close()
            print("Closed browser")
        elif action == "type":
            page.keyboard.type(arg)
            print(f"Typed: {arg}")
        elif action == "enter":
            page.keyboard.press("Enter")
            print("Pressed Enter")

    def close(self):
        if self.browser and self.browser.is_connected():
            self.browser.close()


def beep():
    try:
        import winsound
        winsound.Beep(1000, 150)
    except Exception:
        print("\a", end="", flush=True)


def main():
    import keyboard
    import numpy as np
    import sounddevice as sd
    import whisper
    from playwright.sync_api import sync_playwright

    state = {"on": False, "quit": False}

    def toggle():
        state["on"] = not state["on"]
        print("\nAssistant ON" if state["on"] else "\nAssistant OFF")

    keyboard.add_hotkey("f8", toggle)
    keyboard.add_hotkey("esc", lambda: state.update(quit=True))

    print(f"Loading Whisper ({WHISPER_MODEL})...")
    model = whisper.load_model(WHISPER_MODEL)
    print("Ready.  F8 = toggle listening, ESC = quit")

    def listen():
        """Record one clip. Returns None if interrupted by F8/ESC or the clip is silent."""
        beep()
        print("\nListening...")
        audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        while sd.get_stream().active:
            if state["quit"] or not state["on"]:
                sd.stop()
                return None
            time.sleep(0.05)
        audio = audio.flatten()
        if np.abs(audio).max() < SILENCE_THRESHOLD:
            return None  # Whisper hallucinates "Thank you." on silence
        return audio

    pw = sync_playwright().start()
    browser = Browser(pw)
    try:
        while not state["quit"]:
            if not state["on"]:
                time.sleep(0.1)
                continue
            audio = listen()
            if audio is None:
                continue
            text = model.transcribe(audio, fp16=False, language="en", initial_prompt=WHISPER_HINT)["text"].strip()
            if not text:
                continue
            print("Heard:", text)
            steps = parse_steps(text)
            if not steps:
                print("No command matched.")
                continue
            try:
                for action, arg in steps:
                    browser.run(action, arg)
            except Exception as e:
                print("Command error:", e)
    finally:
        browser.close()
        pw.stop()
        print("Exiting...")


if __name__ == "__main__":
    main()
