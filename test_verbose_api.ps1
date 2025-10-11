# 测试详细日志API端点
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Verbose Logging API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Make sure the server is running and you can see its console!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to test GET vocab by ID (look at server console for logs)..."
Read-Host

Write-Host ""
Write-Host "[1] Testing GET /api/v2/vocab-verbose/1" -ForegroundColor Green
Write-Host "    Watch the server console for detailed logs!" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab-verbose/1" -Method Get -ErrorAction Stop
    Write-Host "Response received:" -ForegroundColor Cyan
    Write-Host "  - vocab_body: $($response.data.vocab_body)"
    Write-Host "  - source: $($response.data.source) (type: string)"
    Write-Host "  - is_starred: $($response.data.is_starred)"
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to test GET all vocabs..."
Read-Host

Write-Host ""
Write-Host "[2] Testing GET /api/v2/vocab-verbose/ (get 2 vocabs)" -ForegroundColor Green
Write-Host "    Watch the server console for detailed logs!" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab-verbose/?limit=2" -Method Get -ErrorAction Stop
    Write-Host "Response received:" -ForegroundColor Cyan
    Write-Host "  - Count: $($response.data.count)"
    Write-Host "  - First vocab: $($response.data.vocabs[0].vocab_body)"
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to test POST (create vocab)..."
Read-Host

Write-Host ""
Write-Host "[3] Testing POST /api/v2/vocab-verbose/ (create)" -ForegroundColor Green
Write-Host "    Watch the server console for detailed logs!" -ForegroundColor Yellow
Write-Host ""

$body = @{
    vocab_body = "powershell_verbose_test"
    explanation = "PowerShell verbose logging test"
    source = "manual"
    is_starred = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab-verbose/" -Method Post -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host "Response received:" -ForegroundColor Cyan
    Write-Host "  - Created vocab_id: $($response.data.vocab_id)"
    Write-Host "  - vocab_body: $($response.data.vocab_body)"
    Write-Host "  - source: $($response.data.source)"
    
    $createdId = $response.data.vocab_id
    
    Write-Host ""
    Write-Host "Cleaning up (deleting test vocab)..." -ForegroundColor Yellow
    Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/$createdId" -Method Delete | Out-Null
    Write-Host "  Test vocab deleted." -ForegroundColor Green
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Testing Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the server console to see the detailed conversion logs!" -ForegroundColor Yellow
Write-Host ""

