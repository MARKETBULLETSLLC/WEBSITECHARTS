"""
MarketBullets — Commentary Watcher
Polls commentary/ every 10 seconds for new or updated YYYY-MM-DD.md files.
On change: rebuilds commentary/index.json, commits, and pushes.
Files starting with "_" (templates, samples, drafts) are ignored.

Companion to tools/auto_commit_watcher.py (charts). Same pattern,
no third-party libraries required.

Usage:
    python tools/commentary_watcher.py            # watch mode
    python tools/commentary_watcher.py --once     # index + commit + push, then exit
"""

import json
import re
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCH_DIR = REPO_ROOT / "commentary"
INDEX_FILE = WATCH_DIR / "index.json"
LOG_FILE = REPO_ROOT / "tools" / "commentary_watcher.log"

POLL_SECONDS = 10
COOLDOWN_SECONDS = 30

DATE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def git(cmd: list) -> tuple[int, str, str]:
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                            creationflags=flags)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def read_headline(path: Path) -> str:
    """First non-empty line, leading '#' stripped."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                return line.lstrip("#").strip()
    except OSError as e:
        logging.error(f"Could not read {path.name}: {e}")
    return "(no headline)"


def build_index() -> dict:
    entries = []
    for p in sorted(WATCH_DIR.glob("*.md"), reverse=True):
        m = DATE_NAME.match(p.name)
        if not m:
            continue  # ignores _TEMPLATE.md, _SAMPLE.md, README.md, drafts
        entries.append({
            "date": m.group(1),
            "headline": read_headline(p),
            "file": p.name,
        })
    return {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "entries": entries,  # newest first
    }


def write_index() -> bool:
    """Write index.json. Returns True if content changed."""
    new_index = build_index()
    new_entries = new_index["entries"]
    if INDEX_FILE.exists():
        try:
            old_entries = json.loads(INDEX_FILE.read_text(encoding="utf-8")).get("entries")
            # ignore the 'generated' timestamp when deciding whether anything changed
            if old_entries == new_entries:
                return False
        except (json.JSONDecodeError, OSError):
            pass
    INDEX_FILE.write_text(json.dumps(new_index, indent=2), encoding="utf-8")
    logging.info(f"index.json rebuilt — {len(new_entries)} entries")
    return True


def commit_and_push() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    rc, _, err = git(["git", "add", "commentary/"])
    if rc != 0:
        logging.error(f"git add failed: {err}")
        return

    rc, staged, _ = git(["git", "diff", "--cached", "--name-only"])
    if not staged:
        logging.info("Skipped (no change)")
        return

    rc, _, err = git(["git", "commit", "-m", f"Commentary update [{timestamp}]"])
    if rc != 0:
        logging.error(f"git commit failed: {err}")
        return
    logging.info(f"Committed: {staged.replace(chr(10), ', ')}")

    rc, _, err = git(["git", "push", "origin", "main"])
    if rc == 0:
        logging.info("Pushed.")
    else:
        logging.error(f"git push failed: {err}")


def snapshot() -> dict[str, float]:
    return {
        p.name: p.stat().st_mtime
        for p in WATCH_DIR.glob("*.md")
        if p.is_file() and DATE_NAME.match(p.name)
    }


def run_once() -> None:
    write_index()
    commit_and_push()


if __name__ == "__main__":
    WATCH_DIR.mkdir(exist_ok=True)

    if "--once" in sys.argv:
        run_once()
        sys.exit(0)

    logging.info("=" * 55)
    logging.info("MarketBullets Commentary Watcher started")
    logging.info(f"Watching: {WATCH_DIR}")
    logging.info(f"Poll interval: {POLL_SECONDS}s  |  Cooldown: {COOLDOWN_SECONDS}s")
    logging.info("Rebuilds index.json, commits AND pushes automatically.")
    logging.info("=" * 55)

    # Catch up on anything saved while the watcher was off
    run_once()

    known = snapshot()
    last_pushed: dict[str, float] = {}

    try:
        while True:
            time.sleep(POLL_SECONDS)
            current = snapshot()

            changed = [
                name for name, mtime in current.items()
                if mtime != known.get(name, 0)
                and (time.time() - last_pushed.get(name, 0)) >= COOLDOWN_SECONDS
            ]

            if changed:
                logging.info(f"Change detected: {', '.join(changed)}")
                time.sleep(3)  # let the editor finish writing
                run_once()
                for name in changed:
                    last_pushed[name] = time.time()

            known = current

    except KeyboardInterrupt:
        logging.info("Commentary Watcher stopped.")
