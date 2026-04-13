# BLOCKING ISSUES RESOLVED — ACTION REQUIRED FROM GARY

**Status**: Two blocking issues resolved and documented  
**Next Owner**: Gary Hofer  
**Timeline**: Complete by Friday April 18, 2026  
**Impact**: Blocks dashboard launch without these actions

---

## Issue #1: FIN_ vs AGI_ Naming Convention ✅ RESOLVED

### Decision: Option B — Standardize on FIN_ prefix
- **Why**: Existing files (FIN_DE_D.png, FIN_HD_D.png) have permanent embed codes in Squarespace
- **Constraint**: Cannot rename files without breaking website embeds (per CLAUDE.md)
- **Solution**: Update spreadsheet to use FIN_ naming instead

### Gary's Action Required:
Update `MarketBullets_Master_Chart_Index.csv`:
- **Row 72**: Change `AGI_HD_D` → `FIN_HD_D` (file exists ✓)
- **Row 73**: Change `AGI_DE_D` → `FIN_DE_D` (file exists ✓)
- **Row 74**: Change `AGI_CAT_D` → `FIN_CAT_D` (new export needed)

### Export Required:
- [ ] **FIN_CAT_D.png** (Caterpillar Daily) from Trade Navigator

**Time to complete**: 5-10 minutes

---

## Issue #2: Missing Chart Files ✅ PRIORITIZED AND PLANNED

### Summary:
11 chart PNG files need to be exported from Trade Navigator before dashboard can launch.

### Critical Path (Tier 1 — Must Have):
**5 wheat contract charts** — 15 minutes  
Dashboard won't look complete without these:
- [ ] WHEAT_HRW_D.png (Kansas City HRW Daily)
- [ ] WHEAT_HRW_M.png (Kansas City HRW Monthly)
- [ ] WHEAT_HRS_D.png (Minneapolis HRS Daily)
- [ ] WHEAT_HRS_M.png (Minneapolis HRS Monthly)
- [ ] WHEAT_FWH_M.png (Paris 11% Milling Wheat Monthly)

### High Priority (Tier 2 — Should Have):
**4 additional charts** — 15 minutes
- [ ] SPD_HRW_H_K.png (Kansas City Spreads)
- [ ] NRG_CL_W.png (Crude Oil Weekly)
- [ ] NRG_HO_W.png (Heating Oil Weekly)
- [ ] NRG_HO_M.png (Heating Oil Monthly)

### Medium Priority (Tier 3 — Nice to Have):
**2 additional charts** — 10 minutes
- [ ] METL_SI_M.png (Silver Monthly)
- [ ] FIN_CAT_D.png (Caterpillar Daily — categorized as FIN_ per Decision #1)

### Total Time: 40 minutes for all 11 exports

**For detailed export instructions, see**: [MISSING_EXPORTS_ACTION_PLAN.md](MISSING_EXPORTS_ACTION_PLAN.md)

---

## Downstream Impact

| If Gary Completes | Then Gabe Can | Result |
|---|---|---|
| Naming fix only | ✅ Deploy API | API works, but missing 3 ag indices |
| Tier 1 exports only | ✅ Deploy dashboard | Dashboard launches, 6/11 charts present |
| Tier 1 + Tier 2 | ✅ Full dashboard launch | All core functionality ready |
| All 11 exports | ✅ Dashboard + polish | 100% feature complete |

---

## How to Export (Quick Reference)

1. Open Trade Navigator
2. Load chart (e.g., "Kansas City HRW Daily")
3. Export as PNG
4. Name file **exactly** as shown in checklists above (case-sensitive)
5. Save to: `c:/Users/hofer/OneDrive/Documents/GitHub/ClonerMarketbulletsllc/WEBSITECHARTS/`
6. Repeat for each file

After exporting:
```bash
git add WEBSITECHARTS/*.png
git commit -m "Add missing chart exports"
git push
```

---

## Verification Checklist

After exporting, verify all files exist:
```bash
# From WEBSITECHARTS folder
ls WHEAT_HRW_D.png WHEAT_HRW_M.png WHEAT_HRS_D.png WHEAT_HRS_M.png WHEAT_FWH_M.png
ls SPD_HRW_H_K.png NRG_CL_W.png NRG_HO_W.png NRG_HO_M.png METL_SI_M.png FIN_CAT_D.png
```

If all files exist: ✅ Ready for Gabe to deploy

---

## Document References

- [NAMING_CONVENTION_DECISION_NEEDED.txt](NAMING_CONVENTION_DECISION_NEEDED.txt) — Full naming decision details
- [MISSING_FILES_TO_EXPORT.txt](MISSING_FILES_TO_EXPORT.txt) — Original issue tracking
- [MISSING_EXPORTS_ACTION_PLAN.md](MISSING_EXPORTS_ACTION_PLAN.md) — Detailed tier-by-tier export plan

---

**Status Updated**: April 7, 2026  
**Owner**: Gary Hofer  
**Timeline**: Complete Tier 1 by Wednesday, all tiers by Friday  
**Next Step**: After exports complete, notify Gabe "Charts ready for dashboard"
