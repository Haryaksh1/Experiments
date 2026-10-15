from assistant import parse, parse_steps

CASES = {
    " Search for cats and dogs.": ("search", "cats and dogs"),
    "search R&D jobs": ("search", "R&D jobs"),
    "Open YouTube.": ("open", "https://youtube.com"),
    "go to google dot co dot in": ("open", "https://google.co.in"),
    "Open stack overflow": ("open", "https://stackoverflow.com"),
    "Open the first result.": ("result", 1),
    "open second result": ("result", 2),
    "Open result number 3": ("result", 3),
    "click the 4th link": ("result", 4),
    "Open a new tab": ("new_tab", None),
    "close tab": ("close_tab", None),
    "Click on Sign in.": ("click", "Sign in"),
    "Scroll down.": ("scroll", "down"),
    "scroll up": ("scroll", "up"),
    "Go back.": ("back", None),
    "go forward": ("forward", None),
    "Refresh": ("refresh", None),
    "Type Hello World.": ("type", "Hello World"),
    "type search for cats": ("type", "search for cats"),
    "Press enter.": ("enter", None),
    "Thank you.": (None, None),
    # natural speech
    "Open browser and search for cats.": ("search", "cats"),
    "Can you search for cats please": ("search", "cats please"),
    "search for type 2 diabetes": ("search", "type 2 diabetes"),
    "Please open YouTube.": ("open", "https://youtube.com"),
    "Open the browser.": ("open", "https://duckduckgo.com"),
    "Open the best pizza place near me": ("search", "best pizza place near me"),
    "Okay, scroll down a bit.": ("scroll", "down"),
    "Can you go back?": ("back", None),
    "Open second webpage.": ("result", 2),
    "Open the third web page": ("result", 3),
    "open the first one": ("result", 1),
    "Close browser.": ("close_browser", None),
    "Close the browser.": ("close_browser", None),
    "Close the tab.": ("close_tab", None),
    "show me entertainment news": (None, None),
}

for text, expected in CASES.items():
    assert parse(text) == expected, f"{text!r}: got {parse(text)}, want {expected}"
print(f"all {len(CASES)} parse cases pass")

# compound "new tab" commands (cases from a real session log)
STEPS = {
    "Open a new tab.": [("new_tab", None)],
    "Open new tab and search white sky.": [("new_tab", None), ("search", "white sky")],
    "open youtube in a new tab": [("new_tab", None), ("open", "https://youtube.com")],
    "Open browser and search botan.": [("search", "botan")],
    "Use browser": [],
}
for text, expected in STEPS.items():
    assert parse_steps(text) == expected, f"{text!r}: got {parse_steps(text)}, want {expected}"
print(f"all {len(STEPS)} step cases pass")
