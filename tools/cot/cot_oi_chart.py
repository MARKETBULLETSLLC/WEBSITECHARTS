#!/usr/bin/env python3
"""
MarketBullets — Chicago SRW: Price vs. Open Interest (weekly)
==============================================================
Builds charts/COT_SRW_OI_W.png from free, keyless public data:

  * CFTC Disaggregated COT, futures only (publicreporting.cftc.gov, dataset 72hh-3qpy),
    market code 001602 = WHEAT-SRW, Chicago Board of Trade:
      - total open interest (all contract months)
      - managed money long / short  -> net
  * Price on each COT "as of" Tuesday:
      - Gary's Trade Navigator daily export (Comb Cont Liq) wherever it covers the week,
        so the line matches every other gallery chart;
      - otherwise the live lead contract from Yahoo Finance (e.g. ZWZ26.CBT).

Each week is tagged with one of four regimes from the weekly change in price and
open interest:
    price down, OI up    -> NEW SELLING       (new shorts coming in)
    price down, OI down  -> LONG LIQUIDATION  (longs getting out)
    price up,   OI up    -> NEW BUYING        (new longs coming in)
    price up,   OI down  -> SHORT COVERING    (shorts buying back)

Hands-off by design: Task Scheduler runs this several times a week. It exits
quietly unless the CFTC has published a newer report than the last chart, so the
auto-commit watcher only sees (and pushes) the PNG when there is new data.
Holiday-delayed releases are picked up on the next run automatically.

Usage:
    python tools/cot/cot_oi_chart.py            # publish if a new report exists
    python tools/cot/cot_oi_chart.py --force    # rebuild + publish now
    python tools/cot/cot_oi_chart.py --preview M:/preview/COT_SRW_OI_W.png
                                                # render elsewhere, never touch charts/
"""

import argparse
import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import pandas as pd  # noqa: E402
import requests  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402

# ── Paths (self-locating, like the other tools) ──────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
CHART_OUT = REPO_ROOT / "charts" / "COT_SRW_OI_W.png"   # permanent generic filename
DATA_DIR = REPO_ROOT / "data" / "cot"
HISTORY_CSV = DATA_DIR / "COT_SRW_OI_history.csv"
STATE_JSON = DATA_DIR / "COT_SRW_OI_state.json"
LOG_FILE = Path(__file__).resolve().parent / "cot_oi.log"

# ── Feeds ─────────────────────────────────────────────────────────────────────
CFTC_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
CFTC_CODE = "001602"            # WHEAT-SRW - CHICAGO BOARD OF TRADE
WEEKS = 156                     # three years on the chart

# Yahoo carries no history for expired contracts, so TN is the history and Yahoo
# only fills weeks after the last TN export.
TN_DAILY = Path(r"C:\Users\hofer\OneDrive\Attachments\BULLETS it\SRW_Daily.txt")
CONTRACT_MONTHS = [(3, "H"), (5, "K"), (7, "N"), (9, "U"), (12, "Z")]
ROLL_DAYS = 15                  # roll to the next contract ~15 days before its delivery month

# ── Look: matches the 1876×732 gallery charts, brand off-white surface ───────
W, H, DPI = 1876, 732, 100
SURFACE = "#F5F5F0"
INK, INK_2, INK_MUTED = "#2A1F16", "#4A3425", "#7A6A55"
GRID = "#DDD5C6"
PRICE_COLOR = "#4A3425"         # Deep Brown
OI_COLOR = "#8B6F47"            # Aged Wood
MM_COLOR = "#6B5440"
ACCENT = "#D4A051"              # Wheat Gold

# Regime palette, validated with the dataviz validator (light, surface #F5F5F0,
# all pairs): lightness, chroma, CVD and normal-vision checks PASS. The two lighter
# slots WARN on contrast, so every regime also carries a text label (legend + header).
REGIMES = {
    "NEW SELLING":      ("#B4442E", "price ↓  open interest ↑"),
    "LONG LIQUIDATION": ("#E8876B", "price ↓  open interest ↓"),
    "NEW BUYING":       ("#1F64A8", "price ↑  open interest ↑"),
    "SHORT COVERING":   ("#5C9FD8", "price ↑  open interest ↓"),
}
REGIME_PLAIN = {
    "NEW SELLING": "new shorts coming in",
    "LONG LIQUIDATION": "longs getting out",
    "NEW BUYING": "new longs coming in",
    "SHORT COVERING": "shorts buying back",
}

