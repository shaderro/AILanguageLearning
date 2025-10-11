# 🎯 使用哪个服务器？一图看懂

## ✅ 已解决混淆问题

我已经帮你重命名了前端的server.py，现在不会混淆了！

---

## 📁 现在的文件结构

```
AILanguageLearning-main/
│
├── server.py  ← 主后端API（端口8001）
│   ⭐ 使用这个进行真实开发！
│   ⭐ 连接数据库
│   ⭐ 包含vocab-verbose详细日志
│
└── frontend/my-web-ui/backend/
    └── server_frontend_mock.py  ← Mock服务器（端口8000）
        🔴 仅用于前端独立开发
        🔴 不连接数据库
        🔴 返回模拟数据
```

---

## 🎯 快速决策

### 我应该使用哪个？

| 我想做什么... | 使用哪个服务器 | 端口 |
|--------------|---------------|------|
| **开发和测试Vocab数据库功能** | `server.py`（根目录） | 8001 ✅ |
| **查看详细的数据转换日志** | `server.py`（根目录） | 8001 ✅ |
| **前后端联调** | `server.py`（根目录） | 8001 ✅ |
| **测试API** | `server.py`（根目录） | 8001 ✅ |
| **前端独立开发UI** | `server_frontend_mock.py` | 8000 🔴 |
| **快速原型（不需要数据）** | `server_frontend_mock.py` | 8000 🔴 |

**90%的情况下，你应该使用 `server.py`（根目录，8001端口）！**

---

## 🚀 正确启动步骤

### 启动主后端API（99%的情况）

```powershell
# 第1步：确认在根目录
cd C:\Users\Mayn\AILanguageLearning-main
pwd  # 确认路径

# 第2步：启动服务器
python server.py

# 第3步：确认端口
# 应该看到：INFO:     Uvicorn running on http://0.0.0.0:8001
#                                                      ^^^^ 8001端口
```

**如果看到8000，说明目录错了！重新执行第1步。**

---

### 启动Mock服务器（前端独立开发）

```powershell
# 仅在前端需要独立开发时使用
cd frontend\my-web-ui\backend
python server_frontend_mock.py
```

---

## 🔍 如何区分当前运行的是哪个？

### 方法1：看PowerShell输出

**主后端API (server.py)：**
```
============================================================
Starting FastAPI Server...
============================================================
Server Address: http://localhost:8001  ← 看这里！
...
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Mock服务器 (server_frontend_mock.py)：**
```
Creating FastAPI app...
Starting debug API server on port 8000...  ← 看这里！
...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 方法2：检查端口

```powershell
# 运行检查脚本
.\check_ports.ps1
```

输出：
```
[Port 8000] Frontend Debug Server
  [FREE] Not in use  或  [RUNNING] PID: xxxxx

[Port 8001] Backend API Server
  [FREE] Not in use  或  [RUNNING] PID: xxxxx
```

---

### 方法3：访问API根路径

**8001端口（主后端）：**
```
http://localhost:8001/
```

返回：
```json
{
  "message": "Language Learning API",
  "endpoints": {
    "vocab_v2": "/api/v2/vocab",
    "vocab_verbose": "/api/v2/vocab-verbose (详细日志版本)"
  }
}
```

**8000端口（Mock）：**
```
http://localhost:8000/
```

返回不同的响应。

---

## 🔧 如何切换

### 从Mock服务器切换到真实API

```powershell
# 1. 停止Mock服务器（Ctrl+C 或）
Stop-Process -Name python -Force

# 2. 切换到根目录
cd C:\Users\Mayn\AILanguageLearning-main

# 3. 启动真实API
python server.py
```

### 从真实API切换到Mock服务器

```powershell
# 1. 停止真实API
Stop-Process -Name python -Force

# 2. 切换到前端backend目录
cd frontend\my-web-ui\backend

# 3. 启动Mock服务器
python server_frontend_mock.py
```

---

## 💡 端口冲突处理

### 如果8001已被占用

**临时改端口：**
```powershell
# 不修改代码，启动时指定端口
uvicorn server:app --port 8002
```

**或修改配置：**
编辑 `server.py` 最后一行：
```python
uvicorn.run(app, host="0.0.0.0", port=8002)  # 改为8002
```

---

## 📊 端口号规划建议

### 当前使用

| 端口 | 服务 | 状态 |
|------|------|------|
| 5173 | 前端UI (Vite) | 使用中 |
| 8000 | Mock API | 可选 |
| **8001** | **主后端API** | **主要使用** ✅ |

### 未来扩展

| 端口 | 可用于 |
|------|--------|
| 8002 | 测试环境API |
| 8003 | 预发布环境API |
| 9000-9999 | 其他微服务 |

---

## 🎓 端口使用的最佳实践

### 1. 统一规范

```
5000-5999  → 前端服务
8000-8999  → 后端API
9000-9999  → 微服务/工具
3000-3999  → 数据库
```

### 2. 文档化

在项目中记录端口使用：
```
# .env 或 config.py
FRONTEND_PORT=5173
BACKEND_API_PORT=8001
MOCK_API_PORT=8000
```

### 3. 避免冲突

- 使用不常见的端口（8001而不是8000）
- 检查端口：`netstat -ano | findstr :端口`
- 文档化端口使用

---

## ✅ 总结

### 你的两个server.py

| 特征 | 根目录 server.py | 前端 server_frontend_mock.py |
|------|-----------------|----------------------------|
| **路径** | `AILanguageLearning-main/` | `frontend/my-web-ui/backend/` |
| **端口** | 8001 | 8000 |
| **用途** | 真实后端API | 前端开发Mock |
| **数据库** | SQLite（真实） | Mock或JSON |
| **使用频率** | 主要使用 ✅ | 偶尔使用 🔴 |
| **详细日志** | 有（vocab-verbose） | 无 |

### 启动命令

**主后端API（常用）：**
```powershell
cd C:\Users\Mayn\AILanguageLearning-main
python server.py  # 8001端口
```

**Mock服务器（可选）：**
```powershell
cd frontend\my-web-ui\backend
python server_frontend_mock.py  # 8000端口
```

---

## 🎉 问题解决

- ✅ 两个server.py已区分（通过重命名）
- ✅ 清楚各自的用途
- ✅ 知道何时使用哪个
- ✅ 知道如何切换端口
- ✅ 理解端口的概念

**现在你可以正确启动服务器并查看详细日志了！** 🚀

---

## 📞 快速帮助

**忘记在哪个目录？**
```powershell
pwd  # 查看当前目录
```

**忘记哪个端口？**
```powershell
.\check_ports.ps1  # 查看端口使用情况
```

**启动错了？**
```powershell
Stop-Process -Name python -Force  # 停止重来
```

