# Cost Snapshot — Breakeven Calculator trend data

`cost_snapshot.py` runs nightly, pulls USDA ERS's wheat cost-of-production
data, and appends one entry to `data/cost-history.json`, which the
Breakeven Calculator's reference chart reads via
`raw.githubusercontent.com/MARKETBULLETSLLC/WEBSITECHARTS/main/data/cost-history.json`.

## Why USDA ERS only, not a nightly web search across all five sources

The original spec called for searching USDA ERS, farmdoc, Purdue, DTN, and
regional extension budgets every night. In practice:

- **farmdoc, Purdue, and DTN publish PDFs**, not structured data. A live
  test (2026-09-17) confirmed WebFetch cannot reliably pull numbers out of
  the farmdoc crop-budget PDF — it came back as unparseable binary. An
  unattended script with no LLM in the loop has even less chance.
- **All five sources update quarterly-to-annually at best**, not nightly
  — the spec itself flags this. A script that "web searches" every night
  for data that changes twice a year adds fragility (silent breakage,
  hallucinated numbers from a search summary) for zero added freshness.
- **USDA ERS is the one source with an actual machine-readable feed**:
  a stable CSV export (`ers.usda.gov/media/4978/wheat.csv`) that updates
  on a fixed schedule (~May 1 and ~Oct 1) and already breaks costs into
  category line items — no scraping or interpretation required.

So the nightly script fetches only the ERS CSV. On the ~363 nights a year
ERS hasn't republished, it re-appends the same $/acre figures under a
fresh timestamp — that's the "gracefully reuse the last value" behavior
the spec asked for, just via a real feed instead of a search-and-guess.

**If Gary wants farmdoc/Purdue/DTN reflected too:** that's a periodic
(quarterly-ish) research task best done in a Claude session — WebSearch +
source verification, the same way commentary sourcing works — not
something to bolt onto the unattended nightly job. Ask Claude to update
`data/cost-history.json` (or add an override) when a new budget drops.

## Region and category mapping

Eastern Washington / the Palouse dryland wheat belt (Whitman, Columbia,
Walla Walla, Garfield, Asotin counties) falls in USDA's **"Basin and
Range"** Farm Resource Region — the closest ERS region to Waitsburg, WA.
That's the region the script pulls, not the U.S. national average.

ERS line items are re-bucketed into the calculator's three categories:

| Calculator category | ERS line items |
|---|---|
| Land & Fixed | Opportunity cost of land, capital recovery of machinery/equipment, taxes & insurance, general farm overhead |
| Seed, Fertilizer & Chemical | Seed, fertilizer, chemicals |
| Fuel, Power & Operations | Fuel/lube/electricity, repairs, custom services, hired labor, interest on operating inputs, other variable expenses |

**Deliberately excluded:** ERS's "opportunity cost of unpaid labor" — an
imputed economic cost, not a cash outlay. The calculator only asks
producers for actual dollars spent, so the reference data should measure
the same thing.

## One-time setup

```
tools\install_cost_snapshot_task.ps1
```

Registers a Windows Task Scheduler job (`MarketBullets-CostSnapshot`,
daily at 2:15 AM). To run it once by hand for testing:

```
python tools\cost_snapshot.py
```

Log: `tools\cost_snapshot.log` (gitignored, same as the other watcher logs).
