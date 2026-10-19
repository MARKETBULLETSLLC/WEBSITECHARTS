"""
MarketBullets — BoR Chart Engine
Draws the Box-o-Rox daily chart (WHEAT_SRW_BOR_D.png) from price data copied out of
Trade Navigator, keeps support/resistance/range/trendline/note annotations from day to
day, and writes a daily review sheet flagging which annotations need Gary's attention.

Usage:
    python tools/bor/bor_update.py              # read clipboard, write PREVIEW chart
    python tools/bor/bor_update.py --live       # read clipboard, write charts/ (auto-commit picks it up)
    python tools/bor/bor_update.py --file x.txt # read pasted text from a file instead of the clipboard
    python tools/bor/bor_update.py --no-paste   # redraw from saved history + annotations only

Paste format: see tools/bor/PASTE_FORMAT.txt. Instruction lines (SUPPORT:, NOTE:, ...) may
sit above the Trade Navigator data table; both are optional.
"""

import argparse
import html
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

REPO_ROOT = Path(__file__).resolve().parents[2]
CHART_NAME = "WHEAT_SRW_BOR_D.png"
DATA_DIR = REPO_ROOT / "data" / "bor"
HISTORY = DATA_DIR / "WHEAT_SRW_BOR_D_history.csv"
ANNOTATIONS = DATA_DIR / "WHEAT_SRW_BOR_D_annotations.json"
LIVE_OUT = REPO_ROOT / "charts" / CHART_NAME
PREVIEW_DIR = Path("M:/preview")
PREVIEW_OUT = PREVIEW_DIR / CHART_NAME
REVIEW_DIR = PREVIEW_DIR

VISIBLE_BARS = 120
W, H, DPI = 1876, 732, 100
GREEN, RED, BLUE = "#00B000", "#E00000", "#0000E0"
STATUS_COLOR = {"EXECUTE": RED, "SUSPEND": "#1a3a5c"}  # SUSPEND = BOR badge suspend blue
UP, DOWN = "#22C022", "#E01010"
SUPPORT_COLOR, RESIST_COLOR, TREND_COLOR = "#0050C8", "#C05000", "#6A2C91"
ZONE_LABEL = "Execute Sale of Tranche(s)"

DEFAULT_ANNOTATIONS = {
    "symbol_line": "ZW-202612:  Wheat CBT (Elec) Dec 2026 @ CBOT  (Daily bars)",
    "title": ["Chicago (SRW) Soft Red Winter", "{date}: CLOSE", "DAILY - {contract} (Current Contract)"],
    "contract": "DEC '26",
    "support": [], "resist": [], "range": [], "trend": [], "note": [],
}


# ── Price & date helpers ─────────────────────────────────────────────────────

def eighths(v):
    """Price in cents -> Trade Navigator ^eighths notation (696.5 -> 696^4)."""
    sign = "-" if v < 0 else ""
    v = abs(v)
    whole = math.floor(v + 1e-9)
    e = round((v - whole) * 8)
    if e == 8:
        whole, e = whole + 1, 0
    return f"{sign}{whole}^{e}"


def parse_price(s):
    """'731^4' -> 731.5, '731.5' -> 731.5"""
    s = s.strip()
    if "^" in s:
        whole, e = s.split("^")
        sign = -1 if whole.startswith("-") else 1
        return sign * (abs(int(whole)) + int(e) / 8)
    return float(s)


def tick(v):
    """Round to the nearest quarter-cent contract tick."""
    return round(v * 4) / 4


def parse_date(s):
    return pd.Timestamp(pd.to_datetime(s.strip())).normalize()


# ── Paste parsing ────────────────────────────────────────────────────────────

def read_clipboard():
    import tkinter
    root = tkinter.Tk()
    root.withdraw()
    try:
        return root.clipboard_get()
    finally:
        root.destroy()


