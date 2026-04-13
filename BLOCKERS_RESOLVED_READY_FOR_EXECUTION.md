# MarketBullets Phase 1 — Blockers Ready for Resolution

**Date**: April 7, 2026  
**Status**: All blocking issues identified, prioritized, and documented  
**Next Action**: Gary executes chart exports (40 min) + spreadsheet update (5 min)

---

## What Was Just Resolved

Two blocking issues that prevent dashboard launch have been analyzed, decided, and documented:

### 1. Naming Convention Conflict (FIN_ vs AGI_)
✅ **DECISION MADE**: Use FIN_ prefix  
- Updated: [NAMING_CONVENTION_DECISION_NEEDED.txt](NAMING_CONVENTION_DECISION_NEEDED.txt)
- Rationale documented: permanent embed codes cannot change
- Spreadsheet updates required: 3 rows
- New export required: 1 file (FIN_CAT_D.png)

### 2. Missing Chart Files (11 total)
✅ **PRIORITIZED INTO 4 TIERS**:
- New: [MISSING_EXPORTS_ACTION_PLAN.md](MISSING_EXPORTS_ACTION_PLAN.md)
- Tier 1 (Critical): 5 wheat files — 15 min
- Tier 2 (High): 4 spreads/energy files — 15 min
- Tier 3 (Medium): 1 metals file — 5 min
- Tier 4 (Low): 1 ag index file — 5 min
- Total: ~45 minutes

### 3. Summary Document for Ready Reference
✅ **CREATED**: [BLOCKING_ISSUES_RESOLVED.md](BLOCKING_ISSUES_RESOLVED.md)
- One-page reference for Gary
- Checklists for each tier
- Impact analysis for downstream teams
- Verification steps

---

## Gary's Next Steps (45 minutes total)

### Step 1: Naming Convention Update (5 min)
1. Open `MarketBullets_Master_Chart_Index.csv`
2. Find rows 72-74
3. Change:
   - Row 72: `AGI_HD_D` → `FIN_HD_D`
   - Row 73: `AGI_DE_D` → `FIN_DE_D`
   - Row 74: `AGI_CAT_D` → `FIN_CAT_D`
4. Save CSV
5. Commit to Git

### Step 2: Export Tier 1 Charts (15 min) — CRITICAL
1. Open Trade Navigator
2. Export these 5 chats as PNG files with EXACT names:
   - WHEAT_HRW_D.png
   - WHEAT_HRW_M.png
   - WHEAT_HRS_D.png
   - WHEAT_HRS_M.png
   - WHEAT_FWH_M.png
3. Save to `WEBSITECHARTS/` folder
4. Commit to Git

### Step 3 (Optional): Export Tier 2-4 Charts (25 min)
- If time allows, export additional 6 charts per [MISSING_EXPORTS_ACTION_PLAN.md](MISSING_EXPORTS_ACTION_PLAN.md)
- Minimum viable: Complete Tier 1 only, do Tier 2-4 after dashboard launches

### Step 4: Notify Gabe
After all exports committed to GitHub:
```
"Charts ready — all Tier 1 exports complete. Dashboard can launch."
```

---

## Gabe's Status (When Gary Completes)

Once Gary finishes Step 2 (Tier 1 exports):
- ✅ API backend is production-ready
- ✅ Google Sheets integration configured
- ✅ Documentation complete
- ✅ Chart exports arriving
- 👉 **Can proceed with dashboard deployment**

---

## Files Updated/Created This Session

| File | Action | Purpose |
|---|---|---|
| [NAMING_CONVENTION_DECISION_NEEDED.txt](NAMING_CONVENTION_DECISION_NEEDED.txt) | Updated | Decision documented: FIN_ prefix selected |
| [MISSING_EXPORTS_ACTION_PLAN.md](MISSING_EXPORTS_ACTION_PLAN.md) | Created | Prioritized tier-by-tier export plan |
| [BLOCKING_ISSUES_RESOLVED.md](BLOCKING_ISSUES_RESOLVED.md) | Created | One-page ready reference for Gary |

---

## Quick Reference Checklists

### Naming Convention Update
- [ ] Open MarketBullets_Master_Chart_Index.csv
- [ ] Update row 72: AGI_HD_D → FIN_HD_D
- [ ] Update row 73: AGI_DE_D → FIN_DE_D
- [ ] Update row 74: AGI_CAT_D → FIN_CAT_D
- [ ] Save and commit

### Export Tier 1 (Minimum Required)
- [ ] WHEAT_HRW_D.png
- [ ] WHEAT_HRW_M.png
- [ ] WHEAT_HRS_D.png
- [ ] WHEAT_HRS_M.png
- [ ] WHEAT_FWH_M.png

### Export Tiers 2-4 (If Time)
- [ ] SPD_HRW_H_K.png (Tier 2)
- [ ] NRG_CL_W.png (Tier 2)
- [ ] NRG_HO_W.png (Tier 2)
- [ ] NRG_HO_M.png (Tier 2)
- [ ] METL_SI_M.png (Tier 3)
- [ ] FIN_CAT_D.png (Tier 4)

---

**These issues are now ready for Gary to execute.**  
**Estimated completion**: 45 minutes  
**Unblocks**: Full dashboard deployment for Gabe  

