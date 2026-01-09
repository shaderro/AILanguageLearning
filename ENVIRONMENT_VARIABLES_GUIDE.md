# 🔐 环境变量管理指南

## ⚠️ 为什么环境变量不能写在代码里？

### 1. **安全风险**
- **代码泄露风险**：如果代码被提交到 Git 仓库（包括 GitHub、GitLab 等），所有硬编码的密钥都会被公开
- **版本控制暴露**：即使后来删除了密钥，Git 历史记录中仍然保留，任何人都可以查看
- **多人协作风险**：团队成员可能无意中看到或分享包含密钥的代码

### 2. **不同环境配置**
- **开发环境**：使用测试密钥和本地数据库
- **测试环境**：使用测试密钥和测试数据库
- **生产环境**：使用真实密钥和生产数据库
- 如果硬编码，每次切换环境都需要修改代码，容易出错

### 3. **密钥轮换困难**
- 如果密钥泄露，需要立即更换
- 硬编码的密钥需要修改代码、重新部署
- 环境变量只需要更新配置，无需修改代码

### 4. **合规要求**
- 许多安全标准（如 PCI DSS、SOC 2）要求敏感信息不能存储在代码中
- 审计时会被标记为安全漏洞

## 📋 必需的环境变量

以下环境变量**必须**通过环境变量管理，**绝对不能**硬编码在代码中：

### 1. `JWT_SECRET`
- **用途**：用于生成和验证 JWT token（用户认证）
- **重要性**：🔴 **极高** - 泄露后攻击者可以伪造用户身份
- **生成方法**：
  ```bash
  # Linux/Mac
  openssl rand -hex 32
  
  # Windows PowerShell
  -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
  ```

### 2. `OPENAI_API_KEY`
- **用途**：调用 OpenAI/DeepSeek API
- **重要性**：🔴 **极高** - 泄露后可能产生费用，或被他人滥用
- **获取方法**：从 API 提供商网站获取

### 3. `DATABASE_URL`
- **用途**：数据库连接字符串
- **重要性**：🟠 **高** - 泄露后可能暴露数据库访问权限
- **格式示例**：`sqlite:///database_system/data_storage/data/dev.db`

### 4. `ENV`
- **用途**：指定运行环境（development/testing/production）
- **重要性**：🟡 **中** - 影响应用行为和数据隔离
- **可选值**：`development` / `testing` / `production`

## 🚀 使用方法

### 步骤 1：安装依赖

```bash
pip install python-dotenv
```

### 步骤 2：创建 `.env` 文件

在项目根目录创建 `.env` 文件（**不要提交到 Git**）：

```env
# JWT 密钥（生产环境必须使用强随机字符串）
JWT_SECRET=your-strong-random-secret-key-here

# OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# 运行环境
ENV=development

# 数据库 URL（可选）
# DATABASE_URL=sqlite:///database_system/data_storage/data/dev.db
```

### 步骤 3：确保 `.env` 不被提交

检查 `.gitignore` 文件是否包含：

```
.env
.env.local
.env.*.local
```

### 步骤 4：在代码中使用

代码会自动从环境变量读取配置：

```python
# ✅ 正确：从环境变量读取
from backend.config import JWT_SECRET, OPENAI_API_KEY, ENV

# ❌ 错误：硬编码在代码中
SECRET_KEY = "sk-4035e2a8e00b48c2a335b8cadbd98979"  # 绝对不要这样做！
```

## 🔍 检查清单

在提交代码前，检查以下内容：

- [ ] 所有 API Key 都从环境变量读取
- [ ] 所有密钥都从环境变量读取
- [ ] 所有数据库连接字符串都从环境变量读取
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 代码中没有硬编码的密钥
- [ ] 代码中没有硬编码的 API Key
- [ ] 代码中没有硬编码的数据库 URL

## 🛠️ 已修复的问题

### ✅ 已修复的文件

1. **`backend/utils/auth.py`**
   - ❌ 之前：`SECRET_KEY = "your-secret-key-change-in-production"`
   - ✅ 现在：从 `JWT_SECRET` 环境变量读取

2. **`backend/assistants/sub_assistants/sub_assistant.py`**
   - ❌ 之前：`api_key="sk-4035e2a8e00b48c2a335b8cadbd98979"`
   - ✅ 现在：从 `OPENAI_API_KEY` 环境变量读取

3. **`backend/api/text_routes.py`**
   - ❌ 之前：`DatabaseManager('development')`
   - ✅ 现在：从 `ENV` 环境变量读取

4. **`backend/api/auth_routes.py`**
   - ❌ 之前：`DatabaseManager('development')`
   - ✅ 现在：从 `ENV` 环境变量读取

5. **`backend/api/vocab_routes.py`**
   - ❌ 之前：`DatabaseManager('development')`
   - ✅ 现在：从 `ENV` 环境变量读取

6. **`backend/api/grammar_routes.py`**
   - ❌ 之前：`DatabaseManager('development')`
   - ✅ 现在：从 `ENV` 环境变量读取

## 📝 注意事项

1. **开发环境**：如果未设置环境变量，代码会使用默认值并显示警告
2. **生产环境**：必须设置所有必需的环境变量，否则应用可能无法启动
3. **密钥管理**：建议使用密钥管理服务（如 AWS Secrets Manager、Azure Key Vault）管理生产环境密钥

## 🔗 相关文件

- `backend/config.py` - 统一的环境变量配置模块
- `.env.example` - 环境变量模板（可以提交到 Git）
- `requirements.txt` - 已添加 `python-dotenv` 依赖

