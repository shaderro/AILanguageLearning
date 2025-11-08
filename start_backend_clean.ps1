# 智能启动后端服务器脚本
# 自动检查并清理端口占用

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   启动后端服务器（智能版）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$port = 8001

# 检查端口是否被占用
Write-Host "[1/3] 检查端口 $port..." -ForegroundColor Yellow
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    $pid = $connection.OwningProcess | Select-Object -First 1
    Write-Host "  发现进程 PID: $pid 正在占用端口 $port" -ForegroundColor Red
    Write-Host "  正在关闭旧进程..." -ForegroundColor Yellow
    
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] 旧进程已关闭" -ForegroundColor Green
    
    # 等待端口释放
    Write-Host "  等待端口释放..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} else {
    Write-Host "  [OK] 端口 $port 可用" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] 启动服务器..." -ForegroundColor Yellow
Write-Host "  服务器地址: http://localhost:$port" -ForegroundColor Cyan
Write-Host "  Swagger 文档: http://localhost:${port}/docs" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

Write-Host "[3/3] 运行中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动服务器
python frontend/my-web-ui/backend/main.py
