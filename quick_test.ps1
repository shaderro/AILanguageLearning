# 快速测试API
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Vocab API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health Check
Write-Host "[1] Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method Get -ErrorAction Stop
    Write-Host "    [OK] Status: $($health.status)" -ForegroundColor Green
    Write-Host "    [OK] Vocab Service: $($health.services.'vocab_v2')" -ForegroundColor Green
} catch {
    Write-Host "    [ERROR] Cannot connect to server" -ForegroundColor Red
    Write-Host "    Make sure server is running on port 8001" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Get Vocabs
Write-Host "[2] Getting vocab list..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/?limit=3" -Method Get -ErrorAction Stop
    $vocabs = $response.data.vocabs
    Write-Host "    [OK] Found $($vocabs.Count) vocabs" -ForegroundColor Green
    
    if ($vocabs.Count -gt 0) {
        Write-Host "    First vocab:" -ForegroundColor Cyan
        Write-Host "      - ID: $($vocabs[0].vocab_id)"
        Write-Host "      - Body: $($vocabs[0].vocab_body)"
        Write-Host "      - Source: $($vocabs[0].source)"
        Write-Host "      - Starred: $($vocabs[0].is_starred)"
    }
} catch {
    Write-Host "    [ERROR] Failed to get vocabs" -ForegroundColor Red
}

Write-Host ""

# Test 3: Stats
Write-Host "[3] Getting statistics..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/stats/summary" -Method Get -ErrorAction Stop
    $stats = $response.data
    Write-Host "    [OK] Statistics:" -ForegroundColor Green
    Write-Host "      - Total: $($stats.total)"
    Write-Host "      - Starred: $($stats.starred)"
    Write-Host "      - Auto: $($stats.auto)"
    Write-Host "      - Manual: $($stats.manual)"
} catch {
    Write-Host "    [ERROR] Failed to get stats" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   All tests completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now visit:" -ForegroundColor Yellow
Write-Host "  - Swagger UI: http://localhost:8001/docs" -ForegroundColor Green
Write-Host ""

