# 服务器管理指南

## 📋 项目中的所有服务器文件

### 1️⃣ 主后端API服务器（生产使用）✅

**文件：** `server.py`（项目根目录）  
**端口：** 8001  
**功能：**
- ✅ 完整的后端API
- ✅ 连接SQLite数据库
- ✅ Vocab管理（数据库版本）
- ✅ Vocab详细日志（vocab-verbose）
- ✅ Asked Tokens管理

**启动：**
```powershell
cd C:\Users\Mayn\AILanguageLearning-main
python server.py
```

**访问：**
- API文档：http://localhost:8001/docs
- 健康检查：http://localhost:8001/api/health

**适用场景：**
- ✅ 真实开发和测试
- ✅ 前端联调
- ✅ 生产部署
- ✅ 数据库操作

---

### 2️⃣ 前端Mock服务器（开发辅助）

**文件：** `frontend\my-web-ui\backend\server_frontend_mock.py`（已重命名）  
**端口：** 8000  
**功能：**
- 🔴 前端开发调试
- 🔴 模拟API响应
- 🔴 不需要数据库
- 🔴 返回Mock数据

**启动：**
```powershell
cd frontend\my-web-ui\backend
python server_frontend_mock.py
```

**访问：**
```
http://localhost:8000
```

**适用场景：**
- 🔴 前端独立开发
- 🔴 UI原型设计
- 🔴 不需要真实数据的测试

---

## 🎯 未来如何处理

### 推荐方案：明确分工

```
项目结构
│
├── server.py  ← 主后端API（8001端口）
│   用途：生产和真实开发
│   状态：保持并持续完善 ✅
│
└── frontend/my-web-ui/backend/
    ├── server_frontend_mock.py  ← Mock服务器（8000端口）
    │   用途：前端独立开发
    │   状态：按需使用，或归档 🔴
    │
    ├── main.py  ← 其他前端后端文件
    └── ...
```

---

## 🔄 三种使用模式

### 模式1：完整开发模式（使用真实数据）

**适用：** 后端开发、前后端联调、测试

```powershell
# 终端1：启动后端API
cd C:\Users\Mayn\AILanguageLearning-main
python server.py  # 8001端口

# 终端2：启动前端
cd frontend\my-web-ui
npm run dev  # 5173端口
```

**架构：**
```
前端(5173) → 后端API(8001) → 数据库
```

---

### 模式2：前端独立开发（使用Mock数据）

**适用：** 前端UI开发，不需要真实数据

```powershell
# 终端1：启动Mock服务器
cd frontend\my-web-ui\backend
python server_frontend_mock.py  # 8000端口

# 终端2：启动前端
cd frontend\my-web-ui
npm run dev  # 5173端口
```

**架构：**
```
前端(5173) → Mock API(8000) → Mock数据
```

---

### 模式3：仅测试后端API

**适用：** 后端开发、API测试

```powershell
# 只启动后端
cd C:\Users\Mayn\AILanguageLearning-main
python server.py  # 8001端口

# 使用Swagger测试
# http://localhost:8001/docs
```

**架构：**
```
Swagger UI → 后端API(8001) → 数据库
```

---

## 🛠️ 管理建议

### 选项A：保留两个（推荐）

**优点：**
- ✅ 前端可以独立开发
- ✅ 不需要启动完整后端
- ✅ 快速原型开发

**结构：**
```
server.py  ← 主服务器（8001）
frontend/my-web-ui/backend/server_frontend_mock.py  ← Mock服务器（8000）
```

**使用：**
- 真实开发 → 用 `server.py`
- 前端原型 → 用 `server_frontend_mock.py`

---

### 选项B：归档Mock服务器（如果不需要）

如果前端总是连接真实后端，可以归档：

```powershell
# 创建归档目录
New-Item -Path "frontend\my-web-ui\backend\archive" -ItemType Directory -Force

# 移动文件
Move-Item -Path "frontend\my-web-ui\backend\server_frontend_mock.py" -Destination "frontend\my-web-ui\backend\archive\"
```

---

### 选项C：统一配置文件

创建配置文件管理不同环境：

```python
# config.py（项目根目录）
import os

class Config:
    # 环境
    ENV = os.getenv("ENV", "development")
    
    # 端口配置
    API_PORT = 8001  # 真实API
    MOCK_PORT = 8000  # Mock API
    FRONTEND_PORT = 5173  # 前端UI
    
    # 数据库配置
    DATABASE_URL = "sqlite:///database_system/data_storage/data/dev.db"
    
    # API版本
    USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
```

```python
# server.py
from config import Config

if __name__ == "__main__":
    port = Config.MOCK_PORT if Config.USE_MOCK else Config.API_PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 📝 快速参考卡片

### 何时使用哪个服务器？

| 场景 | 使用服务器 | 端口 | 启动命令 |
|------|-----------|------|---------|
| **真实开发/测试** | `server.py` | 8001 | `python server.py` |
| **前端独立开发** | `server_frontend_mock.py` | 8000 | `python frontend/.../server_frontend_mock.py` |
| **生产部署** | `server.py` | 8001 | `python server.py` |
| **API调试** | `server.py` | 8001 | `python server.py` + Swagger |

---

## ✅ 当前状态（已完成）

我已经帮你：
1. ✅ 重命名前端服务器：`server.py` → `server_frontend_mock.py`
2. ✅ 保持根目录服务器：`server.py` 不变
3. ✅ 创建说明文档

**现在：**
- `server.py` = 主后端API（8001端口）← **使用这个！**
- `frontend/.../server_frontend_mock.py` = Mock服务器（8000端口）← 前端开发用

---

## 🚀 现在开始正确使用

```powershell
# 确保在项目根目录
cd C:\Users\Mayn\AILanguageLearning-main

# 启动主后端API
python server.py

# 应该看到：
# INFO:     Uvicorn running on http://0.0.0.0:8001  ← 8001端口！
```

**访问详细日志API：**
```
http://localhost:8001/api/v2/vocab-verbose/1
```

**切换回PowerShell窗口查看完整的数据转换日志！** 🎉

---

## 📚 相关文档

- `PORT_EXPLAINED.md` - 端口概念详解
- `YOUR_PROJECT_PORTS.md` - 项目端口架构
- `CORRECT_SERVER_START.md` - 正确启动方法
- `frontend/my-web-ui/backend/README_SERVERS.md` - 前端服务器说明

