#!/usr/bin/env python3
"""
export_sales.py -- weekly USDA FAS wheat export sales, summed from the ESR API.

Usage:
    python tools/export_sales.py                 # latest week, prints a summary
    python tools/export_sales.py --week 2026-10-29
    python tools/export_sales.py --json          # also writes data/export_sales_wheat.json

The API key is read from the USDA_FAS_API_KEY environment variable, or from the
first line of ~/.usda_fas_key (a file OUTSIDE the repo). It is never written to
the repo. Free key: https://api.fas.usda.gov

Host note: the old apps.fas.usda.gov/OpenData host returns HTTP 500 on every
endpoint; api.fas.usda.gov with an X-Api-Key header is the working one.
The API returns one row per country per week; this script sums them.
Units are metric tonnes. Country 9990 = unknown destinations (cancellations
show up there as negatives).
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

BASE = "https://api.fas.usda.gov/api/esr"
CLASSES = {107: "All wheat", 101: "HRW", 102: "SRW", 103: "HRS", 104: "White"}
FIELDS = ["weeklyExports", "grossNewSales", "currentMYNetSales", "nextMYNetSales",
          "accumulatedExports", "outstandingSales", "currentMYTotalCommitment"]


def api_key():
    key = os.environ.get("USDA_FAS_API_KEY", "").strip()
    if not key:
        p = os.path.join(os.path.expanduser("~"), ".usda_fas_key")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                key = f.readline().strip()
    if not key:
        sys.exit("No API key. Set USDA_FAS_API_KEY (or put it on line 1 of ~/.usda_fas_key).")
    return key


def get(path, key):
    req = urllib.request.Request(BASE + path, headers={"X-Api-Key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def marketing_year(d):
    """Wheat MY starts June 1; the API labels it by its ending year (2026/27 -> 2027)."""
    return d.year + 1 if d.month >= 6 else d.year


def week_rows(code, my, week, key):
    rows = get(f"/exports/commodityCode/{code}/allCountries/marketYear/{my}", key)
    return [r for r in rows if r["weekEndingDate"].startswith(week)], rows


def total(rows):
    return {f: sum(r[f] for r in rows) for f in FIELDS}


def pct(a, b):
    return None if not b else round((a / b - 1) * 100, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="week-ending date YYYY-MM-DD (default: latest posted)")
    ap.add_argument("--json", action="store_true", help="also write data/export_sales_wheat.json")
    a = ap.parse_args()
    key = api_key()

    names = {c["countryCode"]: c["countryDescription"].strip() for c in get("/countries", key)}
    rel = [r for r in get("/datareleasedates", key) if r["commodityCode"] == 107]
    release = max(r["releaseTimeStamp"] for r in rel) if rel else "?"
    my = max(r["marketYear"] for r in rel) if rel else marketing_year(dt.date.today())

    _, all_rows = week_rows(107, my, "", key)
    week = a.week or max(r["weekEndingDate"] for r in all_rows)[:10]
    wk = dt.date.fromisoformat(week)
    prior = (wk - dt.timedelta(days=7)).isoformat()
    ly = (wk - dt.timedelta(days=364)).isoformat()

    out = {"weekEnding": week, "released": release, "marketYear": my, "classes": {}, "buyers": {}}
    for code, label in CLASSES.items():
        cur, _ = week_rows(code, my, week, key)
        pri, _ = week_rows(code, my, prior, key)
        lyr, _ = week_rows(code, my - 1, ly, key)
        t, p, y = total(cur), total(pri), total(lyr)
        out["classes"][label] = {"thisWeek": t, "priorWeek": p, "yearAgo": y}
        if code == 107:
            out["buyers"] = {
                "topNetSales": sorted(((r["currentMYNetSales"], names.get(r["countryCode"], r["countryCode"])) for r in cur), reverse=True)[:6],
                "reductions": sorted(((r["currentMYNetSales"], names.get(r["countryCode"], r["countryCode"])) for r in cur))[:4],
                "topShipments": sorted(((r["weeklyExports"], names.get(r["countryCode"], r["countryCode"])) for r in cur), reverse=True)[:5],
            }

    print(f"USDA FAS Export Sales -- week ended {week}   (released {release} ET; MY {my-1}/{str(my)[2:]}; tonnes)")
    for label, d in out["classes"].items():
        t, p, y = d["thisWeek"], d["priorWeek"], d["yearAgo"]
        print(f"\n{label}")
        print(f"  net sales      {t['currentMYNetSales']:>11,}   prior wk {p['currentMYNetSales']:>11,}   yr ago {y['currentMYNetSales']:>11,}")
        print(f"  shipments      {t['weeklyExports']:>11,}   prior wk {p['weeklyExports']:>11,}   yr ago {y['weeklyExports']:>11,}")
        print(f"  accum exports  {t['accumulatedExports']:>11,}   vs yr ago {pct(t['accumulatedExports'], y['accumulatedExports'])}%")
        print(f"  commitments    {t['currentMYTotalCommitment']:>11,}   vs yr ago {pct(t['currentMYTotalCommitment'], y['currentMYTotalCommitment'])}%")
    b = out["buyers"]
    print("\nTop net buyers:  " + ", ".join(f"{n} {v:,}" for v, n in b["topNetSales"]))
    print("Reductions:      " + ", ".join(f"{n} {v:,}" for v, n in b["reductions"] if v < 0))
    print("Top shipments:   " + ", ".join(f"{n} {v:,}" for v, n in b["topShipments"]))

    if a.json:
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "export_sales_wheat.json")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"\nWrote {os.path.normpath(dest)}")


if __name__ == "__main__":
    main()
