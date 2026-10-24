$root = Split-Path -Parent $PSScriptRoot
# Run this script ONCE on the PC where Gary writes the commentary.
# Registers the Word commentary publisher in Task Scheduler: starts at login,
# runs silently (pythonw, no window). Log: tools\word_commentary.log

$taskName = "MarketBullets-WordCommentary"
$script   = "$root\tools\word_commentary.py"

# Prefer the repo's .venv; fall back to whatever pythonw is on PATH.
$pythonw = "$root\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $pythonw) -or -not (& "$root\.venv\Scripts\python.exe" -c "print(1)" 2>$null)) {
    $pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
}
if (-not $pythonw) {
    Write-Host "Python not found. Install it first:  winget install Python.Python.3.13" -ForegroundColor Red
    exit 1
}

$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $root

$trigger  = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host ""
Write-Host "Task registered: '$taskName'"
Write-Host "Starts automatically at login, no window."
Write-Host "Python:  $pythonw"
Write-Host "Watches: $root\commentary  (YYYY-MM-DD.docx)"
Write-Host "Log:     $root\tools\word_commentary.log"
Write-Host ""
Write-Host "Starting it now..."
Start-ScheduledTask -TaskName $taskName
Write-Host "Done. To remove it:  Unregister-ScheduledTask -TaskName $taskName"