def split_paste(text):
    """Separate instruction lines from the Trade Navigator data table."""
    directives, rows, header = [], [], None
    for line in text.splitlines():
        if not line.strip():
            continue
        if re.match(r"^\s*[A-Z]+\s*:", line):
            directives.append(line.strip())
        elif line.lstrip().startswith("Date"):
            header = re.split(r"\t|\s{2,}|,", line.strip())
        elif re.match(r"^\s*\d{4}[/-]\d{1,2}[/-]\d{1,2}|^\s*\d{1,2}/\d{1,2}/\d{4}", line):
            rows.append(re.split(r"\t|,|\s+", line.strip()))
    bars = None
    if rows:
        cols = ["Date", "Open", "High", "Low", "Close"]
        bars = pd.DataFrame([r[:5] for r in rows], columns=cols)
        bars["Date"] = pd.to_datetime(bars.Date).dt.normalize()
        bars[cols[1:]] = bars[cols[1:]].astype(float)
        # Optional Trade Navigator columns: Settle and Net Change (header change uses them if present)
        for name, pat in (("Settle", r"^settle"), ("NetChg", r"^net\s*ch|^chg$|^change$")):
            j = next((k for k, h in enumerate(header or []) if re.search(pat, h.strip(), re.I)), None)
            if j is not None:
                bars[name] = [parse_price(r[j]) if len(r) > j and r[j].strip() else np.nan for r in rows]
    return directives, bars


def apply_directives(ann, directives):
    """Apply SUPPORT/RESIST/RANGE/TREND/NOTE/REMOVE/TITLE/CONTRACT lines. Returns change log."""
    log = []
    for d in directives:
        key, _, rest = d.partition(":")
        key, rest = key.strip().upper(), rest.strip()
        try:
            if key in ("SUPPORT", "RESIST"):
                price, _, label = rest.partition(" ")
                kind = key.lower()
                p = parse_price(price)
                ann[kind] = [x for x in ann[kind] if x["price"] != p]
                ann[kind].append({"price": p, "label": label.strip()})
                log.append(f"{key} set at {eighths(p)} {label.strip()}")
            elif key == "RANGE":
                parts = rest.split()
                start = None
                if re.match(r"\d{4}[/-]|\d{1,2}/\d{1,2}/\d{4}", parts[0]):
                    start = str(parse_date(parts.pop(0)).date())
                lo, hi = sorted([parse_price(parts[0]), parse_price(parts[1])])
                label = " ".join(parts[2:])
                ann["range"].append({"low": lo, "high": hi, "start": start, "label": label})
                log.append(f"RANGE set {eighths(lo)}–{eighths(hi)} from {start or '20 bars back'} {label}")
            elif key == "TREND":
                p = rest.split(" ", 4)
                t = {"d1": str(parse_date(p[0]).date()), "p1": parse_price(p[1]),
                     "d2": str(parse_date(p[2]).date()), "p2": parse_price(p[3]),
                     "label": p[4] if len(p) > 4 else ""}
                ann["trend"].append(t)
                log.append(f"TREND set {t['d1']} {eighths(t['p1'])} → {t['d2']} {eighths(t['p2'])} {t['label']}")
            elif key == "NOTE":
                dt, anchor, text = rest.split(" ", 2)
                n = {"date": str(parse_date(dt).date()), "anchor": anchor.lower(), "text": text.strip()}
                ann["note"] = [x for x in ann["note"] if x["date"] != n["date"]]
                ann["note"].append(n)
                log.append(f"NOTE set {n['date']}")
            elif key == "REMOVE":
                kind, _, what = rest.partition(" ")
                kind, what = kind.lower(), what.strip()
                kind = {"resistance": "resist", "notes": "note", "trendline": "trend"}.get(kind, kind)
                before = len(ann[kind])
                if kind in ("support", "resist"):
                    ann[kind] = [x for x in ann[kind] if x["price"] != parse_price(what)]
                elif kind == "note":
                    ann[kind] = [x for x in ann[kind] if x["date"] != str(parse_date(what).date())]
                elif kind == "range":
                    lo = parse_price(what.split()[0])
                    ann[kind] = [x for x in ann[kind] if x["low"] != lo and x["high"] != lo]
                elif kind == "trend":
                    ann[kind] = [x for x in ann[kind] if what not in (x["label"], x["d1"])]
                removed = before - len(ann[kind])
                log.append(f"REMOVE {kind.upper()} {what}: {removed} removed" if removed
                           else f"REMOVE {kind.upper()} {what}: NOT FOUND — nothing removed")
            elif key == "TITLE":
                ann["title"] = [s.strip() for s in rest.split("|")]
                log.append("TITLE updated")
            elif key == "CONTRACT":
                ann["contract"] = rest
                log.append(f"CONTRACT set to {rest}")
            elif key == "SYMBOL":
                ann["symbol_line"] = rest
                log.append("SYMBOL line updated")
            else:
                log.append(f"UNRECOGNIZED instruction ignored: {d}")
        except (ValueError, IndexError, KeyError) as e:
            log.append(f"COULD NOT READ: {d}  ({e})")
    return log


def merge_history(bars, contract_changed):
    """Pasted bars overwrite saved bars on matching dates. A contract change replaces history."""
    if bars is None:
        return pd.read_csv(HISTORY, parse_dates=["Date"])
    if HISTORY.exists() and not contract_changed:
        old = pd.read_csv(HISTORY, parse_dates=["Date"])
        bars = pd.concat([old[~old.Date.isin(bars.Date)], bars])
    return bars.sort_values("Date").reset_index(drop=True)


# ── Daily review ─────────────────────────────────────────────────────────────

def trend_value(t, dates, i):
    """Trendline price at bar i, extrapolated through trading-day index."""
    idx = {d: k for k, d in enumerate(dates)}
    i1, i2 = idx.get(pd.Timestamp(t["d1"])), idx.get(pd.Timestamp(t["d2"]))
    if i1 is None or i2 is None or i1 == i2:
        return None
    return t["p1"] + (t["p2"] - t["p1"]) * (i - i1) / (i2 - i1)


def pivots(d, n=5):
    """Swing highs/lows: bar extreme beyond the n bars on each side."""
    hs, ls = [], []
    for i in range(n, len(d) - n):
        win = d.iloc[i - n:i + n + 1]
        if d.High.iloc[i] == win.High.max():
            hs.append((d.Date.iloc[i], d.High.iloc[i]))
        if d.Low.iloc[i] == win.Low.min():
            ls.append((d.Date.iloc[i], d.Low.iloc[i]))
    return hs, ls


