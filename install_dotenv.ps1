# 安装 python-dotenv 脚本
Write-Host "正在安装 python-dotenv..." -ForegroundColor Yellow

# 尝试多种安装方式
$methods = @(
    { python -m pip install python-dotenv },
    { pip install python-dotenv },
    { python -m pip install --user python-dotenv }
)

foreach ($method in $methods) {
    try {
        Write-Host "尝试方法: $($method.ToString())" -ForegroundColor Cyan
        & $method 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 安装成功！" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "❌ 方法失败: $_" -ForegroundColor Red
    }
}

# 验证安装
Write-Host "`n验证安装..." -ForegroundColor Yellow
try {
    python -c "from dotenv import load_dotenv; print('✅ python-dotenv 可用')"
} catch {
    Write-Host "❌ 验证失败，请手动安装" -ForegroundColor Red
    Write-Host "运行: python -m pip install python-dotenv" -ForegroundColor Yellow
}

