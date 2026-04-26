# MarketBullets — Wheat Chart Auto-Push Pipeline

Trade Navigator → OneDrive → GitHub → Squarespace

## How It Works

1. Export a JPG from Trade Navigator into the repo root folder.
2. `chart_watcher.py` detects the new file, matches it to a canonical name, copies it into `charts/`, and runs `git add → commit → push`.
3. Squarespace image embeds (permanent raw.githubusercontent.com URLs) update automatically within ~5 minutes.

No manual GitHub steps. No Squarespace edits. Ever.

---

## One-Time Setup

### 1. Install dependency

```
pip install watchdog==4.0.0
```

### 2. GitHub authentication

Run one manual push so Windows Credential Manager stores your token:

```
cd C:\users\hofer\onedrive\documents\github\websitecharts
git push origin main
```

Enter your GitHub username and Personal Access Token (PAT) as the password.
Generate a PAT at: GitHub → Settings → Developer Settings → Tokens (classic) → repo scope.

### 3. Verify CHART_MAP keys

Open `scripts/chart_watcher.py` and check the `CHART_MAP` dictionary.
The keys (left side) must match substrings in whatever Trade Navigator names the exported files.

```python
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
```

Example: if Trade Navigator exports `Chart_Winter_Wheat_04252026.jpg`, the key `"winter"` matches correctly.

### 4. (Optional) Auto-start on Windows login

1. Press Win+R → type `shell:startup` → Enter
2. Paste a shortcut to `start_watcher.bat` in that folder

---

## Daily Workflow

1. Double-click `start_watcher.bat`
2. Export chart(s) from Trade Navigator → save to repo root
3. Terminal confirms: Detected → Copied → Pushed → URL
4. Squarespace updates within ~5 minutes

---

## Squarespace Embed URLs (permanent — never change)

```
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-winter-belt.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-spring-belt.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-pacific-nw.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-ukraine.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-russia.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-canada.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-argentina.jpg
https://raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/charts/wheat-australia.jpg
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `git push` auth error | Re-run manual push, re-enter PAT when prompted |
| Chart not updating on site | Wait 5 min (GitHub CDN cache); verify raw URL directly in browser |
| Wrong chart gets wrong name | Check `CHART_MAP` keys in `chart_watcher.py`; restart watcher |
| Watcher doesn't detect file | Confirm OneDrive is fully synced (not Files On-Demand); save to repo root, not a subfolder |
| File extension not matched | Watcher only picks up `.jpg` / `.jpeg` |
