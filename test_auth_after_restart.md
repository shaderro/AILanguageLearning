# 重启后端后的测试步骤

## 1. 停止当前后端服务器
按 `Ctrl+C` 停止正在运行的后端服务器

## 2. 重新启动后端
```powershell
.\start_backend.ps1
```

你应该看到这些输出：
```
[OK] 注册认证API路由: /api/auth
[OK] 注册文章API路由: /api/v2/texts
[OK] 注册词汇API路由: /api/v2/vocab
[OK] 注册语法API路由: /api/v2/grammar
```

## 3. 测试登录API
```powershell
$body = @{
    user_id = 1
    password = "test123456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8001/api/auth/login" -Method POST -Body $body -ContentType "application/json"
```

**预期结果**：
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1
}
```

## 4. 测试前端登录
1. 访问 http://localhost:5173
2. 点击右上角"登录"按钮
3. 输入：
   - User ID: `1`
   - 密码: `test123456`
4. 点击"登录"

**预期结果**：成功登录，页面显示"User 1"

## 5. 其他可用测试账号

| User ID | 密码 |
|---------|------|
| 1 | test123456 |
| 2 | mypassword123 |
| 3 | test123456 |
| 4 | test123456 |
| 5 | testpwd123 |
| 6 | test123 |

注意：User 7-9 的密码未知（需要通过注册创建）

