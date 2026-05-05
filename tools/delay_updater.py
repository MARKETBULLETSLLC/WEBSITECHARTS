"""
delay_updater.py
────────────────
Maintains charts/10daydelay/*OLD.png — versions of each chart from
exactly 10 trading days ago. Run automatically via the post-commit
git hook, or manually: python tools/delay_updater.py

Naming: WHEAT_SRW_D.png  →  charts/10daydelay/WHEAT_SRW_DOLD.png

Trading days: Mon–Fri, minus major US equity/grain market holidays.
Update MARKET_HOLIDAYS each January for the new calendar year.
"""

import subprocess
import logging
from pathlib import Path
from datetime import date, timedelta

# ─── PATHS ────────────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).resolve().parent.parent
CHARTS_DIR = REPO_ROOT / "charts"
DELAY_DIR  = CHARTS_DIR / "10daydelay"
STATE_FILE = DELAY_DIR / ".last_updated"   # records last date this ran

LOG_FILE   = Path(__file__).parent / "delay_updater.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# ─── TRADING CALENDAR ─────────────────────────────────────────────────────────
# US grain/equity market holidays. Update the set each January.

MARKET_HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1,  1),   # New Year's Day
    date(2025, 1, 20),   # MLK Day
    date(2025, 2, 17),   # Presidents' Day
    date(2025, 4, 18),   # Good Friday
    date(2025, 5, 26),   # Memorial Day
    date(2025, 6, 19),   # Juneteenth
    date(2025, 7,  4),   # Independence Day
    date(2025, 9,  1),   # Labor Day
    date(2025, 11, 27),  # Thanksgiving
    date(2025, 12, 25),  # Christmas
    # 2026
    date(2026, 1,  1),   # New Year's Day
    date(2026, 1, 19),   # MLK Day
    date(2026, 2, 16),   # Presidents' Day
    date(2026, 4,  3),   # Good Friday
    date(2026, 5, 25),   # Memorial Day
    date(2026, 6, 19),   # Juneteenth
    date(2026, 7,  3),   # Independence Day (observed)
    date(2026, 9,  7),   # Labor Day
    date(2026, 11, 26),  # Thanksgiving
    date(2026, 12, 25),  # Christmas
}


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in MARKET_HOLIDAYS


def n_trading_days_ago(n: int, from_date: date | None = None) -> date:
    """Return the date that was exactly n trading days before from_date."""
    d = from_date or date.today()
    count = 0
    while count < n:
        d -= timedelta(days=1)
        if is_trading_day(d):
            count += 1
    return d


# ─── GIT HELPERS ──────────────────────────────────────────────────────────────

def _git(args: list[str], binary_output: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
    )
    if binary_output:
        return result.stdout if result.returncode == 0 else b""
    return result.stdout.decode("utf-8", errors="replace").strip()


def git_file_at_date(repo_rel_path: str, target_date: date) -> bytes | None:
    """
    Return raw bytes of repo_rel_path as it existed on or before target_date.
    Falls back to the oldest available commit if no commit predates target_date.
    Returns None if the file has never been committed.
    """
    date_str = target_date.strftime("%Y-%m-%d 23:59:59")

    # Most-recent commit that touched this file on or before target_date
    commit = _git([
        "log", f"--before={date_str}", "--format=%H", "-n", "1",
        "--", repo_rel_path,
    ])

    if not commit:
        # File has no history before target_date — use its very first commit
        commit = _git([
            "log", "--format=%H", "--reverse", "-n", "1",
            "--", repo_rel_path,
        ])

    if not commit:
        return None  # file has never been committed

    data = _git(["show", f"{commit}:{repo_rel_path}"], binary_output=True)
    return data if data else None


# ─── CORE UPDATE LOGIC ────────────────────────────────────────────────────────

def update_delay_folder() -> bool:
    """
    Populate charts/10daydelay/*OLD.png with versions from 10 trading days ago.
    Commits the result.  Returns True if a commit was made, False if skipped.

    Runs at most once per calendar day (guarded by STATE_FILE).
    """
    today = date.today()

    # Once-per-day guard — also prevents the hook from looping after this
    # script's own commit triggers the post-commit hook again.
    if STATE_FILE.exists():
        try:
            if STATE_FILE.read_text().strip() == today.isoformat():
                logging.info("delay_updater: already ran today — skipping")
                return False
        except OSError:
            pass

    target_date = n_trading_days_ago(10)
    logging.info(f"delay_updater: updating 10daydelay/ → charts from {target_date}")

    DELAY_DIR.mkdir(parents=True, exist_ok=True)

    charts = sorted(CHARTS_DIR.glob("*.png"))
    if not charts:
        logging.warning("delay_updater: no PNG files found in charts/ — nothing to do")
        return False

    written = 0
    for chart in charts:
        repo_rel = f"charts/{chart.name}"
        data = git_file_at_date(repo_rel, target_date)

        old_name = chart.stem + "OLD" + chart.suffix   # e.g. WHEAT_SRW_DOLD.png
        old_path = DELAY_DIR / old_name

        if data:
            old_path.write_bytes(data)
            written += 1
        else:
            logging.warning(f"  no history found for {chart.name} — leaving existing file")

    logging.info(f"  wrote {written}/{len(charts)} delayed charts")

    # Write state before committing so the recursive hook call exits immediately
    STATE_FILE.write_text(today.isoformat())

    # Stage everything in 10daydelay/
    _git(["add", str(DELAY_DIR.relative_to(REPO_ROOT))])

    # Only commit if something actually changed
    staged = _git(["diff", "--cached", "--name-only"])
    if not staged:
        logging.info("  10daydelay/ unchanged — no commit needed")
        return False

    commit_msg = (
        f"Auto-update: 10daydelay/ charts from {target_date.isoformat()} "
        f"[run {today.isoformat()}]"
    )
    _git(["commit", "-m", commit_msg])
    logging.info(f"  committed: {commit_msg}")
    return True


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv

    if force and STATE_FILE.exists():
        STATE_FILE.unlink()
        logging.info("delay_updater: --force flag — ignoring today-guard")

    updated = update_delay_folder()
    sys.exit(0 if updated or not force else 1)
