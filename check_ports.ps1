# 检查端口使用情况
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Port Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查8000端口
Write-Host "[Port 8000] Frontend Debug Server" -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $pid = $port8000.OwningProcess | Select-Object -First 1
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    Write-Host "  [RUNNING] PID: $pid" -ForegroundColor Green
    Write-Host "  Process: $($process.ProcessName)" -ForegroundColor Green
    Write-Host "  To stop: Stop-Process -Id $pid -Force" -ForegroundColor Yellow
} else {
    Write-Host "  [FREE] Not in use" -ForegroundColor Gray
}

Write-Host ""

# 检查8001端口
Write-Host "[Port 8001] Backend API Server (with database)" -ForegroundColor Yellow
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($port8001) {
    $pid = $port8001.OwningProcess | Select-Object -First 1
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    Write-Host "  [RUNNING] PID: $pid" -ForegroundColor Green
    Write-Host "  Process: $($process.ProcessName)" -ForegroundColor Green
    Write-Host "  To stop: Stop-Process -Id $pid -Force" -ForegroundColor Yellow
} else {
    Write-Host "  [FREE] Not in use" -ForegroundColor Gray
}

Write-Host ""

# 检查5173端口（Vite前端）
Write-Host "[Port 5173] Frontend UI (Vite)" -ForegroundColor Yellow
$port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($port5173) {
    $pid = $port5173.OwningProcess | Select-Object -First 1
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    Write-Host "  [RUNNING] PID: $pid" -ForegroundColor Green
    Write-Host "  Process: $($process.ProcessName)" -ForegroundColor Green
} else {
    Write-Host "  [FREE] Not in use" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Recommended setup:" -ForegroundColor Yellow
Write-Host "  - Port 8001: Backend API (use this for vocab database)" -ForegroundColor Green
Write-Host "  - Port 5173: Frontend UI" -ForegroundColor Green
Write-Host ""

