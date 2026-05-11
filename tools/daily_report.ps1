# MarketBullets Daily Report Generator
# Scheduled via Windows Task Scheduler -- runs at 05:00 AM daily
# Output: docs/reports/report-YYYY-MM-DD.html
# Convos:  docs/convorecords/YYYY-MM-DD-<session-id>.txt

param(
    [datetime]$ReportDate = (Get-Date)
)

$projectRoot = "C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS"
$reportsDir  = "$projectRoot\devlogs\reports"
$convoDir    = "$projectRoot\devlogs\convorecords"
$claudeDir   = "C:\Users\hofer\.claude\projects\c--Users-hofer-OneDrive-Documents-GitHub-WEBSITECHARTS"

$dateStr = $ReportDate.ToString("yyyy-MM-dd")
$cutoff  = $ReportDate.AddHours(-24)

New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
New-Item -ItemType Directory -Force -Path $convoDir   | Out-Null

# -- 1. Collect project files modified in the last 24 hours ----------------
$skipSegments = @('.git', 'reports', 'convorecords')

$modifiedFiles = Get-ChildItem -Recurse -Path $projectRoot -File -ErrorAction SilentlyContinue |
    Where-Object {
        if ($_.LastWriteTime -lt $cutoff) { return $false }
        $parts = $_.FullName.Split([IO.Path]::DirectorySeparatorChar)
        foreach ($seg in $skipSegments) {
            if ($parts -contains $seg) { return $false }
        }
        return $true
    } |
    Sort-Object LastWriteTime -Descending

# -- 2. Convert Claude JSONL sessions to plain text in convorecords/ --------
$sessionLinks = @()

if (Test-Path $claudeDir) {
    $sessionFiles = Get-ChildItem -Path $claudeDir -Filter "*.jsonl" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $cutoff }

    foreach ($sf in $sessionFiles) {
        $txtName = "$dateStr-$($sf.BaseName).txt"
        $txtPath = "$convoDir\$txtName"

        $rawLines = Get-Content $sf.FullName -ErrorAction SilentlyContinue
        if (-not $rawLines) { continue }

        $out = [System.Collections.Generic.List[string]]::new()
        $out.Add("MarketBullets - Claude Conversation Record")
        $out.Add("Session : $($sf.BaseName)")
        $out.Add("Date    : $dateStr")
        $out.Add("=" * 70)
        $out.Add("")

        foreach ($line in $rawLines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            try {
                $msg = $line | ConvertFrom-Json -ErrorAction Stop
            } catch { continue }

            if ($msg.type -notin @("user", "assistant")) { continue }

            $role = $msg.type.ToUpper()
            $ts   = if ($msg.timestamp) { " [$($msg.timestamp)]" } else { "" }
            $out.Add("-- $role$ts --")

            $content = $msg.message.content

            if ($null -eq $content) {
                # nothing
            } elseif ($content -is [string]) {
                $out.Add($content)
            } else {
                foreach ($block in $content) {
                    $btype = $block.type
                    if ($btype -eq "text") {
                        $out.Add($block.text)
                    } elseif ($btype -eq "tool_use") {
                        $out.Add("[Tool call: $($block.name)]")
                    }
                }
            }
            $out.Add("")
            $out.Add("-" * 50)
            $out.Add("")
        }

        $out | Out-File -FilePath $txtPath -Encoding utf8 -Force

        $sessionLinks += [PSCustomObject]@{
            TxtName  = $txtName
            Modified = $sf.LastWriteTime
        }
    }
}

# -- 3. Build HTML report ---------------------------------------------------
$now = Get-Date -Format "HH:mm"

function Format-Size($bytes) {
    if ($bytes -gt 1MB) { return "$([math]::Round($bytes / 1MB, 1)) MB" }
    if ($bytes -gt 1KB) { return "$([math]::Round($bytes / 1KB, 1)) KB" }
    return "$bytes B"
}

