# 两个server.py的处理方案

## 📊 当前情况

你的项目中有两个 `server.py` 文件：

### 1️⃣ 根目录的 `server.py` （206行）

**位置：** `C:\Users\Mayn\AILanguageLearning-main\server.py`

**特点：**
- ✅ 简洁清晰（206行）
- ✅ 端口：8001
- ✅ 功能：真实后端API
- ✅ 数据库：连接SQLite
- ✅ 路由：
  - `/api/v2/vocab/` - Vocab管理（数据库）
  - `/api/v2/vocab-verbose/` - 详细日志版本
  - `/api/user/asked-tokens` - Asked Tokens
- ✅ **这是主要的生产服务器**

**用途：**
```python
# 核心后端API服务器
# - 连接真实数据库
# - 提供RESTful API
# - 供前端调用
```

---

### 2️⃣ 前端目录的 `server.py` （934行）

**位置：** `frontend\my-web-ui\backend\server.py`

**特点：**
- ⚠️ 复杂庞大（934行）
- ⚠️ 端口：8000
- ⚠️ 功能：前端开发调试用
- ⚠️ 数据库：可能使用JSON文件或Mock数据
- ⚠️ 路由：包含各种前端调试端点
- 🔴 **这是前端开发时的临时服务器**

**用途：**
```python
# 前端独立开发调试服务器
# - 前端开发者不需要启动真实后端
# - 提供Mock数据
# - 快速原型开发
```

---

## 🎯 推荐处理方案

### 方案1：重命名区分（推荐）✅

**保留两个文件，但重命名以避免混淆：**

#### 步骤1：重命名前端的server.py

```powershell
# 在项目根目录运行
Rename-Item -Path "frontend\my-web-ui\backend\server.py" -NewName "server_dev_mock.py"
```

**结果：**
```
frontend\my-web-ui\backend\server_dev_mock.py  ← 前端开发Mock服务器
```

#### 步骤2：保持根目录的server.py不变

```
server.py  ← 生产后端API服务器（保持原名）
```

#### 步骤3：创建说明文件

```powershell
# 在前端backend目录创建README
```

---

### 方案2：归档前端服务器（如果不再使用）

如果前端已经可以调用真实后端，前端的Mock服务器可以归档：

```powershell
# 创建archive目录
New-Item -Path "frontend\my-web-ui\backend\archive" -ItemType Directory -Force

# 移动文件
Move-Item -Path "frontend\my-web-ui\backend\server.py" -Destination "frontend\my-web-ui\backend\archive\server_mock_backup.py"
```

---

### 方案3：统一配置（长期方案）

创建配置文件来管理端口：

```python
# config.py
class Config:
    # 生产环境
    PRODUCTION_API_PORT = 8001
    
    # 开发环境
    DEV_MOCK_API_PORT = 8000
    DEV_FRONTEND_PORT = 5173
    
    # 数据库
    DATABASE_URL = "sqlite:///database_system/data_storage/data/dev.db"
```

然后在server.py中使用：

```python
from config import Config

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PRODUCTION_API_PORT)
```

---

## 🔧 立即实施（推荐方案1）

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">Rename-Item -Path "frontend\my-web-ui\backend\server.py" -NewName "server_frontend_mock.py"
