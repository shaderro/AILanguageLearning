# 查找并终止占用端口 8000 的进程

Write-Host "🔍 查找占用端口 8000 的进程..." -ForegroundColor Yellow

# 使用 netstat 查找占用端口的进程
$connections = netstat -ano | Select-String ":8000"

if ($connections) {
    Write-Host "`n找到以下连接:" -ForegroundColor Cyan
    $connections | ForEach-Object { Write-Host $_.Line }
    
    # 提取 PID
    $pids = $connections | ForEach-Object {
        if ($_ -match '\s+(\d+)$') {
            $matches[1]
        }
    } | Select-Object -Unique
    
    if ($pids) {
        Write-Host "`n找到进程 ID (PID): $($pids -join ', ')" -ForegroundColor Yellow
        
        foreach ($pid in $pids) {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "`n进程信息:" -ForegroundColor Cyan
                    Write-Host "  PID: $($process.Id)"
                    Write-Host "  名称: $($process.ProcessName)"
                    Write-Host "  路径: $($process.Path)"
                    
                    # 询问是否终止
                    $confirm = Read-Host "`n是否终止此进程? (Y/N)"
                    if ($confirm -eq 'Y' -or $confirm -eq 'y') {
                        Stop-Process -Id $pid -Force
                        Write-Host "✅ 已终止进程 PID: $pid" -ForegroundColor Green
                    } else {
                        Write-Host "⏭️  跳过进程 PID: $pid" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "⚠️  进程 PID $pid 不存在或已终止" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "❌ 终止进程 PID $pid 时出错: $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "⚠️  无法提取进程 ID" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ 端口 8000 未被占用" -ForegroundColor Green
}

Write-Host "`n完成！" -ForegroundColor Cyan
