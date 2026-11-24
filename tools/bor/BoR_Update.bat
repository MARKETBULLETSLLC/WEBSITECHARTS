@echo off
:: MarketBullets — BoR Update (PREVIEW)
:: 1. In Trade Navigator, copy the data table (optionally type instruction lines above it).
:: 2. Double-click this file. Chart + review sheet land in M:\preview.
:: Live publishing (charts\WHEAT_SRW_BOR_D.png) is not enabled yet.
:: %~dp0 = this file's own folder, so the path survives any future folder move.
python "%~dp0bor_update.py"
if errorlevel 1 (
    echo.
    echo BoR update FAILED - see message above. Nothing was changed.
    pause
    exit /b 1
)
for /f "delims=" %%f in ('dir /b /o-d "M:\preview\review-*.html"') do (
    start "" "M:\preview\%%f"
    goto :done
)
:done
