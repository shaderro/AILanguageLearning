# 你的项目端口使用情况

## 🗺️ 完整架构图

```
┌────────────────────────────────────────────────────────────┐
│                    你的电脑 (localhost)                     │
│                                                            │
│  ┌──────────────────────┐     ┌──────────────────────┐   │
│  │   前端UI (Vite)      │     │  后端API (FastAPI)   │   │
│  │                      │     │                      │   │
│  │  端口: 5173         │◄────┤  端口: 8001  ✅     │   │
│  │                      │ API │                      │   │
│  │  目录:               │请求 │  文件:               │   │
│  │  frontend/my-web-ui  │     │  server.py (根目录)  │   │
│  └──────────────────────┘     └─────────┬────────────┘   │
│                                          │                │
│                                          │ 查询            │
│                                          ↓                │
│                              ┌──────────────────────┐     │
│                              │   SQLite数据库       │     │
│                              │                      │     │
│                              │  文件:               │     │
│                              │  database_system/    │     │
│                              │  .../dev.db          │     │
│                              └──────────────────────┘     │
│                                                            │
│  ┌──────────────────────┐                                 │
│  │ 前端调试API (可选)   │                                 │
│  │                      │                                 │
│  │  端口: 8000  🔴     │                                 │
│  │                      │                                 │
│  │  文件:               │                                 │
│  │  frontend/.../       │                                 │
│  │  backend/server.py   │                                 │
│  └──────────────────────┘                                 │
└────────────────────────────────────────────────────────────┘
```

---

## 📁 服务器文件对比

### ✅ 正确的服务器（你应该使用的）

**文件：** `C:\Users\Mayn\AILanguageLearning-main\server.py`

```python
# 端口配置
uvicorn.run(app, host="0.0.0.0", port=8001)

# 功能
- 完整的后端API
- 连接SQLite数据库
- 包含 vocab 路由（9个端点）
- 包含 vocab-verbose 路由（详细日志）
- 包含 asked-tokens 路由

# 启动方式
cd C:\Users\Mayn\AILanguageLearning-main  ← 根目录
python server.py

# 访问
http://localhost:8001/docs
```

---

### 🔴 前端调试服务器（开发用）

**文件：** `frontend\my-web-ui\backend\server.py`

```python
# 端口配置
uvicorn.run(app, host='0.0.0.0', port=8000)

# 功能
- 前端开发时的模拟API
- 不连接真实数据库
- 返回Mock数据
- 用于前端独立开发

# 启动方式
cd frontend\my-web-ui\backend  ← 前端的backend
python server.py

# 访问
http://localhost:8000
```

---

## 🔄 如何切换端口

### 方法1：修改配置文件

打开 `server.py`（**根目录的**），找到最后几行：

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    #                                    ^^^^
    #                                    改这里
```

**修改为其他端口：**
```python
uvicorn.run(app, host="0.0.0.0", port=9000)  # 改为9000
```

### 方法2：命令行指定（临时）

```powershell
# 不修改代码，临时使用其他端口
uvicorn server:app --port 9000 --reload
```

### 方法3：环境变量（高级）

```python
# server.py 改为
import os
port = int(os.getenv("PORT", 8001))  # 默认8001
uvicorn.run(app, host="0.0.0.0", port=port)
```

启动时：
```powershell
$env:PORT=9000; python server.py
```

---

## 🔍 检查端口使用情况

### 查看哪些端口正在使用

```powershell
# 查看特定端口
netstat -ano | findstr :8001

# 查看所有监听的端口
netstat -ano | findstr LISTENING

# 使用我创建的脚本
.\check_ports.ps1
```

**输出示例：**
```
[Port 8000] Frontend Debug Server
  [FREE] Not in use

[Port 8001] Backend API Server
  [RUNNING] PID: 12345
  To stop: Stop-Process -Id 12345 -Force
```

---

## 📝 常用端口号

### Web开发常用端口

| 端口 | 常见用途 |
|------|---------|
| 80 | HTTP网页服务器（默认） |
| 443 | HTTPS安全网页（默认） |
| 3000 | React开发服务器（create-react-app） |
| 4200 | Angular开发服务器 |
| 5173 | Vite开发服务器 |
| 8000 | Django/Flask开发服务器 |
| 8080 | 备用Web服务器 |

### 你的项目使用

| 端口 | 服务 | 用途 |
|------|------|------|
| 5173 | Vite前端 | React UI |
| **8001** | **FastAPI后端** | **主要使用** ✅ |
| 8000 | 调试API | 前端独立开发 |

---

## 🎯 快速参考

### 查看端口

```powershell
netstat -ano | findstr :端口号
```

### 停止进程

```powershell
Stop-Process -Id PID号 -Force
```

### 切换端口

**临时修改：**
```powershell
uvicorn server:app --port 新端口号
```

**永久修改：**
```python
# server.py
uvicorn.run(app, port=新端口号)
```

---

## ✅ 现在做这个

1. **确保在正确目录**
   ```powershell
   cd C:\Users\Mayn\AILanguageLearning-main
   pwd  # 确认目录
   ```

2. **启动服务器**
   ```powershell
   python server.py
   ```

3. **验证端口**
   应该看到 `8001`，不是 `8000`

4. **测试**
   ```
   http://localhost:8001/docs
   ```

现在试试吧！记住一定要在**项目根目录**运行！🚀

