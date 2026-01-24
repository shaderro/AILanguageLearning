# Token 使用记录与扣减机制 - 测试指南

## 📋 测试前准备

### 1. 运行数据库迁移

确保 `token_logs` 表已创建：

```powershell
# 在项目根目录运行
python migrate_add_token_logs_table.py
```

### 2. 运行基础检查脚本

检查数据库表结构和现有数据：

```powershell
# 在项目根目录运行
python test_token_usage_system.py
```

这个脚本会检查：
- ✅ token_logs 表是否存在
- ✅ 用户 token 余额
- ✅ 现有的 token 使用记录
- ✅ token_ledger 账本记录

---

## 🧪 测试步骤

### 步骤 1: 启动后端服务器

确保后端正在运行（通常是 `http://localhost:8000` 或 `http://localhost:8001`）：

```powershell
# 方式 1: 使用启动脚本
.\start_backend.ps1

# 方式 2: 手动启动
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 步骤 2: 获取用户认证 Token

#### 方式 A: 使用现有用户登录

```powershell
# 使用 PowerShell 测试
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body (@{
        user_id = 1
        password = "your_password"
    } | ConvertTo-Json)

$token = $response.access_token
Write-Host "Token: $token"
```

#### 方式 B: 使用 curl（如果已安装）

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "password": "your_password"
  }'
```

#### 方式 C: 使用 Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={
        "user_id": 1,
        "password": "your_password"
    }
)

token = response.json()["access_token"]
print(f"Token: {token}")
```

### 步骤 3: 查看初始 Token 余额

调用 `/api/auth/me` 接口查看当前用户的 token 信息：

```powershell
# PowerShell
$headers = @{
    "Authorization" = "Bearer $token"
}

$userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" `
    -Method GET `
    -Headers $headers

Write-Host "Token Balance: $($userInfo.token_balance)"
Write-Host "Total Tokens Used: $($userInfo.total_tokens_used)"
```

**记录初始值**：
- `token_balance`: ________
- `total_tokens_used`: ________

### 步骤 4: 测试 Chat API（触发 Token 扣减）

⚠️ **重要**：调用 Chat API 会触发 DeepSeek API 调用，从而扣减 token。

#### 前置条件

Chat API 需要先设置会话上下文（句子和问题）。可以通过前端 UI 或直接调用 API：

```powershell
# 1. 设置句子上下文（可选，如果前端已设置可跳过）
$sessionPayload = @{
    sentence = @{
        text_id = 1
        sentence_id = 1
        sentence_body = "This is a test sentence."
    }
    current_input = "What does this mean?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/session/update_context" `
    -Method POST `
    -ContentType "application/json" `
    -Body $sessionPayload

# 2. 调用 Chat API（会触发 token 扣减）
$chatPayload = @{
    user_question = "What does this sentence mean?"
} | ConvertTo-Json

$chatResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
    -Method POST `
    -ContentType "application/json" `
    -Headers $headers `
    -Body $chatPayload

Write-Host "AI Response: $($chatResponse.data.ai_response)"
```

#### 观察后端日志

在后端控制台中，你应该看到类似这样的日志：

```
💰 [Token Usage] user_id=1 | model=deepseek-chat | prompt_tokens=123 | completion_tokens=45 | total_tokens=168 | balance_after=999832
```

### 步骤 5: 验证 Token 扣减

再次调用 `/api/auth/me` 接口，检查 token 是否已扣减：

```powershell
$userInfoAfter = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" `
    -Method GET `
    -Headers $headers

Write-Host "Token Balance (After): $($userInfoAfter.token_balance)"
Write-Host "Total Tokens Used (After): $($userInfoAfter.total_tokens_used)"
```

**验证**：
- ✅ `token_balance` 应该减少（减少量 = 本次使用的 total_tokens）
- ✅ `total_tokens_used` 应该增加（增加量 = 本次使用的 total_tokens）

### 步骤 6: 检查数据库记录

运行测试脚本查看数据库记录：

```powershell
python test_token_usage_system.py
```

或者直接查询数据库：

