@echo off
:: MarketBullets — Word Commentary Publisher
:: Double-click to run in a window (shows what it publishes).
:: To start it silently at every login instead, run tools\install_word_watcher_task.ps1 once.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" tools\word_commentary.py
) else (
    python tools\word_commentary.py
)
pause
