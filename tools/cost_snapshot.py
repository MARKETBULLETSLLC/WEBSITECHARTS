"""
MarketBullets — Nightly Cost Benchmark Snapshot
Pulls USDA ERS "Commodity Costs and Returns" data for wheat, re-buckets
the published line items into the Breakeven Calculator's three cost
categories, and appends one timestamped entry to data/cost-history.json.
Commits and pushes the update the same way chart exports are pushed
(chart_watcher.py / auto_commit_watcher.py).

Why ERS and not a nightly web search of farmdoc/Purdue/DTN:
ERS publishes a clean, machine-readable CSV
(https://www.ers.usda.gov/media/4978/wheat.csv) that updates on a fixed
schedule (~May 1 and ~Oct 1 each year). farmdoc, Purdue, and DTN publish
PDFs that are not reliably parseable by an unattended script and update
on the same slow cadence anyway — see README_COST_SNAPSHOT.md. Most
nightly runs will therefore append the same $/acre figures under a
fresh timestamp; that's expected, not a bug.

Run:      python tools/cost_snapshot.py
Schedule: tools/install_cost_snapshot_task.ps1 (registers a daily task)
"""

import csv
import io
import json
import logging
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS")
HISTORY_FILE = REPO_ROOT / "data" / "cost-history.json"
LOG_FILE = REPO_ROOT / "tools" / "cost_snapshot.log"
MAX_ENTRIES = 365

ERS_WHEAT_CSV_URL = "https://www.ers.usda.gov/media/4978/wheat.csv"

# USDA ERS Farm Resource Region containing eastern Washington / the Palouse
# dryland wheat belt (Whitman, Columbia, Walla Walla, Garfield, Asotin
# counties) — the closest ERS region to Waitsburg WA.
ERS_REGION = "Basin and Range"

# ERS (Category, Item) -> Breakeven Calculator bucket. "Opportunity cost of
# unpaid labor" is deliberately excluded — it's an imputed economic cost,
# not a cash outlay, and the calculator only asks producers for actual
# dollars spent.
LAND_FIXED_ITEMS = {
    ("Allocated overhead", "Opportunity cost of land"),
    ("Allocated overhead", "Capital recovery of machinery and equipment"),
    ("Allocated overhead", "Taxes and insurance"),
    ("Allocated overhead", "General farm overhead"),
}
SEED_CHEM_ITEMS = {
    ("Operating costs", "Seed"),
    ("Operating costs", "Fertilizer"),
    ("Operating costs", "Chemicals"),
}
FUEL_OPS_ITEMS = {
    ("Operating costs", "Fuel, lube, and electricity"),
    ("Operating costs", "Repairs"),
    ("Operating costs", "Custom services"),
    ("Operating costs", "Interest on operating inputs"),
    ("Operating costs", "Other variable expenses"),
    ("Allocated overhead", "Hired labor"),
}

PACIFIC = timezone(timedelta(hours=-7))  # PDT; a nightly timestamp label, not a DST-precise clock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)


def git(cmd):
    result = subprocess.run(
        ["git"] + cmd, cwd=REPO_ROOT, capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def fetch_ers_wheat_rows():
    req = urllib.request.Request(
        ERS_WHEAT_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 (MarketBullets cost snapshot script)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(raw)))


def bucket_totals(rows):
    """Returns (values_dict, source_note) for the latest year available in
    ERS_REGION, or None if the region/rows aren't usable."""
    region_rows = [r for r in rows if r.get("Region") == ERS_REGION]
    if not region_rows:
        return None

    years = [r["Year"] for r in region_rows if r["Category"] in ("Operating costs", "Allocated overhead")]
    if not years:
        return None
    latest_year = max(years)

    def total(bucket_items):
        s = 0.0
        for r in region_rows:
            if r["Year"] != latest_year:
                continue
            key = (r["Category"], r["Item"].strip())
            if key in bucket_items:
                s += float(r["Value"])
        return round(s, 2)

    land_fixed = total(LAND_FIXED_ITEMS)
    seed_chem = total(SEED_CHEM_ITEMS)
    fuel_ops = total(FUEL_OPS_ITEMS)
    if land_fixed == 0 and seed_chem == 0 and fuel_ops == 0:
        return None

    note = (
        f"USDA ERS Commodity Costs and Returns, Wheat \u2014 {ERS_REGION} region, {latest_year} "
        f"forecast (ers.usda.gov/data-products/commodity-costs-and-returns). "
        f"land_fixed = land + machinery capital recovery + taxes/insurance + farm overhead; "
        f"seed_chem = seed + fertilizer + chemicals; "
        f"fuel_ops = fuel/lube/electricity + repairs + custom services + hired labor + interest + other."
    )
    return {"land_fixed": land_fixed, "seed_chem": seed_chem, "fuel_ops": fuel_ops}, note


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []


def main():
    history = load_history()
    timestamp = datetime.now(PACIFIC).replace(microsecond=0).isoformat()

    try:
        rows = fetch_ers_wheat_rows()
        result = bucket_totals(rows)
        if result is None:
            raise ValueError(f"no usable ERS rows for region '{ERS_REGION}'")
        values, note = result
        logging.info(
            f"ERS fetch OK \u2014 land_fixed={values['land_fixed']} "
            f"seed_chem={values['seed_chem']} fuel_ops={values['fuel_ops']}"
        )
    except Exception as exc:
        if not history:
            logging.error(f"ERS fetch failed and no prior history to carry forward: {exc}")
            return
        last = history[-1]
        values = {k: last[k] for k in ("land_fixed", "seed_chem", "fuel_ops")}
        note = f"{last.get('source_notes', '')} [carried forward \u2014 ERS fetch failed: {exc}]"
        logging.warning(f"ERS fetch failed, carrying forward last known values: {exc}")

    entry = {"timestamp": timestamp, **values, "source_notes": note}
    history.append(entry)
    history = history[-MAX_ENTRIES:]

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
    logging.info(f"Wrote entry to {HISTORY_FILE.name} ({len(history)} total entries)")

    rc, _, err = git(["add", str(HISTORY_FILE)])
    if rc != 0:
        logging.error(f"git add failed: {err}")
        return

    rc, staged, _ = git(["diff", "--cached", "--name-only"])
    if "cost-history.json" not in staged:
        logging.info("No change to commit.")
        return

    today = datetime.now(PACIFIC).strftime("%Y-%m-%d")
    rc, _, err = git(["commit", "-m", f"cost snapshot: {today}"])
    if rc != 0:
        logging.error(f"git commit failed: {err}")
        return
    logging.info("Committed.")

    rc, _, err = git(["push", "origin", "main"])
    if rc == 0:
        logging.info("Pushed to GitHub.")
    else:
        logging.error(f"git push failed: {err}")


if __name__ == "__main__":
    main()
