# ── Code Analyzer Unified Launcher ──────────────────
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
    Get-Process -Name "node", "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "All stopped." -ForegroundColor Cyan
}
