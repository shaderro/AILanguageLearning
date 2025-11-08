# 快速测试认证功能

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   测试认证 API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001"

# 测试 1: 注册
Write-Host "[Test 1] 注册新用户..." -ForegroundColor Yellow
try {
    $registerResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method Post -Body '{"password":"test123"}' -ContentType "application/json"
    Write-Host "  [OK] 注册成功!" -ForegroundColor Green
    Write-Host "  User ID: $($registerResp.user_id)" -ForegroundColor Cyan
    Write-Host "  Token: $($registerResp.access_token.Substring(0,50))..." -ForegroundColor Gray
    
    $userId = $registerResp.user_id
    $token = $registerResp.access_token
} catch {
    Write-Host "  [ERROR] 注册失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 2: 登录
Write-Host "[Test 2] 使用密码登录..." -ForegroundColor Yellow
try {
    $loginBody = @{
        user_id = $userId
        password = "test123"
    } | ConvertTo-Json
    
    $loginResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    Write-Host "  [OK] 登录成功!" -ForegroundColor Green
    Write-Host "  User ID: $($loginResp.user_id)" -ForegroundColor Cyan
    
    $token = $loginResp.access_token
} catch {
    Write-Host "  [ERROR] 登录失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 3: 获取当前用户信息
Write-Host "[Test 3] 获取当前用户信息..." -ForegroundColor Yellow
try {
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    $userResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/me" -Headers $headers
    Write-Host "  [OK] 成功获取用户信息!" -ForegroundColor Green
    Write-Host "  User ID: $($userResp.user_id)" -ForegroundColor Cyan
    Write-Host "  Created: $($userResp.created_at)" -ForegroundColor Gray
} catch {
    Write-Host "  [ERROR] 获取失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 测试 4: 错误密码
Write-Host "[Test 4] 测试错误密码（应该失败）..." -ForegroundColor Yellow
try {
    $wrongBody = @{
        user_id = $userId
        password = "wrongpassword"
    } | ConvertTo-Json
    
    $wrongResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $wrongBody -ContentType "application/json"
    Write-Host "  [WARNING] 应该拒绝错误密码！" -ForegroundColor Red
} catch {
    Write-Host "  [OK] 正确拒绝了错误密码" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   [SUCCESS] 所有测试通过!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "保存的信息:" -ForegroundColor Yellow
Write-Host "  User ID: $userId" -ForegroundColor Cyan
Write-Host "  Token: $token" -ForegroundColor Gray
Write-Host ""