log = logging.getLogger("cot_oi")


# ── Formatting ────────────────────────────────────────────────────────────────
FRACTIONS = {0: "", 25: "¼", 50: "½", 75: "¾"}


def _quarters(c: float) -> tuple[int, str]:
    q = round(abs(c) * 4) / 4
    whole = int(q)
    return whole, FRACTIONS.get(int(round((q - whole) * 100)), "")


def dollars(cents: float) -> str:
    """591.25 -> '$5.91¼' (quarter-cent ticks, the way the commentary writes them)."""
    whole, frac = _quarters(cents)
    return f"${whole / 100:.2f}{frac}"


def cents_change(c: float) -> str:
    whole, frac = _quarters(c)
    sign = "−" if c < 0 else "+"
    return f"{sign}${whole / 100:.2f}{frac}" if whole >= 100 else f"{sign}{whole}{frac}¢"


def contracts(n: float, signed: bool = False) -> str:
    n = int(round(n))
    sign = ("−" if n < 0 else "+") if signed else ("−" if n < 0 else "")
    return f"{sign}{abs(n):,}"


def pct(x: float) -> str:
    return f"{x:+.0%}".replace("-", "−")


def kfmt(n: float) -> str:
    return (f"{n / 1000:,.0f}K" if n else "0").replace("-", "−")


def md(d: pd.Timestamp) -> str:
    return f"{d:%b} {d.day}"


# ── Data ──────────────────────────────────────────────────────────────────────
def fetch_cot(weeks: int) -> pd.DataFrame:
    since = (date.today() - timedelta(weeks=weeks + 6)).isoformat()
    params = {
        "$select": ",".join([
            "report_date_as_yyyy_mm_dd", "open_interest_all",
            "m_money_positions_long_all", "m_money_positions_short_all",
        ]),
        "$where": f"cftc_contract_market_code='{CFTC_CODE}' AND report_date_as_yyyy_mm_dd >= '{since}'",
        "$order": "report_date_as_yyyy_mm_dd ASC",
        "$limit": 1000,
    }
    r = requests.get(CFTC_URL, params=params, timeout=30)
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise RuntimeError("CFTC returned no rows for SRW wheat")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"]).dt.normalize()
    df["oi"] = df["open_interest_all"].astype(float)
    df["mm_net"] = (df["m_money_positions_long_all"].astype(float)
                    - df["m_money_positions_short_all"].astype(float))
    return df[["date", "oi", "mm_net"]].drop_duplicates("date").sort_values("date").reset_index(drop=True)


def latest_cot_date() -> pd.Timestamp:
    params = {
        "$select": "max(report_date_as_yyyy_mm_dd) as d",
        "$where": f"cftc_contract_market_code='{CFTC_CODE}'",
    }
    r = requests.get(CFTC_URL, params=params, timeout=30)
    r.raise_for_status()
    return pd.Timestamp(r.json()[0]["d"]).normalize()


def lead_contract(d: pd.Timestamp) -> str:
    """Most-liquid contract on date d: the first one whose delivery month opens
    more than ROLL_DAYS after d (rolls ahead of first notice day)."""
    for year in (d.year, d.year + 1):
        for month, code in CONTRACT_MONTHS:
            if pd.Timestamp(year, month, 1) - pd.Timedelta(days=ROLL_DAYS) > d:
                return f"ZW{code}{str(year)[-2:]}.CBT"
    raise ValueError(d)


def tn_prices() -> pd.Series:
    """Gary's Trade Navigator export (Comb Cont Liq daily). Same series as the gallery charts."""
    if not TN_DAILY.exists():
        log.info(f"TN file not found ({TN_DAILY}); using the exchange feed only.")
        return pd.Series(dtype=float)
    df = pd.read_csv(TN_DAILY, sep="\t", usecols=["Date", "Close"])
    s = pd.Series(df["Close"].astype(float).values, index=pd.to_datetime(df["Date"], format="%Y/%m/%d"))
    return s[~s.index.duplicated(keep="last")].sort_index()


def yahoo_history(ticker: str, start: pd.Timestamp, cache: dict) -> pd.Series:
    if ticker not in cache:
        import yfinance as yf

        h = yf.Ticker(ticker).history(start=(start - pd.Timedelta(days=10)).date().isoformat(),
                                      interval="1d", auto_adjust=False)
        s = h["Close"].copy() if not h.empty else pd.Series(dtype=float)
        if not s.empty:
            s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
            s = s[~s.index.duplicated(keep="last")]
        cache[ticker] = s
    return cache[ticker]


def price_on(s: pd.Series, d: pd.Timestamp) -> float:
    """Close on the COT Tuesday; if that day didn't trade, the last session before it (≤4 days back)."""
    if s.empty:
        return float("nan")
    prior = s[(s.index <= d) & (s.index > d - pd.Timedelta(days=5))]
    return float(prior.iloc[-1]) if not prior.empty else float("nan")


def build(weeks: int) -> pd.DataFrame:
    cot = fetch_cot(weeks)
    tn = tn_prices()
    cache: dict = {}
    prices, sources = [], []
    for d in cot["date"]:
        p, src = price_on(tn, d), "TN"
        if pd.isna(p):
            src = lead_contract(d)
            p = price_on(yahoo_history(src, d, cache), d)
        prices.append(p)
        sources.append(src if not pd.isna(p) else "")
    cot["price"], cot["price_source"] = prices, sources
    missing = int(cot["price"].isna().sum())
    if missing:
        log.warning(f"{missing} COT week(s) have no price and are left off the chart")
    cot = cot.dropna(subset=["price"]).reset_index(drop=True)
    cot["d_price"] = cot["price"].diff()
    cot["d_oi"] = cot["oi"].diff()

    def regime(r):
        if pd.isna(r.d_price) or pd.isna(r.d_oi):
            return None
        if r.d_price < 0:
            return "NEW SELLING" if r.d_oi >= 0 else "LONG LIQUIDATION"
        return "NEW BUYING" if r.d_oi >= 0 else "SHORT COVERING"

    cot["regime"] = cot.apply(regime, axis=1)
    return cot.tail(weeks).reset_index(drop=True)


# ── Chart ─────────────────────────────────────────────────────────────────────
def panel_title(ax, text: str) -> None:
    ax.text(0.003, 0.97, text, transform=ax.transAxes, fontsize=12, color=INK_MUTED, va="top",
            fontweight="bold", zorder=10, bbox=dict(boxstyle="square,pad=0.2", fc=SURFACE, ec="none", alpha=0.9))


def end_label(ax, d, y, text) -> None:
    ax.annotate(text, (d, y), xytext=(12, 0), textcoords="offset points", va="center",
                fontsize=14, fontweight="bold", color=INK, annotation_clip=False)


