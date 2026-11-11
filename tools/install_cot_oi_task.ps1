$root = Split-Path -Parent $PSScriptRoot
# Run this script ONCE (as yourself, no elevation needed) to register the
# weekly Price vs. Open Interest chart in Windows Task Scheduler.
#
# The CFTC posts the COT report Fridays at 12:30 PM Pacific (later after a federal
# holiday). The task checks twice a day; the script does nothing unless there is a
# new report, so the auto-commit watcher only pushes the PNG once a week.

$batPath  = "$root\tools\cot\cot_oi_chart.bat"
$taskName = "MarketBullets-COT-OI-Chart"

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batPath`""

$triggers = @(
    (New-ScheduledTaskTrigger -Daily -At "12:50PM"),
    (New-ScheduledTaskTrigger -Daily -At "09:00PM")
)
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $triggers `
    -Settings $settings `
    -RunLevel Limited `
    -Force

Write-Host ""
Write-Host "Task registered: '$taskName'"
Write-Host "Checks daily at 12:50 PM and 9:00 PM; publishes only when the CFTC has a new report"
Write-Host "Writes:  $root\charts\COT_SRW_OI_W.png  (watcher pushes it)"
Write-Host "Data:    $root\data\cot\COT_SRW_OI_history.csv"
Write-Host "Log:     $root\tools\cot\cot_oi.log"
Write-Host ""
Write-Host "To run immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
