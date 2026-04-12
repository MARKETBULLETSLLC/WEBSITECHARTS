"""
MarketBullets — Auto Commit Watcher
Watches WEBSITECHARTS/ for new or updated PNG files exported from Trade Navigator.
Commits each changed chart automatically. Does NOT push — Gary pushes manually.

Usage:
    python tools/auto_commit_watcher.py

To run at Windows startup, use the included auto_commit_watcher.bat via Task Scheduler.
"""

import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = Path(r"c:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS")
LOG_FILE = WATCH_DIR / "tools" / "auto_commit.log"

# Prevents duplicate commits if watchdog fires multiple events for one file save
COOLDOWN_SECONDS = 15

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Track last commit time per filename
last_committed: dict[str, float] = {}


def git_commit(filepath: Path) -> None:
    filename = filepath.name
    now = time.time()

    # Skip if we just committed this file (duplicate event guard)
    if filename in last_committed and (now - last_committed[filename]) < COOLDOWN_SECONDS:
        return

    # Brief pause — ensures Trade Navigator has finished writing the file
    time.sleep(3)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        # Stage the file
        add = subprocess.run(
            ["git", "add", filename],
            cwd=WATCH_DIR,
            capture_output=True,
            text=True
        )
        if add.returncode != 0:
            logging.error(f"git add failed — {filename}: {add.stderr.strip()}")
            return

        # Check if anything is actually staged (file may be identical to last commit)
        status = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=WATCH_DIR,
            capture_output=True,
            text=True
        )
        if not status.stdout.strip():
            logging.info(f"Skipped (no change detected): {filename}")
            return

        # Commit
        commit_msg = f"Auto-commit: {filename} [{timestamp}]"
        commit = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=WATCH_DIR,
            capture_output=True,
            text=True
        )
        if commit.returncode == 0:
            last_committed[filename] = now
            logging.info(f"Committed: {filename}")
        else:
            logging.error(f"git commit failed — {filename}: {commit.stderr.strip()}")

    except Exception as e:
        logging.error(f"Unexpected error processing {filename}: {e}")


class PNGHandler(FileSystemEventHandler):
    """Handles file system events for PNG files in the root of WATCH_DIR only."""

    def _is_root_png(self, path: str) -> bool:
        p = Path(path)
        return (
            not p.is_dir()
            and p.suffix.lower() == ".png"
            and p.parent.resolve() == WATCH_DIR.resolve()
        )

    def on_created(self, event):
        if self._is_root_png(event.src_path):
            logging.info(f"New chart detected: {Path(event.src_path).name}")
            git_commit(Path(event.src_path))

    def on_modified(self, event):
        if self._is_root_png(event.src_path):
            logging.info(f"Updated chart detected: {Path(event.src_path).name}")
            git_commit(Path(event.src_path))


if __name__ == "__main__":
    logging.info("=" * 55)
    logging.info("MarketBullets Auto-Commit Watcher started")
    logging.info(f"Watching: {WATCH_DIR}")
    logging.info("Commits automatically. YOU push manually.")
    logging.info("=" * 55)

    observer = Observer()
    observer.schedule(PNGHandler(), str(WATCH_DIR), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Auto-Commit Watcher stopped.")

    observer.join()
