#!/usr/bin/env python3
"""
MarketBullets — End-of-Day Futures Report
==========================================
Pulls front two contract months for SRW, HRW, HRS wheat,
plus DXY and crude as correlated markets. Outputs plain text.

Run after ~3:15 PM CT (CME settlement).
Schedule via Windows Task Scheduler — see eod_report.bat

SETUP:
    pip install yfinance

OUTPUT:
    tools/eod_reports/eod_YYYYMMDD.txt
    (also printed to console)
"""

import sys
from datetime import datetime, date
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed.  Run:  pip install yfinance")
    sys.exit(1)

# ── Output directory ─────────────────────────────────────────────────────────
REPORT_DIR = Path(__file__).parent / "eod_reports"
REPORT_DIR.mkdir(exist_ok=True)

# ── Contract month codes ─────────────────────────────────────────────────────
# (calendar month number, futures letter code)
WHEAT_CONTRACT_MONTHS = [
    (3,  "H"),   # March
    (5,  "K"),   # May
    (7,  "N"),   # July
    (9,  "U"),   # September
    (12, "Z"),   # December
]

ROLL_DAYS = 15   # switch to next contract this many days before expiry (~14th)


# ── Contract math ─────────────────────────────────────────────────────────────

def get_front_months(today: date):
    """Return (code, year) tuples for front and second contract months."""
    candidates = []
    for year in [today.year, today.year + 1, today.year + 2]:
        for month_num, code in WHEAT_CONTRACT_MONTHS:
            exp = date(year, month_num, 14)
            if exp >= today:
                candidates.append((code, year, exp))

    candidates.sort(key=lambda x: x[2])

    front_code, front_year, front_exp = candidates[0]
    if (front_exp - today).days < ROLL_DAYS:
        front_code, front_year, _ = candidates[1]
        second_code, second_year, _ = candidates[2]
    else:
        second_code, second_year, _ = candidates[1]

    return (front_code, front_year), (second_code, second_year)


def build_ticker(base: str, code: str, year: int) -> str:
    """Construct yfinance ticker, e.g. ZWK26.CBT"""
    yr = str(year)[-2:]
    return f"{base}{code}{yr}.CBT"


# ── Data fetch ────────────────────────────────────────────────────────────────

def fetch(ticker_str: str, decimals: int = 2) -> dict:
    """Pull last two sessions from yfinance. Returns structured dict."""
    r = dict(ticker=ticker_str, settle=None, prev=None, change=None,
             pct=None, open=None, high=None, low=None, volume=None, ok=False)
    try:
        hist = yf.Ticker(ticker_str).history(period="5d")
        if hist.empty:
            return r
        latest = hist.iloc[-1]
        r["settle"] = round(float(latest["Close"]), decimals)
        r["open"]   = round(float(latest["Open"]),  decimals)
        r["high"]   = round(float(latest["High"]),  decimals)
        r["low"]    = round(float(latest["Low"]),   decimals)
        r["volume"] = int(latest["Volume"]) if latest["Volume"] else None
        if len(hist) >= 2:
            prev = float(hist.iloc[-2]["Close"])
            r["prev"]   = round(prev, decimals)
            chg         = r["settle"] - prev
            r["change"] = round(chg, decimals)
            r["pct"]    = round((chg / prev) * 100, 2) if prev else None
        r["ok"] = True
    except Exception as e:
        r["error"] = str(e)
    return r


# ── Formatting helpers ────────────────────────────────────────────────────────

def fp(val, w=7, d=2) -> str:
    """Format price, right-justified."""
    if val is None:
        return " " * (w - 3) + "N/A"
    return f"{val:{w}.{d}f}"


def fc(chg, pct) -> str:
    """Format change + pct string."""
    if chg is None:
        return "     N/A    "
    sign = "+" if chg >= 0 else ""
    pct_s = f"({sign}{pct:.1f}%)" if pct is not None else ""
    return f"{sign}{chg:6.2f}  {pct_s:<9}"


def fv(vol) -> str:
    """Format volume."""
    if vol is None:
        return "  N/A"
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:5.1f}M"
    if vol >= 1_000:
        return f"{vol / 1_000:5.0f}K"
    return f"{vol:6d}"


# ── Report builder ────────────────────────────────────────────────────────────