def draw(df: pd.DataFrame, out: Path) -> None:
    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"]})
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=SURFACE)
    gs = fig.add_gridspec(4, 1, height_ratios=[3.0, 0.30, 1.75, 1.75], hspace=0.14,
                          left=0.058, right=0.925, top=0.775, bottom=0.115)
    ax_p = fig.add_subplot(gs[0])
    ax_r = fig.add_subplot(gs[1], sharex=ax_p)
    ax_o = fig.add_subplot(gs[2], sharex=ax_p)
    ax_m = fig.add_subplot(gs[3], sharex=ax_p)

    x = df["date"]
    week = pd.Timedelta(days=7)
    last = df.iloc[-1]

    for ax in (ax_p, ax_r, ax_o, ax_m):
        ax.set_facecolor(SURFACE)
        for s in ("top", "right", "left", "bottom"):
            ax.spines[s].set_visible(False)
        ax.tick_params(colors=INK_MUTED, labelsize=12, length=0, pad=6)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
    for ax in (ax_p, ax_r, ax_o):
        plt.setp(ax.get_xticklabels(), visible=False)

    # ── Price
    ax_p.plot(x, df["price"], color=PRICE_COLOR, lw=2, solid_capstyle="round")
    pmin, pmax = df["price"].min(), df["price"].max()
    ax_p.set_ylim(pmin - (pmax - pmin) * 0.06, pmax + (pmax - pmin) * 0.16)
    ax_p.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v / 100:.2f}"))
    ax_p.plot([last.date], [last.price], "o", ms=8, color=PRICE_COLOR, mec=SURFACE, mew=2, zorder=5)
    end_label(ax_p, last.date, last.price, dollars(last.price))
    panel_title(ax_p, "PRICE  ·  Chicago SRW settlement each COT Tuesday")

    recent = df.tail(26)
    hi = recent.loc[recent["price"].idxmax()]
    show_hi = hi.date != last.date
    if show_hi:
        ax_p.plot([hi.date], [hi.price], "o", ms=8, color=ACCENT, mec=SURFACE, mew=2, zorder=5)
        ax_p.annotate(f"{md(hi.date)} high {dollars(hi.price)}", (hi.date, hi.price), xytext=(-12, 0),
                      textcoords="offset points", ha="right", va="center", fontsize=12, color=INK_2)

    # ── Regime strip: one cell per week, surface gap between cells
    for _, r in df.iterrows():
        if r.regime:
            ax_r.bar(r.date, 1, width=week * 0.8, color=REGIMES[r.regime][0], lw=0)
    ax_r.set_ylim(0, 1)
    ax_r.set_yticks([])
    ax_r.grid(False)
    ax_r.annotate("weekly read", (1.0, 0.5), xycoords="axes fraction", xytext=(12, 0),
                  textcoords="offset points", va="center", fontsize=11, color=INK_MUTED)

    # ── Open interest
    base = df["oi"].min() * 0.9
    ax_o.fill_between(x, df["oi"], base, color=OI_COLOR, alpha=0.16, lw=0)
    ax_o.plot(x, df["oi"], color=OI_COLOR, lw=2)
    ax_o.set_ylim(base, df["oi"].max() * 1.10)
    ax_o.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: kfmt(v)))
    ax_o.yaxis.set_major_locator(mticker.MaxNLocator(3))
    ax_o.plot([last.date], [last.oi], "o", ms=8, color=OI_COLOR, mec=SURFACE, mew=2, zorder=5)
    end_label(ax_o, last.date, last.oi, contracts(last.oi))
    yr = df[df["date"] > last.date - pd.Timedelta(days=365)]
    oi_tag = "  ·  HIGHEST IN A YEAR" if last.oi >= yr["oi"].max() else ""
    panel_title(ax_o, f"OPEN INTEREST  ·  all contracts open, all months{oi_tag}")

    # ── Managed money net
    ax_m.bar(x, df["mm_net"], width=week * 0.7, color=MM_COLOR, lw=0)
    ax_m.axhline(0, color=INK_MUTED, lw=1)
    lo = df.loc[df["mm_net"].idxmin()]
    span = df["mm_net"].max() - lo.mm_net
    ax_m.set_ylim(lo.mm_net - span * 0.30, max(df["mm_net"].max(), 0) + span * 0.30)
    ax_m.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: kfmt(v)))
    ax_m.yaxis.set_major_locator(mticker.MaxNLocator(3))
    ax_m.axhline(lo.mm_net, color=ACCENT, lw=1.4, ls=(0, (6, 3)))
    ax_m.annotate(f"Most short in {len(df) // 52} years: {contracts(lo.mm_net)} ({md(lo.date)}, {lo.date:%Y})",
                  (lo.date, lo.mm_net), xytext=(0, -5), textcoords="offset points", ha="left", va="top",
                  fontsize=11, color=INK_2)
    end_label(ax_m, last.date, last.mm_net, contracts(last.mm_net))
    side = "net short" if last.mm_net < 0 else "net long"
    panel_title(ax_m, f"MANAGED MONEY (FUNDS)  ·  long minus short  ·  {side} {contracts(abs(last.mm_net))}")
    ax_m.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax_m.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax_m.set_xlim(df["date"].iloc[0] - week, last.date + week)

    # ── Header: title + as-of (left); this week's read + since-the-high (right)
    fig.text(0.035, 0.955, "Chicago SRW Wheat — Price vs. Open Interest", fontsize=24,
             fontweight="bold", color=INK, va="top")
    fig.text(0.035, 0.885, f"Weekly  ·  CFTC Commitments of Traders as of Tuesday, {last.date:%B} {last.date.day}, "
             f"{last.date:%Y}", fontsize=13, color=INK_MUTED, va="top")
    hx = 0.50
    if last.regime:
        fig.patches.append(FancyBboxPatch((hx, 0.912), 0.011, 0.038, boxstyle="round,pad=0,rounding_size=0.002",
                                          transform=fig.transFigure, fc=REGIMES[last.regime][0], ec="none"))
        fig.text(hx + 0.018, 0.955, f"This week: {last.regime.title()}", fontsize=18, fontweight="bold",
                 color=INK, va="top")
        fig.text(hx + 0.018, 0.885, f"Price {cents_change(last.d_price)}, open interest "
                 f"{contracts(last.d_oi, True)}: {REGIME_PLAIN[last.regime]}", fontsize=13, color=INK_2, va="top")
    if show_hi:
        dp, doi = last.price - hi.price, last.oi - hi.oi
        fig.text(hx + 0.018, 0.835, f"Since the {md(hi.date)} high: price {cents_change(dp)} ({pct(dp / hi.price)}), "
                 f"open interest {contracts(doi, True)} ({pct(doi / hi.oi)})", fontsize=13, color=INK_2, va="top")

    # ── Legend (identity never color-alone) + source line
    handles = [Patch(facecolor=c, edgecolor="none", label=f"{name.title()}  {desc}")
               for name, (c, desc) in REGIMES.items()]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=4, frameon=False,
               fontsize=11.5, labelcolor=INK_2, handlelength=1.1, handleheight=1.0, columnspacing=1.8)
    fig.text(0.985, 0.018, "Sources: CFTC Disaggregated COT, futures only · CBOT · MarketBullets®",
             fontsize=10, color=INK_MUTED, ha="right", va="bottom")

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp" + out.suffix)
    fig.savefig(tmp, dpi=DPI, facecolor=SURFACE)
    plt.close(fig)
    tmp.replace(out)  # atomic swap so the watcher never sees a half-written file


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="rebuild and publish even if no new report")
    ap.add_argument("--preview", type=Path, help="render to this path instead of charts/ (no state change)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s",
                        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()])

    try:
        state = json.loads(STATE_JSON.read_text()) if STATE_JSON.exists() else {}
        newest = latest_cot_date()
        if not (args.force or args.preview) and state.get("report_date") == newest.date().isoformat():
            log.info(f"No new COT report (latest {newest.date()}). Chart unchanged.")
            return 0

        df = build(WEEKS)
        out = args.preview or CHART_OUT
        draw(df, out)
        last = df.iloc[-1]
        log.info(f"Rendered {out} · as of {last.date.date()} · {last.regime} · price {last.price} "
                 f"({last.price_source}) · OI {int(last.oi)} · MM net {int(last.mm_net)}")

        if not args.preview:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            ints = {c: df[c].round().astype("Int64") for c in ("oi", "mm_net", "d_oi")}
            df.assign(date=df["date"].dt.date, **ints).to_csv(HISTORY_CSV, index=False, float_format="%.2f")
            STATE_JSON.write_text(json.dumps({"report_date": last.date.date().isoformat(),
                                              "rendered": datetime.now().isoformat(timespec="seconds")}, indent=2))
        return 0
    except Exception as e:  # keep the last good chart on any failure
        log.exception(f"COT OI chart not updated: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
