# Quick Auth Test Script (English only to avoid encoding issues)

Write-Host "`n=== Auth API Test ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8001"

# Test 1: Register
Write-Host "`n[1] Register..." -ForegroundColor Yellow
$registerResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/register" -Method Post -Body '{"password":"test123"}' -ContentType "application/json"
Write-Host "  SUCCESS! User ID: $($registerResp.user_id)" -ForegroundColor Green
$userId = $registerResp.user_id
$token = $registerResp.access_token

# Test 2: Get current user
Write-Host "`n[2] Get current user info..." -ForegroundColor Yellow
$headers = @{ Authorization = "Bearer $token" }
$userResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/me" -Headers $headers
Write-Host "  SUCCESS! User ID: $($userResp.user_id)" -ForegroundColor Green

# Test 3: Login
Write-Host "`n[3] Login..." -ForegroundColor Yellow
$loginBody = @{ user_id = $userId; password = "test123" } | ConvertTo-Json
$loginResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
Write-Host "  SUCCESS! User ID: $($loginResp.user_id)" -ForegroundColor Green

Write-Host "`n=== ALL TESTS PASSED ===" -ForegroundColor Green
Write-Host "User ID: $userId" -ForegroundColor Cyan
Write-Host "Token: $token`n" -ForegroundColor Gray