def build_report(today: date) -> str:
    front, second = get_front_months(today)

    # Label helpers
    def month_label(code, year):
        names = {"H": "MAR", "K": "MAY", "N": "JUL",
                 "U": "SEP", "Z": "DEC"}
        return f"{names.get(code, code)}{str(year)[-2:]}"

    f1 = month_label(*front)
    f2 = month_label(*second)

    lines = []
    W = 64

    def bar(char="="):
        lines.append(char * W)

    bar()
    lines.append(f"  MARKETBULLETS -- END-OF-DAY FUTURES REPORT")
    lines.append(f"  {today.strftime('%A, %B %d, %Y')}  |  CME Settlement")
    bar()

    # ── Wheat ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append("  WHEAT FUTURES                                        c/bu")
    lines.append("  " + "-" * (W - 2))
    lines.append(f"  {'CONTRACT':<14}  {'SETTLE':>7}  {'CHANGE':>12}  "
                 f"{'OPEN':>7}  {'HIGH':>7}  {'LOW':>7}  {'VOL':>6}")
    lines.append("  " + "-" * (W - 2))

    wheat = [
        ("SRW  ZW", "ZW"),
        ("HRW  KE", "KE"),
        ("HRS  MW", "MW"),    # Minneapolis spring wheat (MGEX/CME)
    ]

    for label, base in wheat:
        for slot_label, (code, year) in [(f1, front), (f2, second)]:
            ticker = build_ticker(base, code, year)
            q = fetch(ticker)
            cname = f"{label} {slot_label}"
            lines.append(
                f"  {cname:<14}  {fp(q['settle']):>7}  {fc(q['change'], q['pct']):<14}"
                f"  {fp(q['open']):>7}  {fp(q['high']):>7}  {fp(q['low']):>7}  {fv(q['volume']):>6}"
            )
        lines.append("  " + "." * (W - 2))

    # ── Spreads ───────────────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"  SPREADS  (front month: {f1})")
    lines.append("  " + "-" * 40)

    zw  = fetch(build_ticker("ZW", *front))
    ke  = fetch(build_ticker("KE", *front))
    mwe = fetch(build_ticker("MW", *front))

    def spread_line(label, a, b):
        if a["settle"] and b["settle"]:
            spd = round(b["settle"] - a["settle"], 2)
            sign = "+" if spd >= 0 else ""
            lines.append(f"  {label:<28}  {sign}{spd:.2f} c/bu")
        else:
            lines.append(f"  {label:<28}  N/A")

    spread_line("HRW premium over SRW:", ke,  zw)
    spread_line("HRS premium over SRW:", mwe, zw)
    spread_line("HRS premium over HRW:", mwe, ke)

    # ── Carry spread F1 vs F2 ─────────────────────────────────────────────────
    lines.append("")
    lines.append(f"  CARRY  ({f1} vs {f2})")
    lines.append("  " + "-" * 40)

    for label, base in wheat:
        q1 = fetch(build_ticker(base, *front))
        q2 = fetch(build_ticker(base, *second))
        if q1["settle"] and q2["settle"]:
            carry = round(q2["settle"] - q1["settle"], 2)
            sign = "+" if carry >= 0 else ""
            lines.append(f"  {label:<14}  {f2} vs {f1}:  {sign}{carry:.2f} c/bu")
        else:
            lines.append(f"  {label:<14}  N/A")

    # ── Correlated markets ────────────────────────────────────────────────────
    lines.append("")
    lines.append("  CORRELATED MARKETS")
    lines.append("  " + "-" * 40)

    corr = [
        ("U.S. Dollar (DXY)", "DX-Y.NYB", 2),
        ("Crude Oil WTI",     "CL=F",     2),
    ]

    for label, ticker, dec in corr:
        q = fetch(ticker, decimals=dec)
        settle_s = fp(q["settle"], w=8, d=dec)
        chg_s    = fc(q["change"], q["pct"])
        lines.append(f"  {label:<24}  {settle_s}  {chg_s}")

    # ── Footer ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"  Data: yfinance / CME  |  "
                 f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    bar()

    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    today = date.today()
    print(f"Fetching EOD data for {today}...\n")

    report = build_report(today)
    print(report)

    out = REPORT_DIR / f"eod_{today.strftime('%Y%m%d')}.txt"
    out.write_text(report, encoding="utf-8")
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
