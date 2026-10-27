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
import urllib.request
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCH_DIR = REPO_ROOT / "charts"
LOG_FILE = REPO_ROOT / "tools" / "auto_commit.log"

NTFY_TOPIC_FILE = REPO_ROOT / "tools" / "ntfy_topic.txt"  # local only, excluded via .git/info/exclude

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


def notify(message: str) -> None:
    """Phone alert via ntfy. Public server — keep messages generic."""
    try:
        topic = NTFY_TOPIC_FILE.read_text(encoding="utf-8").strip()
        if topic:
            urllib.request.urlopen(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"), timeout=10)
    except Exception as e:
        logging.error(f"ntfy alert failed: {e}")


def pull_and_retry_push(filename: str) -> None:
    """Push was rejected: merge in outside commits, then push again. Never leave a half-done merge."""
    rc, _, err = git(["git", "pull", "--no-rebase", "--no-edit", "origin", "main"], REPO_ROOT)
    if rc != 0:
        git(["git", "merge", "--abort"], REPO_ROOT)
        logging.error(f"git pull failed (merge aborted) — {filename}: {err}")
        notify("Chart watcher: push blocked, auto-merge failed. Charts not reaching GitHub - needs a look.")
        return
    logging.info(f"Pulled outside commits from GitHub — {filename}")

    rc, _, err = git(["git", "push", "origin", "main"], REPO_ROOT)
    if rc == 0:
        logging.info(f"Pushed after pull: {filename}")
        notify("Chart watcher: GitHub had outside commits. Merged and pushed OK.")
    else:
        logging.error(f"git push failed after pull — {filename}: {err}")
        notify("Chart watcher: push still failing after pull. Charts not reaching GitHub - needs a look.")


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
    elif "rejected" in err:
        logging.warning(f"git push rejected — {filename}: GitHub has commits this repo lacks")
        pull_and_retry_push(filename)
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
                if mtime != prev_mtime and (time.time() - last_commit_time) < COOLDOWN_SECONDS:
                    current[name] = prev_mtime  # TN rewrote it inside the cooldown — revisit once it expires
                elif mtime != prev_mtime:
                    action = "New" if name not in known else "Updated"
                    logging.info(f"{action} chart detected: {name}")
                    time.sleep(3)  # wait for TN to finish writing
                    commit_and_push(WATCH_DIR / name)
                    last_committed[name] = time.time()

            known = current

    except KeyboardInterrupt:
        logging.info("Auto-Commit Watcher stopped.")
