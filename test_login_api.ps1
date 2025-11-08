# 测试登录 API
Write-Host "================================" -ForegroundColor Cyan
Write-Host "测试登录 API" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 测试 User 1
Write-Host "测试 User 1 (密码: test123456)" -ForegroundColor Yellow

$body = @{
    user_id = 1
    password = "test123456"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/auth/login" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "✅ 登录成功！" -ForegroundColor Green
    Write-Host "响应内容:" -ForegroundColor Green
    Write-Host $response.Content
} catch {
    Write-Host "❌ 登录失败！" -ForegroundColor Red
    Write-Host "状态码: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "错误信息:" -ForegroundColor Red
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $reader.BaseStream.Position = 0
    $responseBody = $reader.ReadToEnd()
    Write-Host $responseBody
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan

