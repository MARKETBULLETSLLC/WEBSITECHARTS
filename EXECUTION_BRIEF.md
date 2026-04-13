# EXECUTION BRIEF - MARKETBULLETS PHASE 1 (Gary)

**Phase:** 1 of 3 (MVP Phase 1)  
**Timeline:** April 12-26, 2026 (15 minutes of Gary work)  
**Responsibility:** Gary (Editorial/Content)  
**Gabe Responsibility:** 20+ hours (development)  

---

## Executive Summary

Phase 1 API is now ready. Gabe begins Monday (April 15) and deploys live by April 26. Your role: **prepare the data** that feeds the API.

---

## What is Happening (Week 1-2)

**Gabe is:**
1. Setting up development environment (120 min)
2. Verifying all 4 API endpoints work (180 min)
3. Testing caching and performance (30 min)
4. Deploying to Vercel production (60 min)

**You are:**
1. ✅ Creating Google Sheets structure (15 min)
2. ✅ Populating initial chart list (30 min)
3. ✅ Adding initial quote data (15 min)
4. ✅ Setting BoR status indicator (5 min)

---

## Your Actions (This Week)

### ACTION 1: Create Google Sheet (15 min)

**Create new Google Sheet named: `MarketBullets_Phase1_Data`**

1. Go to https://sheets.google.com/
2. Click "Create" → "Spreadsheet"
3. Name it: `MarketBullets_Phase1_Data`
4. Create 4 sheets (tabs at bottom):
   - `Charts`
   - `Quotes`
   - `BoR_Status`
   - `Config`

**Get Spreadsheet ID:**
- URL: `https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit`
- Copy the ID (long string after `/d/`)
- Send to Gabe: "Spreadsheet ID: [paste]"

---

### ACTION 2: Populate Charts Sheet (30 min)

**Sheet: `Charts`**

Create headers in Row 1:
```
id | name | category | url | lastUpdated | description
```

Add sample data (at least 55 charts total across all categories):

**Wheat Futures (14 charts):**
```
WHEAT_SRW_D | SRW Wheat Daily | Wheat Futures | https://tradingnavigator.example.com/WHEAT_SRW_D.png | 2026-04-12T08:30:00Z | CBOT Soft Red Winter daily chart
WHEAT_SRW_W | SRW Wheat Weekly | Wheat Futures | https://tradingnavigator.example.com/WHEAT_SRW_W.png | 2026-04-12T08:30:00Z | Weekly trend analysis
...
```

**Spreads & Ratios (23 charts):**
```
SPREAD_SRW_KE | SRW vs HRW Spread | Spreads & Ratios | https://tradingnavigator.example.com/SPREAD_SRW_KE.png | 2026-04-12T08:30:00Z | CBOT SRW vs KCBT HRW
...
```

**Currencies (6 charts):**
```
DXY | Dollar Index | Currencies | https://tradingnavigator.example.com/DXY.png | 2026-04-12T08:30:00Z | U.S. Dollar Index
...
```

**Interest Rates (4 charts):**
**General Macro (13 charts):**

**Why:** The API groups charts by category automatically. Gabe tests that dashboard receives all 55+ charts organized by category.

---

### ACTION 3: Populate Quotes Sheet (15 min)

**Sheet: `Quotes`**

Create headers in Row 1:
```
contract | month | bid | ask | last | change | volume | timestamp
```

Add initial data (8-12 contracts):
```
ZWK25 | May 2025 | 545.25 | 545.75 | 545.50 | 2.25 | 124500 | 2026-04-12T08:30:00Z
ZWU25 | Jul 2025 | 548.75 | 549.25 | 549.00 | 2.50 | 98200 | 2026-04-12T08:30:00Z
KE (HRW) | May | 580.50 | 581.00 | 580.75 | 1.75 | 54300 | 2026-04-12T08:30:00Z
MWE (HRS) | May | 610.25 | 610.75 | 610.50 | 2.00 | 32100 | 2026-04-12T08:30:00Z
```

**Why:** The API calculates totalVolume, maxChange, minPrice, maxPrice automatically.  Gabe tests that these aggregations work.

---

### ACTION 4: Set BoR Status (5 min)

**Sheet: `BoR_Status`**

Create headers in Row 1:
```
phase | description | color
```

Set current phase in Row 2:
```
LOADED | Accumulation phase | #FFD700
```

**Allowed values:**
- `LOADED` (#FFD700 - gold)
- `LOCKED & LOADED` (#FF6B6B - red)
- `AIM` (#4ECDC4 - cyan)
- `FIRE` (#FF0000 - red)

**Why:** This is the market phase indicator. You update this weekly (or as market conditions change). It appears on the dashboard as a colored status badge.

---

### ACTION 5: Send Credentials to Gabe (5 min)

**Email Gabe:**
```
Ready for Phase 1 setup. Here are the Google Sheets credentials:

GOOGLE_SHEETS_ID: [your spreadsheet ID]

Also provide him with Google service account credentials - if you don't have one, 
create it at https://console.cloud.google.com/

The service account needs:
- Google Sheets API enabled
- Editor access to MarketBullets_Phase1_Data sheet
```

**Gabe receives:** Spreadsheet ID + service account JSON key

---

## Timeline

| Date | Your Action | Gabe's Action | Status |
|------|-------------|---------------|--------|
| Sat 4/12 | Finish by EOD | - | |
| Mon 4/15 | Sheet ready to access | Runs MONDAY_FIRST_STEPS | |
| Tue 4/16 | Monitor sheet access | Validates endpoints | |
| Thu 4/18 | Update BoR if needed | Tests production build | |
| Fri 4/19 | - | Deploys Phase 1 live | ✅ DONE |

---

## Critical Path Items

**You must complete by Monday 4/15 EOD:**
- [x] Google Sheet created
- [x] 4 sheets configured
- [x] Headers in all sheets
- [x] Sample data populated (minimum 55 charts, 8 quotes)
- [x] Credentials sent to Gabe

**If you miss Monday deadline:**
- Gabe stalls waiting for data
- Phase 1 slip by 3 days
- Send data by EOD Tuesday 4/16

---

## What You'll See on Dashboard (Week 2)

Once Gabe deploys, the member dashboard will:
1. Load all 55 charts from your Google Sheet
2. Display quotes in real-time (pulling from Quotes sheet)
3. Show market phase (LOADED/LOCKED & LOADED/AIM/FIRE) as status badge
4. Cache data for 60 seconds to prevent rate limiting

**You control all this** by editing the Google Sheet. No code changes needed.

---

## Your Weekly Rhythm (Phase 1+)

**Every Monday-Friday:**
- Check BoR_Status sheet - update `phase` if market conditions change
- Review Quotes sheet - update bid/ask/last/change/volume as you watch market
- Check dashboard - verify data appears correctly

**Every Quarter:**
- Review Charts sheet - add new charts if Trade Navigator exports new ones
- Archive retired charts - delete old ones

---

## Questions?

Contact: Gabe (CTO) for technical issues | Gary for strategy decisions

---

## Next Phase (Phase 2 - Frontend)

- **Timeline:** May 1 - June 15, 2026
- **Focus:** Astro-based member dashboard
- **Your role:** Provide design direction, review wireframes, finalize messaging

Stay tuned for Phase 2 brief.
