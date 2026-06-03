# Run this script ONCE to register the auto-commit watcher in Windows Task Scheduler.
# It will start automatically at login and run silently in the background.

$batPath  = "C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\tools\auto_commit_watcher.bat"
$taskName = "MarketBullets-ChartWatcher"

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batPath`""

$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$principal = New-ScheduledTaskPrincipal -UserId $env:USERDOMAIN\$env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Force

Write-Host ""
Write-Host "Task registered: '$taskName'"
Write-Host "Starts automatically at login."
Write-Host "Watches: C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\charts"
Write-Host "Log:     C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\tools\auto_commit.log"
Write-Host ""
Write-Host "Starting watcher now..."
Start-ScheduledTask -TaskName $taskName
Write-Host "Done."
