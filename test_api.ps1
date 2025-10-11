# 测试API是否正常工作
Write-Host "================================" -ForegroundColor Cyan
Write-Host "测试 Vocab API" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 测试健康检查
Write-Host "[1] 测试健康检查..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method Get
    Write-Host "  [OK] 服务器健康状态: $($response.status)" -ForegroundColor Green
    Write-Host "  [OK] Vocab服务: $($response.services.'vocab_v2')" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] 无法连接到服务器" -ForegroundColor Red
    Write-Host "  请先运行: .\start_backend.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 测试获取词汇列表
Write-Host "[2] 测试获取词汇列表..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/?limit=3" -Method Get
    $count = $response.data.vocabs.Count
    Write-Host "  [OK] 获取成功: $count 个词汇" -ForegroundColor Green
    
    if ($count -gt 0) {
        $vocab = $response.data.vocabs[0]
        Write-Host "  第一个词汇:" -ForegroundColor Cyan
        Write-Host "    - ID: $($vocab.vocab_id)"
        Write-Host "    - 内容: $($vocab.vocab_body)"
        Write-Host "    - 来源: $($vocab.source)"
        Write-Host "    - 收藏: $($vocab.is_starred)"
    }
} catch {
    Write-Host "  [ERROR] 获取词汇失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 测试搜索
Write-Host "[3] 测试搜索功能..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/search/?keyword=test" -Method Get
    $count = $response.data.count
    Write-Host "  [OK] 搜索成功: 找到 $count 个结果" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] 搜索失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 测试统计
Write-Host "[4] 测试统计功能..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/stats/summary" -Method Get
    $stats = $response.data
    Write-Host "  [OK] 统计获取成功:" -ForegroundColor Green
    Write-Host "    - 总词汇: $($stats.total)"
    Write-Host "    - 收藏: $($stats.starred)"
    Write-Host "    - 自动生成: $($stats.auto)"
    Write-Host "    - 手动添加: $($stats.manual)"
} catch {
    Write-Host "  [ERROR] 获取统计失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "你现在可以访问:" -ForegroundColor Yellow
Write-Host "  - Swagger UI: http://localhost:8001/docs" -ForegroundColor Green
Write-Host "  - 在浏览器中测试所有API端点" -ForegroundColor Green