```sql
-- 查看最近的 token 使用记录
SELECT * FROM token_logs 
ORDER BY created_at DESC 
LIMIT 5;

-- 查看 token 账本记录
SELECT * FROM token_ledger 
WHERE reason = 'ai_usage' 
ORDER BY created_at DESC 
LIMIT 5;

-- 查看用户当前余额
SELECT user_id, token_balance, token_updated_at 
FROM users 
WHERE user_id = 1;
```

---

## 🎯 完整测试流程（推荐）

### 使用前端 UI 测试（最简单）

1. **启动前端和后端**
   ```powershell
   # 终端 1: 启动后端
   .\start_backend.ps1
   
   # 终端 2: 启动前端
   .\start_frontend.ps1
   ```

2. **登录并查看 Profile**
   - 打开浏览器访问 `http://localhost:5173`
   - 登录你的账户
   - 进入 Profile/Settings 页面
   - 查看 "Token 管理" 模块中的当前剩余 Token

3. **使用 Chat 功能**
   - 选择一篇文章
   - 选择一个句子
   - 提问（例如："What does this mean?"）
   - 等待 AI 回答

4. **再次查看 Profile**
   - 刷新 Profile 页面
   - 检查 Token 余额是否减少
   - 检查累计使用量是否增加

5. **查看后端日志**
   - 在后端控制台查找 `💰 [Token Usage]` 日志
   - 验证 token 使用信息

---

## ✅ 预期结果检查清单

### 数据库层面

- [ ] `token_logs` 表中有新记录
- [ ] `token_logs.total_tokens` = 本次 API 调用使用的 token 数
- [ ] `token_logs.prompt_tokens` 和 `completion_tokens` 有值
- [ ] `token_ledger` 表中有 `reason='ai_usage'` 的记录
- [ ] `token_ledger.delta` 为负数（表示消耗）
- [ ] `users.token_balance` 已更新
- [ ] `users.token_updated_at` 已更新

### API 层面

- [ ] `/api/auth/me` 返回 `token_balance`（当前余额）
- [ ] `/api/auth/me` 返回 `total_tokens_used`（累计使用）
- [ ] `token_balance` 在每次 API 调用后减少
- [ ] `total_tokens_used` 在每次 API 调用后增加

### 日志层面

- [ ] 后端日志中有 `💰 [Token Usage]` 输出
- [ ] 日志包含：user_id, model, prompt_tokens, completion_tokens, total_tokens, balance_after

---

## 🐛 常见问题排查

### 问题 1: Token 没有扣减

**可能原因**：
- 未提供认证 token（使用默认用户 ID 2）
- session 未正确传递
- API 调用失败（未到达 token 记录代码）

**排查步骤**：
1. 检查后端日志中是否有 `💰 [Token Usage]` 输出
2. 检查是否有错误日志
3. 确认提供了正确的 Authorization header

### 问题 2: total_tokens_used 为 0

**可能原因**：
- 还没有调用过 Chat API
- 查询统计有误

**排查步骤**：
1. 运行 `python test_token_usage_system.py` 查看数据库记录
2. 直接查询 `token_logs` 表

### 问题 3: 后端日志没有输出

**可能原因**：
- API 调用失败
- token 记录代码未执行

**排查步骤**：
1. 检查后端日志中是否有 API 调用记录
2. 检查是否有异常错误
3. 确认 `SubAssistant.run()` 方法被正确调用

---

## 📊 测试数据示例

假设你进行了 3 次 Chat API 调用：

| 调用次数 | total_tokens | token_balance (前) | token_balance (后) | total_tokens_used |
|---------|-------------|-------------------|-------------------|------------------|
| 1 | 168 | 1,000,000 | 999,832 | 168 |
| 2 | 145 | 999,832 | 999,687 | 313 |
| 3 | 192 | 999,687 | 999,495 | 505 |

每次调用后：
- `token_balance` 减少 `total_tokens`
- `total_tokens_used` 增加 `total_tokens`
- `token_logs` 表中有新记录
- `token_ledger` 表中有新记录

---

## 🎉 测试完成

如果所有检查项都通过，说明 token 使用记录与扣减机制工作正常！

接下来可以：
1. 在前端 Profile 页面查看 token 使用情况
2. 使用邀请码兑换更多 token
3. 监控后端日志中的 token 使用情况
