"""
MarketBullets Social Automation — RSS Watcher
=============================================
Polls the Squarespace RSS feed and returns commentary entries that
haven't been processed yet.

State is persisted in social_state.json (next to hub.py) as a set of
entry GUIDs. On first run with no state file, only the MOST RECENT entry
is processed — prevents a backlog flood on initialization.

Usage:
    from rss_watcher import RSSWatcher
    watcher = RSSWatcher(rss_url="https://yoursite.com/blog?format=rss")
    entries = watcher.get_new_entries()
    # entries = [{"guid": "...", "title": "...", "body": "...", "link": "..."}]
"""

import json
import os
import re
import html

import feedparser
import requests

from config import STATE_FILE


class RSSWatcher:
    """
    Monitors a Squarespace RSS feed for new commentary entries.
    """

    def __init__(self, rss_url: str):
        self.rss_url   = rss_url
        self.state_path = os.path.join(os.path.dirname(__file__), STATE_FILE)
        self._seen_guids: set[str] = self._load_state()

    # ── Public ────────────────────────────────────────────────────────────────

    def get_new_entries(self) -> list[dict]:
        """
        Fetch the RSS feed and return entries not yet seen.

        Each entry dict contains:
            guid    — unique identifier (used for deduplication)
            title   — post headline
            body    — full text (HTML stripped)
            link    — permalink to the commentary
        """
        feed = feedparser.parse(self.rss_url)

        if feed.bozo:
            # feedparser sets bozo=True on malformed XML — still try to parse
            print(f"  [rss_watcher] Feed parse warning: {feed.bozo_exception}")

        if not feed.entries:
            print(f"  [rss_watcher] No entries found at {self.rss_url}")
            return []

        # First run with empty state: seed state with all current GUIDs,
        # return only the most recent entry to avoid a posting flood.
        is_first_run = len(self._seen_guids) == 0

        new_entries = []
        for entry in feed.entries:
            guid = self._entry_guid(entry)
            if guid not in self._seen_guids:
                parsed = self._parse_entry(entry, guid)
                if parsed:
                    new_entries.append(parsed)

        if is_first_run and new_entries:
            print(f"  [rss_watcher] First run — seeding state, processing only latest entry")
            # Mark all as seen except the most recent
            for e in feed.entries:
                self._seen_guids.add(self._entry_guid(e))
            # Re-add the most recent so it shows as "new"
            most_recent = new_entries[0]  # feed is newest-first
            self._seen_guids.discard(most_recent["guid"])
            new_entries = [most_recent]

        return new_entries

    def mark_processed(self, guid: str):
        """Call after successfully queuing a post to prevent reprocessing."""
        self._seen_guids.add(guid)
        self._save_state()

    # ── Private ───────────────────────────────────────────────────────────────

    def _entry_guid(self, entry) -> str:
        """Stable unique ID — prefer id/guid, fall back to link."""
        return getattr(entry, "id", None) or getattr(entry, "link", "")

    def _parse_entry(self, entry, guid: str) -> dict | None:
        """Extract title, body text, and link from a feed entry."""
        title = getattr(entry, "title", "").strip()
        link  = getattr(entry, "link",  "").strip()

        # Squarespace puts full post HTML in content[0].value or summary
        raw_html = ""
        if hasattr(entry, "content") and entry.content:
            raw_html = entry.content[0].value
        elif hasattr(entry, "summary"):
            raw_html = entry.summary

        body = self._strip_html(raw_html).strip()

        # If RSS only gives a summary (truncated), fetch the full page
        if len(body) < 300 and link:
            body = self._fetch_full_text(link) or body

        if not body:
            print(f"  [rss_watcher] Could not extract body for: {title}")
            return None

        return {"guid": guid, "title": title, "body": body, "link": link}

    def _strip_html(self, raw: str) -> str:
        """Remove HTML tags and decode entities."""
        text = re.sub(r"<[^>]+>", " ", raw)
        text = html.unescape(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _fetch_full_text(self, url: str) -> str:
        """
        Fetch the full commentary page and extract the main text block.
        Squarespace pages embed the post body in <div class="sqs-block-content">.
        Falls back to all paragraph text if that selector isn't found.
        """
        try:
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "MarketBullets-SocialBot/1.0"})
            resp.raise_for_status()
            page_html = resp.text

            # Try Squarespace content block first
            match = re.search(
                r'class="sqs-block-content"[^>]*>(.*?)</div>',
                page_html, re.DOTALL
            )
            if match:
                return self._strip_html(match.group(1))

            # Fall back: collect all <p> tag content
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", page_html, re.DOTALL)
            return self._strip_html(" ".join(paragraphs))

        except Exception as e:
            print(f"  [rss_watcher] Could not fetch full text from {url}: {e}")
            return ""

    def _load_state(self) -> set[str]:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    data = json.load(f)
                return set(data.get("seen_guids", []))
            except Exception as e:
                print(f"  [rss_watcher] Could not load state: {e}")
        return set()

    def _save_state(self):
        try:
            with open(self.state_path, "w") as f:
                json.dump({"seen_guids": list(self._seen_guids)}, f, indent=2)
        except Exception as e:
            print(f"  [rss_watcher] Could not save state: {e}")
