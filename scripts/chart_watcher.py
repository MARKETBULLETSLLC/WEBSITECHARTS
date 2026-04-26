"""
chart_watcher.py
────────────────
Watches your OneDrive folder for new JPG files exported from
Trade Navigator, renames them to fixed canonical names, commits
to GitHub repo MARKETBULLETSLLC/WEBSITECHARTS, and pushes.
Squarespace embeds via raw.githubusercontent.com — URL never
changes, site always shows the latest chart automatically.

Run: python scripts/chart_watcher.py
Stop: Ctrl+C
"""

import sys
import time
import shutil
import subprocess
from pathlib import Path
from datetime import date
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─── CONFIG ─────────────────────────────────────────────────────────────────

# Where Trade Navigator saves exported JPGs (your OneDrive path)
WATCH_FOLDER = Path(r"C:\users\hofer\onedrive\documents\github\websitecharts")

# Root of your local git clone (same folder — it IS the repo)
REPO_ROOT = Path(r"C:\users\hofer\onedrive\documents\github\websitecharts")

# Subfolder inside repo where chart images are stored
CHARTS_DIR = REPO_ROOT / "charts"

# Keyword matching: substring in Trade Navigator filename → fixed GitHub name
# Edit the LEFT side (keys) to match what Trade Navigator actually names files.
# Leave the RIGHT side (values) as-is — these become the GitHub filenames.
CHART_MAP = {
    "winter":    "wheat-winter-belt",
    "spring":    "wheat-spring-belt",
    "pacific":   "wheat-pacific-nw",
    "ukraine":   "wheat-ukraine",
    "russia":    "wheat-russia",
    "canada":    "wheat-canada",
    "argentina": "wheat-argentina",
    "australia": "wheat-australia",
}

# Used if no keyword matches the source filename
FALLBACK_NAME = "wheat-chart"

# GitHub raw base URL (displayed after each successful push)
GITHUB_RAW = "https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts"

# ─── END CONFIG ─────────────────────────────────────────────────────────────


def resolve_chart_name(source_path: Path) -> str:
    stem = source_path.stem.lower()
    for keyword, name in CHART_MAP.items():
        if keyword in stem:
            return name
    return FALLBACK_NAME


def git(cmd: list, cwd: Path):
    result = subprocess.run(
        ["git"] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(cmd)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def process_file(src: Path):
    today = date.today().strftime("%Y-%m-%d")
    base = resolve_chart_name(src)
    fixed_name = f"{base}.jpg"
    dest = CHARTS_DIR / fixed_name

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, dest)
    print(f" ✓ Copied → charts/{fixed_name}")

    git(["add", str(dest)], REPO_ROOT)

    commit_msg = f"chart update: {base} [{today}]"
    git(["commit", "-m", commit_msg], REPO_ROOT)
    print(f" ✓ Committed: {commit_msg}")

    git(["push", "origin", "main"], REPO_ROOT)
    print(f" ✓ Pushed to GitHub")
    print(f"\n 🌐 Live URL:\n {GITHUB_RAW}/{fixed_name}\n")


class JPGHandler(FileSystemEventHandler):

    def __init__(self):
        self._seen = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in {".jpg", ".jpeg"}:
            return
        if "charts" in path.parts:
            return  # skip files already in charts/ subfolder
        if path in self._seen:
            return
        self._seen.add(path)

        time.sleep(2)  # wait for Trade Navigator to finish writing

        print(f"\n[{time.strftime('%H:%M:%S')}] Detected: {path.name}")
        try:
            process_file(path)
        except Exception as exc:
            print(f" ✗ ERROR: {exc}")
            print(" Check git auth and repo status, then retry.\n")


def main():
    print("━" * 60)
    print(" Wheat Chart Watcher")
    print(f" Watching : {WATCH_FOLDER}")
    print(f" GitHub   : MARKETBULLETSLLC/WEBSITECHARTS")
    print(" Ctrl+C to stop")
    print("━" * 60)

    if not WATCH_FOLDER.exists():
        print(f"\nERROR: Watch folder not found:\n {WATCH_FOLDER}")
        sys.exit(1)

    if not (REPO_ROOT / ".git").exists():
        print(f"\nERROR: No git repo found at:\n {REPO_ROOT}")
        print("Run: git remote add origin "
              "https://github.com/MARKETBULLETSLLC/WEBSITECHARTS.git")
        sys.exit(1)

    print("\nWaiting for new JPG exports...\n")

    handler = JPGHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_FOLDER), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("\nWatcher stopped.")


if __name__ == "__main__":
    main()
