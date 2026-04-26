"""
chart_watcher.py — MarketBullets wheat chart auto-push pipeline

Monitors the repo root for new JPG exports from Trade Navigator,
renames them to fixed canonical names, and git push to GitHub.
Squarespace embeds update automatically via permanent raw.githubusercontent.com URLs.

BEFORE FIRST RUN: verify CHART_MAP keys match Trade Navigator export filenames.
"""

import os
import sys
import time
import shutil
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ── Config ────────────────────────────────────────────────────────────────────
WATCH_FOLDER = Path(r"C:\users\hofer\onedrive\documents\github\websitecharts")
REPO_ROOT    = WATCH_FOLDER
CHARTS_DIR   = REPO_ROOT / "charts"
GITHUB_RAW   = "https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts"

# Keys = substring to match in Trade Navigator filename (case-insensitive)
# Values = canonical filename in charts/
CHART_MAP = {
    "winter":    "wheat-winter-belt.jpg",
    "spring":    "wheat-spring-belt.jpg",
    "pacific":   "wheat-pacific-nw.jpg",
    "ukraine":   "wheat-ukraine.jpg",
    "russia":    "wheat-russia.jpg",
    "canada":    "wheat-canada.jpg",
    "argentina": "wheat-argentina.jpg",
    "australia": "wheat-australia.jpg",
}

EXTENSIONS = {".jpg", ".jpeg"}
SETTLE_DELAY = 2  # seconds to wait after detection before processing

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def match_canonical(filename: str) -> str | None:
    """Return the canonical chart name if filename matches a CHART_MAP key."""
    lower = filename.lower()
    for keyword, canonical in CHART_MAP.items():
        if keyword in lower:
            return canonical
    return None


def git_push(canonical: Path) -> bool:
    """Stage, commit, and push one file. Returns True on success."""
    rel = canonical.relative_to(REPO_ROOT)
    cmds = [
        ["git", "-C", str(REPO_ROOT), "add", str(rel)],
        ["git", "-C", str(REPO_ROOT), "commit", "-m", f"update {canonical.name}"],
        ["git", "-C", str(REPO_ROOT), "push", "origin", "main"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.error("Command failed: %s\n%s", " ".join(cmd), result.stderr.strip())
            return False
    return True


def process_file(src: Path) -> None:
    canonical_name = match_canonical(src.name)
    if canonical_name is None:
        log.warning("No CHART_MAP match for '%s' — skipping. Check CHART_MAP keys.", src.name)
        return

    dest = CHARTS_DIR / canonical_name
    shutil.copy2(src, dest)
    log.info("Copied  %s  →  charts/%s", src.name, canonical_name)

    if git_push(dest):
        log.info("Pushed  →  %s/%s", GITHUB_RAW, canonical_name)
    else:
        log.error("Push failed for %s", canonical_name)


# ── Watchdog handler ──────────────────────────────────────────────────────────
class ChartHandler(FileSystemEventHandler):
    def __init__(self):
        self._seen: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in EXTENSIONS:
            return
        # Skip files already inside charts/
        if CHARTS_DIR in path.parents:
            return
        if str(path) in self._seen:
            return
        self._seen.add(str(path))

        log.info("Detected  %s — waiting %ds for write to complete…", path.name, SETTLE_DELAY)
        time.sleep(SETTLE_DELAY)

        if not path.exists():
            log.warning("File disappeared before processing: %s", path.name)
            return

        process_file(path)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    if not CHARTS_DIR.exists():
        log.error("charts/ directory not found at %s", CHARTS_DIR)
        sys.exit(1)

    log.info("MarketBullets chart watcher started.")
    log.info("Watching: %s", WATCH_FOLDER)
    log.info("Chart map: %d entries", len(CHART_MAP))
    log.info("Press Ctrl+C to stop.\n")

    handler  = ChartHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_FOLDER), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutting down…")
        observer.stop()

    observer.join()
    log.info("Watcher stopped.")


if __name__ == "__main__":
    main()
