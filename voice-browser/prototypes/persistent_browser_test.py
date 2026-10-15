from playwright.sync_api import sync_playwright

p = sync_playwright().start()

browser = p.chromium.launch(headless=False)
page = browser.new_page()

print("Browser started")
print("Type a URL or 'quit'")

while True:
    cmd = input("> ")

    if cmd == "quit":
        break

    page.goto(cmd)

browser.close()
p.stop()