# Run this script ONCE (as yourself, no elevation needed) to register the
# daily report task in Windows Task Scheduler.

$scriptPath = "C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\tools\daily_report.ps1"
$taskName   = "MarketBullets-DailyReport"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""

$trigger  = New-ScheduledTaskTrigger -Daily -At "05:00AM"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Remove existing task if present, then register fresh
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force

Write-Host ""
Write-Host "Task registered: '$taskName'"
Write-Host "Runs daily at 05:00 AM"
Write-Host "Report location: C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\devlogs\reports\"
Write-Host "Convos location: C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\devlogs\convorecords\"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  -- or --"
Write-Host "  powershell -File `"$scriptPath`""
