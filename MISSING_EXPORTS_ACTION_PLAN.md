# Missing Chart Exports — Prioritized Action Plan

**Total**: 11 files to export from Trade Navigator  
**Owner**: Gary Hofer  
**Timeline**: Before Friday April 18, 2026 (dashboard launch)

---

## PRIORITY TIER 1 — CRITICAL (Members Dashboard Core)
**Impact**: Without these, members dashboard is incomplete  
**Time**: ~15 minutes for all 5 files

### Wheat Contracts (5 files) — MEMBERS DASHBOARD CORE
1. **WHEAT_HRW_D.png** — Kansas City HRW Daily
   - Export from Trade Navigator as: `WHEAT_HRW_D.png`
   - Save to: `/WEBSITECHARTS/WHEAT_HRW_D.png`
   - Used in: Members dashboard · HRW tab · Daily chart slot

2. **WHEAT_HRW_M.png** — Kansas City HRW Monthly  
   - Export from Trade Navigator as: `WHEAT_HRW_M.png`
   - Save to: `/WEBSITECHARTS/WHEAT_HRW_M.png`
   - Used in: Members dashboard · HRW tab · Monthly chart slot

3. **WHEAT_HRS_D.png** — Minneapolis HRS Daily
   - Export from Trade Navigator as: `WHEAT_HRS_D.png`
   - Save to: `/WEBSITECHARTS/WHEAT_HRS_D.png`
   - Used in: Members dashboard · HRS tab · Daily chart slot

4. **WHEAT_HRS_M.png** — Minneapolis HRS Monthly
   - Export from Trade Navigator as: `WHEAT_HRS_M.png`
   - Save to: `/WEBSITECHARTS/WHEAT_HRS_M.png`
   - Used in: Members dashboard · HRS tab · Monthly chart slot

5. **WHEAT_FWH_M.png** — Paris 11% Milling Wheat Monthly
   - Export from Trade Navigator as: `WHEAT_FWH_M.png`
   - Save to: `/WEBSITECHARTS/WHEAT_FWH_M.png`
   - Used in: Members dashboard · FWH tab · Monthly chart slot

---

## PRIORITY TIER 2 — HIGH (Chart Gallery Completeness)
**Impact**: Gallery looks sparse, but members can still access main signals  
**Time**: ~10 minutes for all 4 files

### Spreads (1 file)
6. **SPD_HRW_H_K.png** — Kansas City HRW Mar/May Spread
   - Export from Trade Navigator as: `SPD_HRW_H_K.png`
   - Save to: `/WEBSITECHARTS/SPD_HRW_H_K.png`
   - Used in: Members dashboard · Spreads section
   - Note: This follows the SPD_ pattern; may already be in Trade Navigator

### Energy (3 files) — MACRO CONTEXT
7. **NRG_CL_W.png** — Crude Oil Weekly (macroeconomic context)
   - Export from Trade Navigator as: `NRG_CL_W.png`
   - Save to: `/WEBSITECHARTS/NRG_CL_W.png`

8. **NRG_HO_W.png** — Diesel/Heating Oil Weekly
   - Export from Trade Navigator as: `NRG_HO_W.png`
   - Save to: `/WEBSITECHARTS/NRG_HO_W.png`

9. **NRG_HO_M.png** — Diesel/Heating Oil Monthly
   - Export from Trade Navigator as: `NRG_HO_M.png`
   - Save to: `/WEBSITECHARTS/NRG_HO_M.png`

---

## PRIORITY TIER 3 — MEDIUM (Chart Gallery Polish)
**Impact**: Missing one metals chart, gallery still 99% complete  
**Time**: ~5 minutes

### Metals (1 file)
10. **METL_SI_M.png** — Silver Monthly
    - Export from Trade Navigator as: `METL_SI_M.png`
    - Save to: `/WEBSITECHARTS/METL_SI_M.png`

---

## PRIORITY TIER 4 — LOW (Agricultural Sector Indicators)
**Impact**: Optional; only if agricultural sector analysis is emphasize  
**Time**: ~5 minutes

### Financial/Agricultural Indices (1 file)
11. **FIN_CAT_D.png** — Caterpillar Daily (agricultural equipment sector)
    - Export from Trade Navigator as: `FIN_CAT_D.png` (per naming decision)
    - Save to: `/WEBSITECHARTS/FIN_CAT_D.png`
    - Note: Updates spreadsheet row 74 to "FIN_CAT_D"

---

## Recommended Export Order (Fastest Track)

1. Do **Tier 1 (all 5 wheat files)** first — 15 min → members dashboard functional
2. Add **Tier 2 spreads (1 file)** → 5 min → completes spread section  
3. Add **Tier 2 energy (3 files)** → 10 min → completes macro context
4. If time: **Tier 3 metals (1)** → 5 min → completes metals section
5. If time: **Tier 4 ag indices (1)** → 5 min → agricultural sector complete

**Total time: ~40 minutes for all 11 files**

---

## Export Workflow

1. Open Trade Navigator
2. For each chart listed above:
   - Load the EXACT chart or indicator
   - Export as PNG
   - Name file EXACTLY as shown (case-sensitive)
   - Save to `/WEBSITECHARTS/` folder
3. Commit to GitHub:
   ```bash
   git add WEBSITECHARTS/*.png
   git commit -m "Add missing chart exports (wheat, spreads, energy, metals, ag indices)"
   git push
   ```

---

## Verification After Export

After exporting all files, run:
```bash
# Verify all 11 files exist
ls -la WEBSITECHARTS/WHEAT_HRW*.png
ls -la WEBSITECHARTS/WHEAT_HRS*.png
ls -la WEBSITECHARTS/WHEAT_FWH_M.png
ls -la WEBSITECHARTS/SPD_HRW_H_K.png
ls -la WEBSITECHARTS/NRG_*.png
ls -la WEBSITECHARTS/METL_SI_M.png
ls -la WEBSITECHARTS/FIN_CAT_D.png
```

---

## Next Steps After Export

1. Regenerate MarketBullets_Master_Chart_Index.csv validation
2. Push exports to GitHub
3. Notify Gabe: "All chart exports complete — safe to deploy dashboard"
4. Deploy to Squarespace/Vercel

