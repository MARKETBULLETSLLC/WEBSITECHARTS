"""
MarketBullets Social Automation — Buffer API Client
====================================================
Pushes generated post drafts into Buffer's queue for each enabled platform.

Buffer API v1 reference: https://buffer.com/developers/api/updates

Each post is scheduled for the platform's configured posting time
(Pacific Time), targeting the NEXT occurrence of that time — so a post
queued at 10 PM schedules for 5 AM the following morning.

Dry-run mode (DRY_RUN=true in .env) prints posts without calling the API.

Usage:
    from buffer_client import BufferClient
    client = BufferClient()
    results = client.queue_posts(posts, chart_url="https://...", link="https://...")
    # results = {"X": True, "LINKEDIN": True, ...}
"""

import os
from datetime import datetime, timedelta

import pytz
import requests

from config import PLATFORMS

BUFFER_API_BASE = "https://api.bufferapp.com/1"
PACIFIC = pytz.timezone("America/Los_Angeles")


class BufferClient:
    """
    Sends post drafts to Buffer for all enabled platforms.
    """

    def __init__(self):
        self.access_token = os.environ.get("BUFFER_ACCESS_TOKEN", "")
        self.chart_url    = os.environ.get("SQUARESPACE_CHART_URL", "")
        self.dry_run      = os.environ.get("DRY_RUN", "false").lower() == "true"
        self._profile_ids = self._load_profile_ids()

        if not self.access_token and not self.dry_run:
            raise ValueError("BUFFER_ACCESS_TOKEN not set. Add it to .env or set DRY_RUN=true.")

    # ── Public ────────────────────────────────────────────────────────────────

    def queue_posts(
        self,
        posts: dict[str, str],
        chart_url: str,
        link: str,
    ) -> dict[str, bool]:
        """
        Queue a batch of platform posts to Buffer.

        Args:
            posts:      {platform_key: post_text} from transformer.py
            chart_url:  Public URL of the primary chart image
            link:       Commentary permalink — appended to posts that support it

        Returns:
            {platform_key: success_bool}
        """
        results = {}

        for platform_key, post_text in posts.items():
            if not post_text:
                print(f"  [buffer] Skipping {platform_key} — empty post text")
                results[platform_key] = False
                continue

            cfg = PLATFORMS.get(platform_key)
            if not cfg or not cfg["enabled"]:
                continue

            profile_id = self._profile_ids.get(platform_key)
            if not profile_id and not self.dry_run:
                print(f"  [buffer] No profile ID for {platform_key} — check .env")
                results[platform_key] = False
                continue

            scheduled_at = self._next_post_time(cfg["post_time_pt"])
            full_text    = self._append_link(platform_key, post_text, link)

            if self.dry_run:
                self._print_dry_run(platform_key, cfg["label"], full_text, scheduled_at)
                results[platform_key] = True
                continue

            success = self._send_to_buffer(
                platform_key  = platform_key,
                label         = cfg["label"],
                profile_id    = profile_id,
                text          = full_text,
                image_url     = chart_url if cfg["has_image"] else "",
                scheduled_at  = scheduled_at,
            )
            results[platform_key] = success

        return results

    # ── Private ───────────────────────────────────────────────────────────────

    def _send_to_buffer(
        self,
        platform_key: str,
        label: str,
        profile_id: str,
        text: str,
        image_url: str,
        scheduled_at: datetime,
    ) -> bool:
        """POST to Buffer's create update endpoint."""
        url = f"{BUFFER_API_BASE}/updates/create.json"

        payload = {
            "access_token":    self.access_token,
            "profile_ids[]":   profile_id,
            "text":            text,
            "scheduled_at":    scheduled_at.isoformat(),
            "now":             False,
        }

        if image_url:
            payload["media[picture]"] = image_url

        try:
            resp = requests.post(url, data=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            if data.get("success"):
                print(f"  [buffer] Queued {label} for {scheduled_at.strftime('%H:%M PT %b %d')}")
                return True
            else:
                print(f"  [buffer] Buffer rejected {label}: {data}")
                return False

        except requests.HTTPError as e:
            print(f"  [buffer] HTTP error for {label}: {e.response.status_code} — {e.response.text}")
            return False
        except Exception as e:
            print(f"  [buffer] ERROR for {label}: {e}")
            return False

    def _append_link(self, platform_key: str, text: str, link: str) -> str:
        """
        X and Bluesky: Buffer auto-shortens links — don't append.
        All others: append the commentary permalink on a new line.
        """
        if platform_key in ("X", "BLUESKY"):
            return text
        if link and "marketbulletsllc.com" not in text:
            return f"{text}\n\n{link}"
        return text

    def _next_post_time(self, time_str_pt: str) -> datetime:
        """
        Return the next occurrence of HH:MM in Pacific Time as a UTC datetime.
        If that time has already passed today, schedule for tomorrow.
        """
        now_pt = datetime.now(PACIFIC)
        hour, minute = map(int, time_str_pt.split(":"))

        target = now_pt.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now_pt:
            target += timedelta(days=1)

        return target.astimezone(pytz.utc)

    def _load_profile_ids(self) -> dict[str, str]:
        """Read Buffer profile IDs from environment variables."""
        ids = {}
        for platform_key, cfg in PLATFORMS.items():
            env_key = cfg.get("env_key", "")
            val = os.environ.get(env_key, "").strip()
            if val:
                ids[platform_key] = val
        return ids

    def _print_dry_run(
        self,
        platform_key: str,
        label: str,
        text: str,
        scheduled_at: datetime,
    ):
        divider = "─" * 60
        print(f"\n{divider}")
        print(f"DRY RUN — {label}  (scheduled: {scheduled_at.strftime('%H:%M UTC %b %d')})")
        print(divider)
        print(text)
        print(divider)
