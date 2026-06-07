# 🚀 .env 文件配置步骤

## 当前状态
✅ `.env` 文件已创建在项目根目录

## 下一步：填写实际值

### 步骤 1：生成并填写 JWT_SECRET

**JWT_SECRET** 用于生成和验证用户登录 token，必须使用强随机字符串。

#### 方法 1：使用 PowerShell 生成（推荐）

在 PowerShell 中运行：
```powershell
$jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "生成的 JWT_SECRET: $jwtSecret"
```

复制生成的密钥，然后：
1. 打开 `.env` 文件
2. 找到 `JWT_SECRET=your-secret-key-change-in-production`
3. 替换为：`JWT_SECRET=你生成的密钥`

#### 方法 2：使用在线工具
访问：https://randomkeygen.com/ 生成随机密钥

#### 方法 3：手动创建（简单但不推荐）
可以暂时使用一个长字符串，例如：
```
JWT_SECRET=my-development-secret-key-2024-change-in-production-1234567890abcdef
```

⚠️ **注意**：生产环境必须使用强随机密钥！

### 步骤 2：填写 OPENAI_API_KEY

**OPENAI_API_KEY** 用于调用 AI 功能。

#### 如果你有 OpenAI/DeepSeek API Key：

1. 打开 `.env` 文件
2. 找到 `OPENAI_API_KEY=sk-your-api-key-here`
3. 替换为：`OPENAI_API_KEY=你的实际API密钥`

#### 如果你还没有 API Key：

**选项 A：暂时留空（功能受限）**
- 保持 `OPENAI_API_KEY=sk-your-api-key-here`
- 应用会显示警告，但可以运行（AI 功能不可用）

**选项 B：获取 API Key**
- **OpenAI**：https://platform.openai.com/api-keys
- **DeepSeek**：https://platform.deepseek.com/api_keys

### 步骤 3：确认 ENV 设置

**ENV** 指定运行环境，当前应该设置为：
```
ENV=development
```

✅ 这个值已经是正确的，不需要修改（除非你要切换到测试或生产环境）

### 步骤 4：保存文件

保存 `.env` 文件（Ctrl+S）

## 📝 配置示例

配置完成后的 `.env` 文件应该类似这样：

```env
# 环境变量配置模板
# ...（注释部分保持不变）...

# JWT 密钥
JWT_SECRET=AbC123XyZ789...（64位随机字符串）

# OpenAI API Key
OPENAI_API_KEY=sk-...（你的实际API密钥）

# 运行环境
ENV=development
```

## ✅ 验证配置

### 方法 1：启动应用验证

启动你的应用，应该看到：
```
[OK] 已加载环境变量文件: C:\Users\ranxi\AILanguageLearning\.env
```

如果没有看到警告，说明配置成功！

### 方法 2：使用 Python 验证

```powershell
python -c "from backend.config import JWT_SECRET, OPENAI_API_KEY, ENV; print(f'JWT_SECRET: {JWT_SECRET[:20]}...'); print(f'OPENAI_API_KEY: {OPENAI_API_KEY[:20] if OPENAI_API_KEY else \"未设置\"}...'); print(f'ENV: {ENV}')"
```

## 🔒 安全提醒

1. ✅ **不要**将 `.env` 文件提交到 Git
2. ✅ **不要**在聊天、邮件中分享 `.env` 文件内容
3. ✅ **不要**在代码中硬编码这些值
4. ✅ 定期轮换密钥（特别是生产环境）

## 🎯 下一步

配置完成后：
1. 安装依赖：`pip install python-dotenv`
2. 重启应用，验证环境变量是否正确加载
3. 测试登录功能（JWT_SECRET 应该生效）
4. 测试 AI 功能（如果设置了 OPENAI_API_KEY）

