# 启动前端开发服务器
Write-Host "================================" -ForegroundColor Cyan
Write-Host "启动前端开发服务器" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "正在切换到前端目录..." -ForegroundColor Yellow

# 切换到前端目录
Set-Location -Path "frontend\my-web-ui"

Write-Host ""
Write-Host "前端将在以下地址运行:" -ForegroundColor Yellow
Write-Host "  - 前端地址: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动前端
npm run dev

