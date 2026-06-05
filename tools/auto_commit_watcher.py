"""
MarketBullets — Auto Commit Watcher
Polls charts/ every 10 seconds for new or updated PNG files exported from Trade Navigator.
Commits and pushes each changed chart automatically. No third-party libraries required.

Usage:
    python tools/auto_commit_watcher.py

To run at Windows startup, use the included auto_commit_watcher.bat via Task Scheduler.
"""

import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(r"c:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS")
WATCH_DIR = REPO_ROOT / "charts"
LOG_FILE = REPO_ROOT / "tools" / "auto_commit.log"

POLL_SECONDS = 10
COOLDOWN_SECONDS = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


def git(cmd: list, cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def commit_and_push(filepath: Path) -> None:
    filename = filepath.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    rc, _, err = git(["git", "add", f"charts/{filename}"], REPO_ROOT)
    if rc != 0:
        logging.error(f"git add failed — {filename}: {err}")
        return

    rc, staged, _ = git(["git", "diff", "--cached", "--name-only"], REPO_ROOT)
    if not staged:
        logging.info(f"Skipped (no change): {filename}")
        return

    rc, _, err = git(["git", "commit", "-m", f"Auto-commit: {filename} [{timestamp}]"], REPO_ROOT)
    if rc != 0:
        logging.error(f"git commit failed — {filename}: {err}")
        return
    logging.info(f"Committed: {filename}")

    rc, _, err = git(["git", "push", "origin", "main"], REPO_ROOT)
    if rc == 0:
        logging.info(f"Pushed: {filename}")
    else:
        logging.error(f"git push failed — {filename}: {err}")


def snapshot(directory: Path) -> dict[str, float]:
    return {
        p.name: p.stat().st_mtime
        for p in directory.glob("*.png")
        if p.is_file()
    }


if __name__ == "__main__":
    logging.info("=" * 55)
    logging.info("MarketBullets Auto-Commit Watcher started")
    logging.info(f"Watching: {WATCH_DIR}")
    logging.info(f"Poll interval: {POLL_SECONDS}s  |  Commit cooldown: {COOLDOWN_SECONDS}s")
    logging.info("Commits AND pushes automatically.")
    logging.info("=" * 55)

    known: dict[str, float] = snapshot(WATCH_DIR)
    last_committed: dict[str, float] = {}

    try:
        while True:
            time.sleep(POLL_SECONDS)
            current = snapshot(WATCH_DIR)

            for name, mtime in current.items():
                prev_mtime = known.get(name, 0)
                last_commit_time = last_committed.get(name, 0)
                if mtime != prev_mtime and (time.time() - last_commit_time) >= COOLDOWN_SECONDS:
                    action = "New" if name not in known else "Updated"
                    logging.info(f"{action} chart detected: {name}")
                    time.sleep(3)  # wait for TN to finish writing
                    commit_and_push(WATCH_DIR / name)
                    last_committed[name] = time.time()

            known = current

    except KeyboardInterrupt:
        logging.info("Auto-Commit Watcher stopped.")
