import os

content = r'''# ── Code Analyzer Unified Launcher ──────────────────
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Starting services..." -ForegroundColor Cyan

# 1. Start Backend
$backendJob = Start-Process -FilePath "$Root\backend\Analyzer.exe" -WorkingDirectory "$Root\backend" -PassThru -NoNewWindow
Write-Host "  [OK] Backend started (PID: $($backendJob.Id))" -ForegroundColor Green

# 2. Start Frontend
$frontendJob = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$Root\frontend" -PassThru -NoNewWindow
Write-Host "  [OK] Frontend started (PID: $($frontendJob.Id))" -ForegroundColor Green

# 3. Start MCP Server (codebase context layer)
$mcpJob = Start-Process -FilePath "python" -ArgumentList "$Root\analyzer\mcp_server.py --http --port 8892" -WorkingDirectory "$Root\analyzer" -PassThru -NoNewWindow
Write-Host "  [OK] MCP Server started on :8892 (PID: $($mcpJob.Id))" -ForegroundColor Green

# 4. Start UI/UX Flask Server (for VS Code Extension)
$flaskJob = Start-Process -FilePath "python" -ArgumentList "$Root\analyzer\analysis_server.py" -WorkingDirectory "$Root\analyzer" -PassThru -NoNewWindow
Write-Host "  [OK] Flask Server started on :7891 (PID: $($flaskJob.Id))" -ForegroundColor Green

Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow

try {
    while ($true) {
        if ($backendJob.HasExited) { break }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    if ($null -ne $backendJob -and -not $backendJob.HasExited) { Stop-Process -Id $backendJob.Id -Force }
    if ($null -ne $frontendJob -and -not $frontendJob.HasExited) { Stop-Process -Id $frontendJob.Id -Force }
    if ($null -ne $mcpJob -and -not $mcpJob.HasExited) { Stop-Process -Id $mcpJob.Id -Force }
    if ($null -ne $flaskJob -and -not $flaskJob.HasExited) { Stop-Process -Id $flaskJob.Id -Force }
    Get-Process -Name "node", "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "All stopped." -ForegroundColor Cyan
}
'''

with open('start.ps1', 'w', encoding='utf-8') as f:
    f.write(content.replace('\r\n', '\n'))
