# BoR Chart Engine: Session Notes, Oct 18–24, 2026

A record of one working session on the Box-o-Rox (BoR) chart: the hold rule, changes to the chart engine, the wording sweep on the dashboard, and what's still open.

---

## 1. BOR rules (as discussed)

| State | Trigger |
|---|---|
| **SUSPEND** | Settlement above the green line (the 60-day average) |
| **EXECUTE (green line)** | Settlement drops below the green line |
| **EXECUTE (Tripwire)** | Early signal: still above the green line, but crosses below the Tripwire (the 20-day average), with no discretionary hold in effect |

- Both averages use the bar's (Open + High + Low + Close) ÷ 4.
- BOR informs; Gary decides. The engine flags a state change on the review sheet but never sets the status itself.
- **Naming:** the green line was called "Threshold" during this session. A later session (Oct 24) retired that word. The chart now labels the line "Above = Suspend / Below = Execute", and running copy calls it the **Suspend/Execute line**.
- **Subscriber-facing copy never shows the averages' lengths** (60-day, 20-day, "60-D", "AvgOHLC").

## 2. Discretionary hold (draft, not approved)

A hold keeps the current status through a single settlement that would otherwise change it.

**Top 5 reasons a producer would hold**

| # | Reason | Typical length (rule of thumb) |
|---|---|---|
| 1 | A major report (WASDE, Grain Stocks, Crop Production) due within a session or two | 1–3 sessions |
| 2 | Weak cross: only a tick or two past the line, light volume, holiday trade | 1–2 sessions |
| 3 | Weekly or monthly chart still pointing the other way | about 5 sessions |
| 4 | Contract roll or delivery distortion | 5–10 sessions |
| 5 | Headline shock (Black Sea, policy, weather) | 1–3 sessions |

**Top 3 reasons a hold ends:** a second close confirms the cross; price closes back on the original side; or the reason for the hold clears.

**Draft rule:**
> When one settlement crosses a trigger line, Gary may hold the current BOR status. Each hold is posted on the chart the same night, with its reason and what releases it. It ends at the first of: (1) a second confirming close, (2) a close back on the original side, (3) the end of its stated reason, or 5 sessions, unless renewed in writing.

**Open conflict:** the draft also said a hold "never delays EXECUTE (green line)". Actual practice contradicts that. The Oct 8 commentary held **SUSPEND** through the WASDE report even though Oct 7 settled below the line; the hold expired with the report. The rule needs to allow that case, for example limited to a named report or event and lasting through report day.

**Where the rule will appear:** off the chart, as a "Discretionary Hold" block in the BoR section of the members dashboard (BENCHMARK1.html) and in the BoR document in the Supplemental Library. Later, a HOLD tag on the badge while a hold is active.

**Oct 6 hold notice:** the notice drawn on the chart this session said "EXECUTE stands". The commentary shows the status was SUSPEND, so that notice was wrong. It is no longer on the chart.

## 3. Settlement vs. Trade Navigator's Close

- Trade Navigator's **Close** column is the last trade, not the official settlement. On Oct 15–16 each was ¾¢ below the CBOT settlement (670^0 and 660^4).
- On Oct 16 Trade Navigator's header showed −10^2. That is Friday's last trade minus Thursday's settlement, two different kinds of price. The official change was −9^4.
- **Engine behavior:** the header shows the day's change only when the paste includes a **Net Change** or **Settle** column, or when Net Change is entered in the history file. Otherwise the change is left off.
- **Watch item:** BOR is defined on settlement. When a close lands within about 2¢ of a line, confirm the CBOT settlement before making a status call.

## 4. Engine changes (tools/bor/bor_update.py)

**Notes** (`note` entries in data/bor/WHEAT_SRW_BOR_D_annotations.json)

| Field | Effect |
|---|---|
| `color` | `red` (default), `blue` or `green` |
| `dy` | Distance from the candle, to clear other notes |
| `align: "right"` | Text ends at the candle and runs left |
| `status` | Adds a closing line "EXECUTE is status." (red) or "SUSPEND is status." (badge navy, #1a3a5c) |

- Arrows start at the note corner nearest the candle, so they don't cross.

**Chart-wide settings in the same file**

| Key | Effect |
|---|---|
| ~~`header: "ma"`~~ | Removed 2026-10-24. The header always reads "Tripwire / Suspend/Execute"; the chart never shows the averages' lengths. |
| `threshold_label`, `tripwire_label`, `close_label` | Text beside the right-side price tags; `\|` starts a new line |
| `text` | Free text placed by date and price: `{date, price, text, color, size}` |
| `zone_label` | Fixed `{date, price}` for "Execute Sale of Tranche(s)". Without it, the label finds the emptiest spot in the shading on its own and steers clear of notes and free text. |

**Paste and command line**
- `Settle` / `Net Change` columns in the paste are detected by header name, in any position.
- Negative eighths (e.g. `-10^2`) now parse correctly.
- `--out <path>` writes the chart to any filename. Example: `python tools/bor/bor_update.py --no-paste --out charts/WHEAT_SRW_BOR_Dhisto.png`

## 5. Dashboard wording sweep

The average lengths were replaced with named lines in everything subscribers see (later renamed again; see section 1):
- BENCHMARK1.html
- index01.html and index.html (including the Oct 8 commentary text)
- MB_DASH_01_BOR_BADGE.html
- supplemental_documents.html
- proto_member_charts.html
- the chart header

**Also changed:**
- The SUSPEND card now reads: "Settlement stays above the [line]. Patience is the posture; wait for confirmation."
- Internal code names (`execute-60d`, etc.) were left alone because subscribers never see them.

## 6. Publishing log

| Commit | What |
|---|---|
| `039f0d4a` | Engine chart first published live; Oct 6 hold notice; header change only from Settle/Net Change |
| `e46fb53c` | Note arrows untangled; status line on notes |
| `fbb58137` | Moving-average terms replaced in dashboard copy and chart header |
| `2222a1a2` | Engine chart for the 10/23 close replaced a Trade Navigator export of `WHEAT_SRW_BOR_D.png` |

**Two files:**
- `WHEAT_SRW_BOR_D.png` is the file the members page loads. Trade Navigator exports to it, so each export replaces the engine chart. The rules template is the planned fix.
- `WHEAT_SRW_BOR_Dhisto.png` is the engine version (shaded "histo" treatment). On Oct 24 it was rebuilt to carry every label and figure from Gary's Trade Navigator chart. Typos in the status banner were corrected, and the Trade Navigator branding line was left off.

## 7. Open items

1. **Hold rule:** approve or revise the draft (section 2), including the WASDE case.
2. **Dashboard hold block:** publish it to BENCHMARK1.html and the BoR library document once the rule is approved, then run the PAC audit on it.
3. **Master Prompt:** amend the BOR section to match the approved rule and the green-line naming.
4. **Header on the Dhisto chart:** `header: "ma"` shows the average lengths, which goes against the subscriber-copy rule. Decide before Dhisto is shown to subscribers.
5. **Members page source:** to use `Dhisto`, the page must point at it. That's a permanent embed change and needs one Squarespace re-paste.
6. **Trade Navigator columns:** check whether the data table can include a Settle or Net Change column.
7. **Desktop shortcut:** `BoR_Update.bat` still points at the retired OneDrive copy of the repo, not `M:\GitHub\WEBSITECHARTS`.
8. **Uncommitted at the end of the session:** engine, notes file and history (Oct 24 changes), per instruction.
