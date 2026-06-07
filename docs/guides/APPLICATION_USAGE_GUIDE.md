# 应用使用指南

## 🎉 恭喜！数据库表已成功创建

您的应用已成功部署到 Render，PostgreSQL 数据库表结构已初始化完成。

---

## 📍 应用访问地址

您的应用部署在 Render 上，访问地址通常是：
```
https://your-service-name.onrender.com
```

**获取完整 URL：**
1. 登录 Render 控制台
2. 进入您的 Web Service
3. 在顶部可以看到应用的 URL

---

## 🔍 方式一：查看 API 文档（推荐）

FastAPI 自动生成了交互式 API 文档，这是最简单的方式来了解和使用所有 API：

### Swagger UI（推荐）
```
https://your-service-name.onrender.com/docs
```

### ReDoc（备用）
```
https://your-service-name.onrender.com/redoc
```

在文档页面，您可以：
- 查看所有可用的 API 端点
- 查看请求/响应格式
- **直接在浏览器中测试 API**（点击 "Try it out"）
- 查看请求示例

---

## 🚀 方式二：基本使用流程

### 1. 验证应用运行状态

访问健康检查端点：
```bash
GET https://your-service-name.onrender.com/api/health
```

预期响应：
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

### 2. 用户注册

创建新用户：
```bash
POST https://your-service-name.onrender.com/api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "email_unique": true,
  "email_check_message": "邮箱可用"
}
```

**保存 `access_token`，后续 API 调用需要它！**

### 3. 用户登录

如果已有账户：
```bash
POST https://your-service-name.onrender.com/api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

或者使用 user_id：
```bash
{
  "user_id": 1,
  "password": "your_password"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1
}
```

### 4. 使用认证 API

在后续 API 调用中，需要在请求头中包含 token：

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📚 主要 API 端点

### 认证相关 (`/api/auth`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户信息（需要认证） |

### 词汇管理 (`/api/v2/vocab`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/vocab` | GET | 获取词汇列表（需要认证） |
| `/api/v2/vocab/{vocab_id}` | GET | 获取词汇详情（需要认证） |
| `/api/v2/vocab` | POST | 创建新词汇（需要认证） |
| `/api/v2/vocab/{vocab_id}` | PUT | 更新词汇（需要认证） |
| `/api/v2/vocab/{vocab_id}` | DELETE | 删除词汇（需要认证） |

### 语法规则 (`/api/v2/grammar`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/grammar` | GET | 获取语法规则列表（需要认证） |
| `/api/v2/grammar/{rule_id}` | GET | 获取语法规则详情（需要认证） |
| `/api/v2/grammar` | POST | 创建新语法规则（需要认证） |
| `/api/v2/grammar/{rule_id}` | PUT | 更新语法规则（需要认证） |
| `/api/v2/grammar/{rule_id}` | DELETE | 删除语法规则（需要认证） |

### 文章管理 (`/api/v2/texts`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/texts` | GET | 获取文章列表（需要认证） |
| `/api/v2/texts/{text_id}` | GET | 获取文章详情（需要认证） |
| `/api/v2/texts` | POST | 创建新文章（需要认证） |
| `/api/v2/texts/{text_id}` | PUT | 更新文章（需要认证） |
| `/api/v2/texts/{text_id}` | DELETE | 删除文章（需要认证） |

### 聊天功能 (`/api/chat`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | AI 助手聊天（可选认证） |
| `/api/chat/pending-knowledge` | GET | 获取待处理的知识点 |
| `/api/chat/history` | GET | 获取聊天历史（需要认证） |

### 会话管理 (`/api/session`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/session/set_sentence` | POST | 设置当前句子 |
| `/api/session/select_token` | POST | 选择标记 |
| `/api/session/update_context` | POST | 更新上下文 |
| `/api/session/reset` | POST | 重置会话 |

---

## 💡 使用示例

### 示例 1: 完整流程（使用 curl）

```bash
# 1. 注册用户
curl -X POST "https://your-service-name.onrender.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'

# 响应中获取 access_token，替换到下面的 TOKEN 变量
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 2. 获取当前用户信息
curl -X GET "https://your-service-name.onrender.com/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取词汇列表
curl -X GET "https://your-service-name.onrender.com/api/v2/vocab" \
  -H "Authorization: Bearer $TOKEN"

# 4. 创建新词汇
curl -X POST "https://your-service-name.onrender.com/api/v2/vocab" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vocab_body": "example",
    "explanation": "示例",
    "language": "en"
  }'

# 5. 聊天（不需要认证，但建议使用）
curl -X POST "https://your-service-name.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这个单词是什么意思？",
    "sentence": "This is an example sentence.",
    "selected_token": "example"
  }'
```

