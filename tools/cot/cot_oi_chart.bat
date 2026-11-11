@echo off
:: MarketBullets — Chicago SRW Price vs. Open Interest (charts\COT_SRW_OI_W.png)
:: Run by Task Scheduler. Exits quietly unless the CFTC has a new weekly report.
:: Double-click to check by hand; add --force to rebuild regardless.
cd /d "%~dp0\..\.."
python -X utf8 tools\cot\cot_oi_chart.py %*
