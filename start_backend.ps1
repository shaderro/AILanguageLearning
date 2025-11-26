# 启动后端FastAPI服务器
Write-Host "================================" -ForegroundColor Cyan
Write-Host "启动 FastAPI 后端服务器" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "服务器将在以下地址运行:" -ForegroundColor Yellow
Write-Host "  - API地址: http://localhost:8001" -ForegroundColor Green
Write-Host "  - Swagger文档: http://localhost:8001/docs" -ForegroundColor Green
Write-Host "  - 健康检查: http://localhost:8001/api/health" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动服务器
python frontend/my-web-ui/backend/main.py

