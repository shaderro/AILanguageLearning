# 清理占用8000端口的进程
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   清理端口 8000 占用" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$port = 8000

# 检查端口是否被占用
Write-Host "检查端口 $port..." -ForegroundColor Yellow
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    $pids = $connection.OwningProcess | Select-Object -Unique
    foreach ($pid in $pids) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  发现进程: $($process.ProcessName) (PID: $pid)" -ForegroundColor Red
            Write-Host "  正在关闭..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] 进程已关闭" -ForegroundColor Green
        }
    }
    
    # 等待端口释放
    Write-Host "  等待端口释放..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    # 再次检查
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "  [WARNING] 端口可能仍在占用中" -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] 端口 $port 已释放" -ForegroundColor Green
    }
} else {
    Write-Host "  [OK] 端口 $port 未被占用" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