def review(d, ann, first_visible):
    """Return (flags, quiet, suggestions). BOR informs; Gary decides."""
    flags, quiet = [], []
    last, prev = d.iloc[-1], d.iloc[-2]
    c, pc = last.Close, prev.Close

    # BOR state (information only — the status-change call is Gary's)
    def state(r):
        return "EXECUTE (60-D)" if r.Close < r.MA60 else "EXECUTE (20-D)" if r.Close < r.MA20 else "SUSPEND"
    s_now, s_prev = state(last), state(prev)
    bor = f"Benchmark reads {s_now}: close {eighths(c)} vs MA60 {eighths(tick(last.MA60))} / MA20 {eighths(tick(last.MA20))}"
    if s_now != s_prev:
        flags.append(("BOR", f"{bor}. Changed from {s_prev} today — your call on a status note."))
    else:
        quiet.append(("BOR", bor))

    recent = d.tail(30)
    for kind, below_is_break in (("support", True), ("resist", False)):
        for lv in ann[kind]:
            p = lv["price"]
            name = f"{kind.upper()} {eighths(p)} {lv['label']}".strip()
            broke = (c < p <= pc) if below_is_break else (c > p >= pc)
            beyond = c < p if below_is_break else c > p
            if broke:
                flags.append((name, f"Closed {'below' if below_is_break else 'above'} today ({eighths(c)}). Keep, move, or remove?"))
            elif beyond:
                flags.append((name, f"Still {'below' if below_is_break else 'above'} — {eighths(abs(c - p))} beyond. Role reversed? Keep, flip, or remove?"))
            elif last.Low <= p <= last.High:
                flags.append((name, f"Tested today (range {eighths(last.Low)}–{eighths(last.High)}), held."))
            elif not ((recent.Low <= p) & (recent.High >= p)).any() and abs(c - p) / c > 0.08:
                flags.append((name, f"Stale — untouched 30 bars, {abs(c - p) / c:.0%} from price. Still relevant?"))
            else:
                quiet.append((name, f"{eighths(abs(c - p))} from close, holding."))

    for rg in ann["range"]:
        name = f"RANGE {eighths(rg['low'])}–{eighths(rg['high'])} {rg['label']}".strip()
        outside = (d.Close > rg["high"]) | (d.Close < rg["low"])
        run = 0
        for o in outside[::-1]:
            if not o:
                break
            run += 1
        if run == 1:
            flags.append((name, f"First close outside ({eighths(c)}). Breakout or false move?"))
        elif run > 1:
            flags.append((name, f"{run} closes outside. Breakout confirmed? Remove or redraw?"))
        else:
            quiet.append((name, "Price inside."))

    dates = list(d.Date)
    for t in ann["trend"]:
        name = f"TREND {t['d1']}→{t['d2']} {t['label']}".strip()
        v, pv = trend_value(t, dates, len(d) - 1), trend_value(t, dates, len(d) - 2)
        if v is None:
            flags.append((name, "Anchor date not in price history — re-enter this trendline."))
        elif (c - v) * (pc - pv) < 0:
            flags.append((name, f"Crossed today: close {eighths(c)} vs line {eighths(tick(v))}. Keep, redraw, or remove?"))
        elif last.Low <= v <= last.High:
            flags.append((name, f"Tested today at {eighths(tick(v))}, held."))
        else:
            quiet.append((name, f"Line at {eighths(tick(v))}, close {'above' if c > v else 'below'}."))

    for n in ann["note"]:
        name = f"NOTE {n['date']}"
        nd = pd.Timestamp(n["date"])
        if nd < first_visible:
            flags.append((name, "Scrolled off the chart. Remove?"))
        else:
            pos = int((d.Date[d.Date >= first_visible] < nd).sum())
            if pos < 10:
                flags.append((name, f"Scrolls off in about {pos} bars."))
            else:
                quiet.append((name, "On chart."))

    # Suggested levels: recent swing highs/lows not already near a saved level
    existing = [x["price"] for x in ann["support"] + ann["resist"]]
    near = lambda p: any(abs(p - e) / p < 0.006 for e in existing)
    hs, ls = pivots(d.tail(80))
    sugg = []
    for dt, p in sorted(hs, key=lambda x: -x[1]):
        if p > c and not near(p) and len([s for s in sugg if s.startswith("RESIST")]) < 2:
            sugg.append(f"RESIST: {eighths(p)} swing high {dt:%b %d}")
    for dt, p in sorted(ls, key=lambda x: x[1], reverse=True):
        if p < c and not near(p) and len([s for s in sugg if s.startswith("SUPPORT")]) < 2:
            sugg.append(f"SUPPORT: {eighths(p)} swing low {dt:%b %d}")
    r20 = d.tail(20)
    if (r20.High.max() - r20.Low.min()) / c < 0.06:
        sugg.append(f"RANGE: {eighths(r20.Low.min())} {eighths(r20.High.max())} 20-day range")
    return flags, quiet, sugg


