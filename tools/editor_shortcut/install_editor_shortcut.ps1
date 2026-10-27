# MarketBullets - Commentary Editor shortcut installer (all users)
# Creates "MB Commentary Editor" in the all-users Start Menu and on the Public
# Desktop. Each user then right-clicks it -> "Pin to taskbar" (Windows does not
# let scripts pin to another user's taskbar).
# Run: right-click -> Run with PowerShell (it asks for admin). Re-run any time
# the repo moves; it overwrites the old shortcuts.

$ErrorActionPreference = 'Stop'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  exit
}

$repo   = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$editor = Join-Path $repo 'commentary\editor.html'
$icon   = Join-Path $PSScriptRoot 'editor.ico'
$url    = ([Uri]$editor).AbsoluteUri

$browser = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) { throw 'Neither Chrome nor Edge found.' }

$targets = @(
  (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\MB Commentary Editor.lnk'),
  (Join-Path $env:PUBLIC 'Desktop\MB Commentary Editor.lnk')
)
$shell = New-Object -ComObject WScript.Shell
foreach ($lnkPath in $targets) {
  $lnk = $shell.CreateShortcut($lnkPath)
  $lnk.TargetPath       = $browser
  $lnk.Arguments        = "`"$url`""
  $lnk.WorkingDirectory = Split-Path $editor
  $lnk.IconLocation     = "$icon,0"
  $lnk.Description      = 'MarketBullets Commentary Editor'
  $lnk.Save()
  Write-Host "Created $lnkPath"
}
Write-Host ''
Write-Host 'Done. Each user: Start menu -> "MB Commentary Editor" -> right-click -> Pin to taskbar.'
if ($Host.Name -eq 'ConsoleHost') { Read-Host 'Press Enter to close' }
