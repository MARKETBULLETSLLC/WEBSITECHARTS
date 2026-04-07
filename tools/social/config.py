"""
MarketBullets Social Automation — Platform Configuration
=========================================================
Non-secret settings: posting times, hashtags, character limits,
platform enable/disable flags.

To enable/disable a platform without touching hub.py, set its
ENABLED flag to False.
"""

# ── Platform Registry ─────────────────────────────────────────────────────────
# Keys match the BUFFER_PROFILE_* env variable suffixes in .env
# and the platform keys used throughout transformer.py / buffer_client.py

PLATFORMS = {
    "X": {
        "enabled":        True,
        "label":          "X (Twitter)",
        "char_limit":     280,
        "has_image":      True,
        "post_time_pt":   "05:00",   # Pacific Time — fires before CBOT open
        "env_key":        "BUFFER_PROFILE_X",
    },
    "BLUESKY": {
        "enabled":        True,
        "label":          "Bluesky",
        "char_limit":     300,
        "has_image":      True,
        "post_time_pt":   "05:00",
        "env_key":        "BUFFER_PROFILE_BLUESKY",
    },
    "LINKEDIN": {
        "enabled":        True,
        "label":          "LinkedIn",
        "char_limit":     3000,      # soft limit — keep posts 150-300 words
        "has_image":      True,
        "post_time_pt":   "06:00",
        "env_key":        "BUFFER_PROFILE_LINKEDIN",
    },
    "INSTAGRAM": {
        "enabled":        True,
        "label":          "Instagram",
        "char_limit":     2200,      # caption limit
        "has_image":      True,      # chart image is required
        "post_time_pt":   "07:00",
        "env_key":        "BUFFER_PROFILE_INSTAGRAM",
    },
    "FACEBOOK": {
        "enabled":        True,
        "label":          "Facebook",
        "char_limit":     63206,     # effectively unlimited — keep 100-200 words
        "has_image":      True,
        "post_time_pt":   "06:30",
        "env_key":        "BUFFER_PROFILE_FACEBOOK",
    },
    "GOOGLE": {
        "enabled":        True,
        "label":          "Google Business",
        "char_limit":     1500,      # GBP post limit
        "has_image":      True,
        "post_time_pt":   "07:30",
        "env_key":        "BUFFER_PROFILE_GOOGLE",
    },
}

# ── Hashtag Sets ──────────────────────────────────────────────────────────────
# Platform-specific. Only Instagram and X/Bluesky use hashtags in body copy.

HASHTAGS = {
    "X": ["#WheatMarket", "#GrainMarketing"],
    "BLUESKY": ["#wheat", "#grainmarket"],
    "INSTAGRAM": [
        "#WheatMarket", "#GrainMarketing", "#AgMarkets",
        "#WheatFutures", "#FarmMarketing", "#PNWWheat",
    ],
    "LINKEDIN":  [],
    "FACEBOOK":  [],
    "GOOGLE":    [],
}

# ── Claude Model ─────────────────────────────────────────────────────────────
# Use the same model family Gary runs on. Update as needed.
CLAUDE_MODEL = "claude-sonnet-4-6"

# Max tokens for generated post (generous ceiling — prompts enforce word count)
CLAUDE_MAX_TOKENS = 1024

# ── State File ────────────────────────────────────────────────────────────────
# JSON file tracking last-processed RSS entry GUID. Prevents re-posting.
# Stored next to hub.py so it persists between runs.
STATE_FILE = "social_state.json"
