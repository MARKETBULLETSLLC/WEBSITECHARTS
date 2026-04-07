#!/usr/bin/env python3
"""
MarketBullets Social Automation — Hub Orchestrator
===================================================
Ties together the RSS watcher, voice transformer, and Buffer client
into a single polling loop.

SETUP
-----
1. Copy .env.example → .env and fill in all values
2. pip install -r requirements.txt
3. python hub.py --dry-run          # test without posting
4. python hub.py                    # live mode — runs until Ctrl+C

MODES
-----
  python hub.py               Polls every POLL_INTERVAL_MINUTES (default 15)
  python hub.py --dry-run     Prints posts, does not call Buffer API
  python hub.py --once        Checks for new posts once and exits
  python hub.py --reset       Clears seen-GUIDs state (re-process latest entry)

FLOW (each poll cycle)
----------------------
  1. RSSWatcher.get_new_entries()   → new commentary entries
  2. Transformer.transform()        → Claude API → platform-specific posts
  3. BufferClient.queue_posts()     → push drafts to Buffer queue
  4. RSSWatcher.mark_processed()    → update state, prevent re-posting

Gary's approval touchpoint: ~5 min to review Buffer queue on mobile
and tap Approve before posts fire in the morning.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import pytz
import schedule
from dotenv import load_dotenv

from rss_watcher   import RSSWatcher
from transformer   import Transformer
from buffer_client import BufferClient

PACIFIC = pytz.timezone("America/Los_Angeles")


# ── Bootstrap ─────────────────────────────────────────────────────────────────

def load_env():
    """Load .env from the same directory as hub.py."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print(
            "ERROR: .env file not found.\n"
            "Copy .env.example → .env and fill in your values."
        )
        sys.exit(1)
    load_dotenv(env_path)


def validate_env():
    """Abort early if critical env vars are missing."""
    required = ["ANTHROPIC_API_KEY", "SQUARESPACE_RSS_PATH", "SQUARESPACE_DOMAIN"]
    missing  = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing required .env values: {', '.join(missing)}")
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    if not dry_run and not os.environ.get("BUFFER_ACCESS_TOKEN"):
        print("ERROR: BUFFER_ACCESS_TOKEN not set. Set DRY_RUN=true to test without Buffer.")
        sys.exit(1)


# ── Core Loop ─────────────────────────────────────────────────────────────────

def run_cycle(watcher: RSSWatcher, transformer: Transformer, client: BufferClient):
    """
    One full poll-and-process cycle.
    Called on a schedule or once in --once mode.
    """
    now = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M PT")
    print(f"\n[hub] Checking RSS — {now}")

    entries = watcher.get_new_entries()

    if not entries:
        print("  [hub] No new commentary found.")
        return

    chart_url = os.environ.get("SQUARESPACE_CHART_URL", "")

    for entry in entries:
        print(f"\n[hub] New commentary: {entry['title']}")

        # Step 1: Transform commentary into platform posts
        posts = transformer.transform(
            title = entry["title"],
            body  = entry["body"],
            link  = entry["link"],
        )

        # Step 2: Queue posts to Buffer
        results = client.queue_posts(
            posts     = posts,
            chart_url = chart_url,
            link      = entry["link"],
        )

        # Step 3: Mark as processed only on full or partial success
        successes = [k for k, v in results.items() if v]
        failures  = [k for k, v in results.items() if not v]

        if successes:
            watcher.mark_processed(entry["guid"])
            print(f"  [hub] Queued to: {', '.join(successes)}")
        if failures:
            print(f"  [hub] Failed on:  {', '.join(failures)} — will retry next cycle")


# ── CLI ────────────────────────────────────────────────────────────────────────

def reset_state():
    """Clear the seen-GUIDs state file."""
    from config import STATE_FILE
    state_path = os.path.join(os.path.dirname(__file__), STATE_FILE)
    if os.path.exists(state_path):
        os.remove(state_path)
        print(f"[hub] State reset — {state_path} deleted.")
    else:
        print("[hub] No state file found — nothing to reset.")


def main():
    parser = argparse.ArgumentParser(
        description="MarketBullets Social Automation Hub"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print generated posts without calling Buffer API"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run one poll cycle and exit"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear seen-GUIDs state and exit"
    )
    args = parser.parse_args()

    load_env()

    if args.reset:
        reset_state()
        sys.exit(0)

    # --dry-run flag overrides .env setting
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    validate_env()

    rss_url = (
        os.environ["SQUARESPACE_DOMAIN"].rstrip("/")
        + os.environ["SQUARESPACE_RSS_PATH"]
    )

    watcher     = RSSWatcher(rss_url)
    transformer = Transformer()
    client      = BufferClient()

    poll_interval = int(os.environ.get("POLL_INTERVAL_MINUTES", "15"))
    dry_label     = " [DRY RUN]" if os.environ.get("DRY_RUN") == "true" else ""

    print(f"[hub] MarketBullets Social Automation{dry_label}")
    print(f"[hub] RSS: {rss_url}")
    print(f"[hub] Poll interval: {poll_interval} minutes")

    if args.once:
        run_cycle(watcher, transformer, client)
        return

    # ── Continuous polling loop ────────────────────────────────────────────────
    # Run immediately on start, then on schedule.
    run_cycle(watcher, transformer, client)

    schedule.every(poll_interval).minutes.do(
        run_cycle, watcher=watcher, transformer=transformer, client=client
    )

    print(f"\n[hub] Running. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[hub] Stopped.")


if __name__ == "__main__":
    main()
