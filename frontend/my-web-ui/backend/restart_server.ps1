# 重启后端服务器脚本

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "🔄 重启后端服务器" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan

# 1. 查找并停止占用 8000 端口的进程
Write-Host "`n步骤1: 查找占用 8000 端口的进程..." -ForegroundColor Cyan
$connections = netstat -ano | Select-String ":8000.*LISTENING"
if ($connections) {
    $connections | ForEach-Object {
        $line = $_.Line
        if ($line -match '\s+(\d+)\s*$') {
            $pid = $Matches[1]
            Write-Host "  找到进程 PID: $pid" -ForegroundColor Yellow
            try {
                Stop-Process -Id $pid -Force
                Write-Host "  ✅ 已停止进程 $pid" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ 停止进程失败: $_" -ForegroundColor Red
            }
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  ℹ️ 没有找到占用 8000 端口的进程" -ForegroundColor Gray
}

# 2. 启动新的服务器
Write-Host "`n步骤2: 启动新的服务器..." -ForegroundColor Cyan
Write-Host "  服务器日志将在下方显示..." -ForegroundColor Gray
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# 启动服务器
python server.py 