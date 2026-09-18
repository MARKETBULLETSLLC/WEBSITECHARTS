# Run this script ONCE (as yourself, no elevation needed) to register the
# nightly cost-benchmark snapshot in Windows Task Scheduler.

$batPath  = "C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\tools\cost_snapshot.bat"
$taskName = "MarketBullets-CostSnapshot"

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batPath`""

$trigger  = New-ScheduledTaskTrigger -Daily -At "02:15AM"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

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
Write-Host "Runs daily at 02:15 AM"
Write-Host "Writes:  C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\data\cost-history.json"
Write-Host "Log:     C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\tools\cost_snapshot.log"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  -- or --"
Write-Host "  python tools\cost_snapshot.py"