def write_review(d, flags, quiet, sugg, changes, out_path, chart_path):
    last = d.iloc[-1]
    rows = lambda items: "".join(
        f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td></tr>" for a, b in items)
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>BoR Review {last.Date:%Y-%m-%d}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#F5F5F0;color:#2a1f16;max-width:1100px;margin:24px auto;padding:0 16px}}
h1{{color:#4A3425;font-size:22px}} h2{{color:#8B6F47;font-size:16px;margin-top:28px;border-bottom:1px solid #D4A574}}
table{{border-collapse:collapse;width:100%}} td{{padding:6px 8px;border-bottom:1px solid #e4dccb;vertical-align:top}}
td:first-child{{font-weight:600;width:34%}} .flag td{{background:#fff4dc}}
pre{{background:#fff;border:1px solid #D4A574;padding:10px;user-select:all}} img{{width:100%;border:1px solid #ccc}}
.empty{{color:#7a6a55;font-style:italic}}
</style></head><body>
<h1>BoR Review — {last.Date:%A %B %d, %Y} close {eighths(last.Close)}</h1>
<h2>Needs your call ({len(flags)})</h2>
{"<table class=flag>" + rows(flags) + "</table>" if flags else "<p class=empty>Nothing flagged. Quiet day.</p>"}
<h2>Suggested levels (copy any line into your next paste)</h2>
{"<pre>" + html.escape(chr(10).join(sugg)) + "</pre>" if sugg else "<p class=empty>None.</p>"}
<h2>Changes applied from today's paste</h2>
{"<table>" + rows([("", c) for c in changes]) + "</table>" if changes else "<p class=empty>No instruction lines in today's paste.</p>"}
<h2>Holding steady ({len(quiet)})</h2>
<table>{rows(quiet)}</table>
<h2>Chart</h2><img src="{chart_path.as_uri()}">
</body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")


# ── Chart ────────────────────────────────────────────────────────────────────

def label_spot(ceiling, ymin, width):
    """Run of `width` bars with the most empty room beneath `ceiling`; returns (center, top)."""
    best, best_i = -1, len(ceiling) // 2
    for i in range(len(ceiling) - width):
        room = ceiling[i:i + width].min() - ymin
        if room > best:
            best, best_i = room, i
    return best_i + width / 2, ceiling[best_i:best_i + width].min()


def draw(d, ann, out):
    v = d.tail(VISIBLE_BARS).reset_index(drop=True)
    offset = len(d) - len(v)
    x = np.arange(len(v))
    last = v.iloc[-1]
    end = len(v) - 1

    lo = math.floor((v.Low.min() - 15) / 25) * 25
    hi = math.ceil((v.High.max() + 15) / 25) * 25
    pad_right = 12
    xr = len(v) + pad_right

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    ax = fig.add_axes([0.0, 0.055, 0.945, 0.885])
    ax.set_xlim(-1, xr)
    ax.set_ylim(lo, hi)

    grad = LinearSegmentedColormap.from_list("bg", ["#FFFFC8", "#C6D6E6"])
    ax.imshow(np.linspace(0, 1, 256).reshape(-1, 1), cmap=grad, aspect="auto",
              extent=[-1, xr, lo, hi], zorder=0)

    # EXECUTE zone: everything beneath the 60-day MA
    ax.fill_between(x, lo, v.MA60, color=GREEN, alpha=0.13, lw=0, zorder=1)

    for y in range(int(lo), int(hi) + 1, 25):
        ax.axhline(y, color="#606060", lw=0.6, ls=(0, (1, 4)), zorder=1.5)
    weekly = [i for i in x if i == 0 or v.Date[i].isocalendar()[1] != v.Date[i - 1].isocalendar()[1]]
    for i in weekly:
        ax.axvline(i, color="#606060", lw=0.6, ls=(0, (1, 4)), zorder=1.5)

    # Ranges, support/resistance, trendlines (behind candles)
    tag = dict(boxstyle="square,pad=0.15", fc="#FFFFF0", ec="none", alpha=0.75)
    for rg in ann["range"]:
        start = pd.Timestamp(rg["start"]) if rg.get("start") else v.Date.iloc[max(end - 20, 0)]
        x0 = int((v.Date < start).sum())
        ax.fill_between([x0, end + 1], rg["low"], rg["high"], color="#6080A0", alpha=0.12, lw=0, zorder=1.2)
        ax.hlines([rg["low"], rg["high"]], x0, end + 1, color="#40607F", lw=1, ls="--", zorder=2)
        if rg["label"]:
            ax.text(x0, rg["high"] + 1, rg["label"], color="#40607F", fontsize=11,
                    fontweight="bold", va="bottom", bbox=tag, zorder=6)
    for kind, color in (("support", SUPPORT_COLOR), ("resist", RESIST_COLOR)):
        for lv in ann[kind]:
            if not lo < lv["price"] < hi:
                continue
            ax.axhline(lv["price"], color=color, lw=1.4, ls=(0, (6, 3)), zorder=2)
            ax.text(0, lv["price"] + (1 if kind == "resist" else -1),
                    f"{lv['label']} {eighths(lv['price'])}".strip(), color=color, fontsize=11,
                    fontweight="bold", ha="left", va="bottom" if kind == "resist" else "top",
                    bbox=tag, zorder=6)
    dates = list(d.Date)
    for t in ann["trend"]:
        i1 = dates.index(pd.Timestamp(t["d1"])) - offset if pd.Timestamp(t["d1"]) in dates else None
        if i1 is None:
            continue
        xs = np.array([max(i1, 0), end + 3])
        ys = [trend_value(t, dates, xi + offset) for xi in xs]
        if None in ys:
            continue
        ax.plot(xs, ys, color=TREND_COLOR, lw=1.6, zorder=2.5)
        if t["label"]:
            ax.text(xs[0] + 1, ys[0] + 2, t["label"], color=TREND_COLOR, fontsize=11,
                    fontweight="bold", zorder=6)

    for i, r in v.iterrows():
        col = UP if r.Close >= r.Open else DOWN
        ax.vlines(i, r.Low, r.High, color="black", lw=1, zorder=3)
        ax.add_patch(Rectangle((i - 0.33, min(r.Open, r.Close)), 0.66, max(abs(r.Close - r.Open), 0.6),
                               facecolor=col, edgecolor="black", lw=0.7, zorder=4))

    ax.plot(x, v.MA20, color=RED, lw=1.8, zorder=5)
    ax.plot(x, v.MA60, color=GREEN, lw=1.8, zorder=5)

    # Note placement, worked out up front so the zone label can steer clear of notes
    idx = {dt: i for i, dt in enumerate(v.Date)}
    bar_px = W * 0.945 / (xr + 1)
    unit_px = H * 0.885 / (hi - lo)
    placed = []
    for n in ann["note"]:
        nd = pd.Timestamp(n["date"])
        if nd not in idx:
            continue
        i, r = idx[nd], v.iloc[idx[nd]]
        above = n["anchor"] == "high"
        y0 = r.High + 3 if above else r.Low - 3
        ty = y0 + (n.get("dy", 24) if above else -n.get("dy", 24))
        right = n.get("align") == "right"  # optional: text ends at the candle and runs left
        tx = i + 1 if right else i - 1
        lines = n["text"].split("|")
        span = max(map(len, lines)) * 9 / bar_px
        x0, x1 = (tx - span, tx) if right else (tx, tx + span)
        nlines = len(lines) + (1 if n.get("status") else 0)
        placed.append((n, i, y0, tx, ty, above, right, x0, x1, ty - nlines * 18 / unit_px))

    # Zone label in the emptiest stretch of the shading, below any notes hanging into it
    ceiling = np.minimum(v.Low.values, v.MA60.values)
    for *_, above, _r, x0, x1, bottom in placed:
        if not above:
            a, b = max(int(x0) - 1, 0), min(int(x1) + 2, len(ceiling))
            ceiling[a:b] = np.minimum(ceiling[a:b], bottom)
    cx, top = label_spot(ceiling, lo, width=28)
    ax.text(cx, lo + (top - lo) * 0.45, ZONE_LABEL, color="#006400", fontsize=21,
            fontweight="bold", ha="center", va="center", alpha=0.85, zorder=6)

    # Right-side tags, Threshold / Tripwire
    ma60, ma20, close = tick(last.MA60), tick(last.MA20), last.Close
    for val, bg in ((ma60, GREEN), (ma20, RED), (close, "black")):
        ax.text(1.0, val, eighths(val), transform=ax.get_yaxis_transform(), fontsize=15,
                fontweight="bold", color="white", va="center", ha="left",
                bbox=dict(boxstyle="square,pad=0.15", fc=bg, ec=bg), zorder=8, clip_on=False)
    for label, val, color, va in (("Threshold", ma60, GREEN, "bottom"), ("Tripwire", ma20, RED, "top")):
        ax.annotate("", xy=(end + 0.6, val), xytext=(xr - 0.2, val),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5), zorder=7)
        ax.text(xr - 0.2, val + (1.5 if va == "bottom" else -1.5), label, color=color,
                fontsize=13, fontweight="bold", ha="right", va=va, zorder=7)
    ax.annotate("", xy=(end + 0.6, close), xytext=(xr - 0.2, close),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.5), zorder=7)

    # Analyst notes — Gary's calls
    for n, i, y0, tx, ty, above, right, *_ in placed:
        col = {"red": RED, "blue": BLUE, "green": GREEN}.get(n.get("color", "red"), RED)
        txt = ax.text(tx, ty, n["text"].replace("|", "\n"), color=col, fontsize=11, fontweight="bold",
                      ha="right" if right else "left", multialignment="left",
                      va="bottom" if above else "top", zorder=7)
        src = txt
        st = n.get("status", "").upper()  # optional closing line, e.g. "EXECUTE is status."
        if st:
            last_line = ax.annotate(f"{st} is status.", xy=(0, 0), xycoords=txt, xytext=(0, -1),
                                    textcoords="offset points", ha="left", va="top", fontsize=11,
                                    fontweight="bold", color=STATUS_COLOR.get(st, col), zorder=7)
            src = last_line if above else txt
        # Arrow leaves the box corner nearest the candle
        corner = (1 if right else 0, 0 if above else 1)
        ax.annotate("", xy=(i, y0), xytext=corner, textcoords=src,
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.3, shrinkA=2), zorder=7)

    ax.yaxis.tick_right()
    yt = range(int(lo), int(hi) + 1, 25)
    ax.set_yticks(yt)
    ax.set_yticklabels([eighths(t) for t in yt], fontsize=15, color="#404040")
    xt = [i for i in weekly[::2] if i >= 3]
    ax.set_xticks(xt)
    ax.set_xticklabels([f"{v.Date[i]:%m/%d/%y}" for i in xt], fontsize=15, color="#404040")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    # Header strip
    fig.patch.set_facecolor("#FFFFC8")
    # Day's change only from TN's own Net Change or Settle columns; the Close column is last trade,
    # so close-minus-close can disagree with TN's header. No column, no change shown.
    chg = None
    if pd.notna(last.get("NetChg", np.nan)):
        chg = last.NetChg
    elif pd.notna(last.get("Settle", np.nan)) and pd.notna(d.iloc[-2].get("Settle", np.nan)):
        chg = last.Settle - d.iloc[-2].Settle
    chg_txt = "" if chg is None else f" ({'+' if chg >= 0 else ''}{eighths(chg)})"
    fig.text(0.5, 0.985, ann["symbol_line"], ha="center", va="top", fontsize=8, fontweight="bold")
    hdr = [(f"Tripwire = {eighths(ma20)}", RED),
           (f"  Threshold = {eighths(ma60)}", GREEN),
           (f"  {last.Date:%m/%d/%Y} = {eighths(close)}{chg_txt}", "black")]
    t = fig.text(0.935, 0.935, hdr[-1][0], ha="right", va="bottom", fontsize=17,
                 fontweight="bold", color=hdr[-1][1])
    fig.canvas.draw()
    for txt, col in reversed(hdr[:-1]):
        bb = t.get_window_extent().transformed(fig.transFigure.inverted())
        t = fig.text(bb.x0, 0.935, txt, ha="right", va="bottom", fontsize=17, fontweight="bold", color=col)
        fig.canvas.draw()

    title = "\n".join(line.format(date=f"{last.Date:%A %B %d, %Y}", contract=ann["contract"])
                      for line in ann["title"])
    ax.text(0.125, 0.86, title, transform=ax.transAxes, fontsize=21, fontweight="bold",
            color=BLUE, va="top", linespacing=1.15,
            bbox=dict(boxstyle="square,pad=0.2", fc="none", ec=BLUE, lw=1), zorder=9)
    ax.text(0.54, 0.80, "BoR", transform=ax.transAxes, fontsize=70, fontweight="bold",
            color=BLUE, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.15", fc="none", ec=BLUE, lw=1), zorder=9)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="write charts/ (published) instead of preview")
    ap.add_argument("--file", help="read pasted text from a file instead of the clipboard")
    ap.add_argument("--no-paste", action="store_true", help="redraw from saved data only")
    args = ap.parse_args()

    ann = json.loads(ANNOTATIONS.read_text(encoding="utf-8")) if ANNOTATIONS.exists() \
        else json.loads(json.dumps(DEFAULT_ANNOTATIONS))

    directives, bars = [], None
    if not args.no_paste:
        text = Path(args.file).read_text(encoding="utf-8") if args.file else read_clipboard()
        directives, bars = split_paste(text)
        if not directives and bars is None:
            sys.exit("Nothing usable on the clipboard — copy the Trade Navigator data table first.")

    old_contract = ann["contract"]
    changes = apply_directives(ann, directives)
    d = merge_history(bars, ann["contract"] != old_contract)
    if len(d) < 61:
        sys.exit(f"Only {len(d)} bars of history — the 60-day average needs at least 61. Paste the full table.")

    avg = (d.Open + d.High + d.Low + d.Close) / 4
    d["MA20"] = avg.rolling(20).mean()
    d["MA60"] = avg.rolling(60).mean()

    if not Path(PREVIEW_DIR.anchor).exists():
        sys.exit(f"Drive {PREVIEW_DIR.anchor} not found — the preview folder lives there.")
    out = LIVE_OUT if args.live else PREVIEW_OUT
    draw(d, ann, out)
    first_visible = d.Date.iloc[-VISIBLE_BARS] if len(d) >= VISIBLE_BARS else d.Date.iloc[0]
    flags, quiet, sugg = review(d, ann, first_visible)
    review_path = REVIEW_DIR / f"review-{d.Date.iloc[-1]:%Y-%m-%d}.html"
    write_review(d, flags, quiet, sugg, changes, review_path, out)

    # Save state only after a successful draw
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    keep = ["Date", "Open", "High", "Low", "Close"] + [c for c in ("Settle", "NetChg") if c in d]
    d[keep].to_csv(HISTORY, index=False, date_format="%Y-%m-%d")
    ANNOTATIONS.write_text(json.dumps(ann, indent=2), encoding="utf-8")

    print(f"Chart:  {out}{'  (LIVE)' if args.live else '  (preview)'}")
    print(f"Review: {review_path}  - {len(flags)} flagged")
    for c in changes:
        print(f"  {c}")
    print(review_path)


if __name__ == "__main__":
    main()
