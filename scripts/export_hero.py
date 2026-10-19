from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent.parent
out = root / "marketbullets_hero_adjusted.png"
url = (root / "marketbullets_nnm.html").as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=2)
    page.goto(url, wait_until="networkidle")
    page.locator("#hero").screenshot(path=str(out), animations="disabled")
    browser.close()

print(f"CREATED: {out}")
print(f"EXISTS: {out.exists()}")
print(f"SIZE: {out.stat().st_size if out.exists() else 0}")