if ($modifiedFiles.Count -gt 0) {
    $fileRows = $modifiedFiles | ForEach-Object {
        $rel  = $_.FullName.Replace($projectRoot + "\", "").Replace("\", "/")
        $href = "file:///" + $_.FullName.Replace("\", "/")
        $time = $_.LastWriteTime.ToString("HH:mm")
        $size = Format-Size $_.Length
        "<tr><td><a href='$href'>$rel</a></td><td class='ext'>$($_.Extension)</td><td class='ts'>$time</td><td class='ts'>$size</td></tr>"
    }
} else {
    $fileRows = @("<tr><td colspan='4' class='empty'>No files modified in the last 24 hours.</td></tr>")
}

if ($sessionLinks.Count -gt 0) {
    $convoRows = $sessionLinks | ForEach-Object {
        $href = "../convorecords/$($_.TxtName)"
        "<tr><td><a href='$href'>$($_.TxtName)</a></td><td class='ts'>$($_.Modified.ToString('HH:mm'))</td></tr>"
    }
} else {
    $convoRows = @("<tr><td colspan='2' class='empty'>No Claude sessions recorded in the last 24 hours.</td></tr>")
}

$fileRowsHtml  = $fileRows  -join "`n  "
$convoRowsHtml = $convoRows -join "`n  "

$css = @"
  :root {
    --gold:  #D4A051;
    --amber: #D4A574;
    --blue:  #B8C5D6;
    --bg:    #1a1a1a;
    --line:  #2e2e2e;
    --text:  #F5F5F0;
    --dim:   #888;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Georgia, 'Times New Roman', serif; background: var(--bg);
         color: var(--text); padding: 2rem 2.5rem; line-height: 1.6; }
  header { border-bottom: 2px solid var(--gold); padding-bottom: 1rem; margin-bottom: 2rem; }
  header h1 { color: var(--gold); font-size: 1.4rem; letter-spacing: 0.04em; }
  header .meta { color: var(--blue); font-size: 0.85rem; margin-top: 0.25rem; }
  h2 { color: var(--gold); font-size: 0.85rem; letter-spacing: 0.08em;
       text-transform: uppercase; border-left: 3px solid var(--gold);
       padding-left: 0.65rem; margin: 2rem 0 0.75rem; }
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  th { text-align: left; color: var(--blue); padding: 0.4rem 0.6rem;
       border-bottom: 1px solid var(--gold); font-family: 'Trebuchet MS', sans-serif;
       font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; }
  td { padding: 0.35rem 0.6rem; border-bottom: 1px solid var(--line); vertical-align: middle; }
  tr:hover td { background: #252525; }
  a { color: var(--amber); text-decoration: none; }
  a:hover { color: var(--gold); text-decoration: underline; }
  .ts   { color: var(--dim); font-size: 0.8rem; font-family: monospace; white-space: nowrap; }
  .ext  { color: var(--blue); font-size: 0.8rem; font-family: monospace; }
  .empty { color: var(--dim); font-style: italic; padding: 0.6rem 0; }
  footer { margin-top: 3rem; color: var(--dim); font-size: 0.75rem;
           border-top: 1px solid var(--line); padding-top: 0.75rem;
           font-family: 'Trebuchet MS', sans-serif; }
"@

$html = "<!DOCTYPE html>`n<html lang=`"en`">`n<head>`n"
$html += "<meta charset=`"UTF-8`">`n"
$html += "<meta name=`"viewport`" content=`"width=device-width, initial-scale=1.0`">`n"
$html += "<title>MarketBullets Daily Report $dateStr</title>`n"
$html += "<style>`n$css`n</style>`n</head>`n<body>`n"
$html += "<header>`n  <h1>MarketBullets &mdash; Daily Activity Report</h1>`n"
$html += "  <div class=`"meta`">$dateStr &nbsp;&bull;&nbsp; Generated $now</div>`n</header>`n"
$html += "<h2>Files Modified &mdash; Last 24 Hours</h2>`n"
$html += "<table>`n  <tr><th>Path</th><th>Type</th><th>Time</th><th>Size</th></tr>`n"
$html += "  $fileRowsHtml`n</table>`n"
$html += "<h2>Claude Session Records</h2>`n"
$html += "<table>`n  <tr><th>Transcript</th><th>Last Active</th></tr>`n"
$html += "  $convoRowsHtml`n</table>`n"
$html += "<footer>MarketBullets LLC &nbsp;&bull;&nbsp; Auto-generated by daily_report.ps1</footer>`n"
$html += "</body>`n</html>"

$reportPath = "$reportsDir\report-$dateStr.html"
[System.IO.File]::WriteAllText($reportPath, $html, [System.Text.Encoding]::UTF8)

Write-Host "Report saved : $reportPath"
Write-Host "Files listed : $($modifiedFiles.Count)"
Write-Host "Sessions exported : $($sessionLinks.Count)"