### 示例 2: 使用 Python requests

```python
import requests

BASE_URL = "https://your-service-name.onrender.com"

# 1. 注册
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={
        "email": "test@example.com",
        "password": "test123456"
    }
)
data = response.json()
token = data["access_token"]
user_id = data["user_id"]

print(f"注册成功！用户ID: {user_id}")
print(f"Token: {token[:50]}...")

# 2. 使用 token 访问受保护的 API
headers = {
    "Authorization": f"Bearer {token}"
}

# 获取词汇列表
response = requests.get(
    f"{BASE_URL}/api/v2/vocab",
    headers=headers
)
vocab_list = response.json()
print(f"词汇列表: {vocab_list}")

# 创建新词汇
response = requests.post(
    f"{BASE_URL}/api/v2/vocab",
    headers=headers,
    json={
        "vocab_body": "hello",
        "explanation": "你好",
        "language": "en"
    }
)
print(f"创建词汇: {response.json()}")
```

### 示例 3: 使用 JavaScript/Fetch

```javascript
const BASE_URL = 'https://your-service-name.onrender.com';

// 1. 注册
async function register() {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: 'test@example.com',
      password: 'test123456'
    })
  });
  
  const data = await response.json();
  console.log('注册成功:', data);
  return data.access_token;
}

// 2. 使用 token 访问 API
async function getVocabList(token) {
  const response = await fetch(`${BASE_URL}/api/v2/vocab`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  console.log('词汇列表:', data);
  return data;
}

// 使用示例
(async () => {
  const token = await register();
  await getVocabList(token);
})();
```

---

## 🌐 前端连接后端

### 1. 配置前端 API 地址

在您的前端代码中，需要配置后端 API 的地址。通常在环境变量或配置文件中：

**开发环境** (`.env.development`):
```env
VITE_API_URL=http://localhost:8000
```

**生产环境** (`.env.production`):
```env
VITE_API_URL=https://your-service-name.onrender.com
```

### 2. 更新 CORS 设置

如果前端部署在其他域名（如 Vercel），需要在后端允许该域名：

修改 `frontend/my-web-ui/backend/main.py` 中的 `ALLOWED_ORIGINS`：

```python
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://your-frontend-domain.vercel.app",  # 添加您的前端域名
]
```

然后重新部署。

### 3. 前端 API 调用示例

```javascript
// api.js
const API_URL = import.meta.env.VITE_API_URL || 'https://your-service-name.onrender.com';

// 注册
export async function register(email, password) {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

// 登录
export async function login(email, password) {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  return response.json();
}

// 获取词汇列表（需要 token）
export async function getVocabList(token) {
  const response = await fetch(`${API_URL}/api/v2/vocab`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.json();
}
```

---

## 🔧 调试和测试

### 1. 查看 API 文档

访问 `/docs` 端点，使用 Swagger UI 测试所有 API。

### 2. 查看数据库信息（调试端点）

```
GET https://your-service-name.onrender.com/api/debug/db-info
```

注意：这个端点可能在生产环境中被禁用。

### 3. 查看 Render 日志

在 Render 控制台查看应用日志，可以看到：
- API 请求日志
- 数据库操作日志
- 错误信息

---

## ⚠️ 重要提示

### 1. Token 管理

- Token 会过期（默认 24 小时）
- 需要安全存储 token（不要提交到代码仓库）
- 前端应该将 token 存储在 localStorage 或 sessionStorage

### 2. 环境变量

确保以下环境变量在 Render 中已设置：
- `DATABASE_URL` - PostgreSQL 连接字符串（应该已自动设置）
- `ENV=production` - 生产环境标识
- `JWT_SECRET` - JWT 密钥（必需）
- `OPENAI_API_KEY` - OpenAI API 密钥（如果需要 AI 功能）

### 3. 数据库

- 所有数据现在存储在 PostgreSQL 数据库中
- 数据持久化，不会因应用重启而丢失
- 每个用户的数据是隔离的（通过 `user_id`）

---

## 📖 下一步

1. **访问 API 文档**: `https://your-service-name.onrender.com/docs`
2. **创建第一个用户**: 使用注册 API
3. **测试功能**: 尝试创建词汇、语法规则等
4. **连接前端**: 将前端应用连接到后端 API
5. **开始使用**: 享受您的语言学习应用！

---

## 🆘 遇到问题？

1. **查看 Render 日志**: 在 Render 控制台查看应用日志
2. **检查 API 文档**: `/docs` 端点有详细的 API 说明
3. **验证环境变量**: 确保所有必需的环境变量已设置
4. **测试连接**: 使用 `/api/health` 端点验证应用运行状态

---

**祝您使用愉快！🎉**