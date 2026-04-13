@echo off
REM MarketBullets — End-of-Day Futures Report
REM Schedule via Task Scheduler at 3:15 PM CT Mon-Fri
REM Action: Start a program → this .bat file

cd /d "c:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS"
python tools\eod_futures_report.py >> tools\eod_reports\eod_runner.log 2>&1
