@echo off
REM Preview the newest commentary draft in the browser (local only, nothing is published)
cd /d "%~dp0"
python tools\preview_draft.py %*
if errorlevel 1 pause
