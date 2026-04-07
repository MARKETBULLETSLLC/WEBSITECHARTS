# CASE SENSITIVITY RENAMES NEEDED
# Run these commands in Git (NOT file system) to fix casing:

## WHEAT FILES (SrW → SRW standardization)
git mv WHEAT_SrW_BOR_D.png WHEAT_SRW_BOR_D.png
git mv WHEAT_SrW_D.png WHEAT_SRW_D.png
git mv WHEAT_SrW_W.png WHEAT_SRW_W.png
git mv WHEAT_SrW_M.png WHEAT_SRW_M.png
git mv WHEAT_SrW_Special_M.png WHEAT_SRW_Special_M.png
git mv WHEAT_SrW_A.png WHEAT_SRW_A.png

## INTRA-MARKET SPREADS (SrW → SRW in SPD names)
git mv SPD_SrW_H_K.png SPD_SRW_H_K.png
git mv SPD_SrW_K_N.png SPD_SRW_K_N.png
git mv SPD_SrW_N_U.png SPD_SRW_N_U.png
git mv SPD_SrW_U_Z.png SPD_SRW_U_Z.png
git mv SPD_SrW_Z_H2.png SPD_SRW_Z_H2.png

## GRAINS (lowercase w → uppercase W)
git mv GRAIN_C_w.png GRAIN_C_W.png

## COMMIT
git commit -m "Standardize chart filename casing for case-sensitive systems"
