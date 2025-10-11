# 端口概念详解

## 🌐 什么是端口？

### 类比：楼房和房间

想象你的电脑是一栋大楼：

```
你的电脑（IP地址：127.0.0.1 或 localhost）
│
│  就像一栋楼的地址
│
└─ 楼里有很多房间（端口）
   ├─ 房间 80号   → 网页服务器
   ├─ 房间 443号  → 安全网页
   ├─ 房间 3000号 → React开发服务器
   ├─ 房间 5173号 → Vite前端服务器
   ├─ 房间 8000号 → 前端调试API
   ├─ 房间 8001号 → 后端真实API
   └─ 房间 3306号 → MySQL数据库
```

**访问方式：**
```
http://localhost       → 访问80号房间（默认）
http://localhost:8000  → 访问8000号房间
http://localhost:8001  → 访问8001号房间
```

---

## 🔢 你的项目中的端口

### 全部服务器文件清单

| 文件位置 | 端口 | 用途 | 是否使用 |
|---------|------|------|---------|
| **server.py** (根目录) | **8001** | 后端API（数据库版） | ✅ **使用这个！** |
| frontend/my-web-ui/backend/server.py | 8000 | 前端调试API | 🔴 调试用 |
| frontend/my-web-ui/backend/main.py | 8000 | 前端完整后端 | 🔴 旧版本 |
| frontend/my-web-ui/backend/main_fixed.py | 8000 | 修复版本 | 🔴 备份 |
| frontend/my-web-ui/backend/main_backup.py | 8000 | 备份版本 | 🔴 备份 |

---

## 🎯 你的项目架构

### 正确的设置（生产环境）

```
┌─────────────────────────────────────┐
│  前端 (React/Vite)                  │
│  端口: 5173                         │
│  URL: http://localhost:5173         │
└────────────┬────────────────────────┘
             │ 调用API
             ↓
┌─────────────────────────────────────┐
│  后端 API (FastAPI + 数据库)        │
│  端口: 8001  ← 这个！                │
│  URL: http://localhost:8001         │
│  文件: server.py (根目录)           │
└────────────┬────────────────────────┘
             │ 查询数据
             ↓
┌─────────────────────────────────────┐
│  SQLite 数据库                      │
│  文件: database_system/.../dev.db   │
└─────────────────────────────────────┘
```

### 开发调试设置（前端独立）

```
┌─────────────────────────────────────┐
│  前端 (React/Vite)                  │
│  端口: 5173                         │
└────────────┬────────────────────────┘
             │ 调用模拟API
             ↓
┌─────────────────────────────────────┐
│  前端调试API (Mock数据)             │
│  端口: 8000  ← 前端专用              │
│  文件: frontend/.../backend/server.py│
└─────────────────────────────────────┘
```

---

## 🔧 如何修改端口

### 方式1：直接修改代码

编辑文件最后一行：

```python
# server.py (根目录)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # ← 改这里
    #                                    ^^^^
    #                                    修改端口号
```

**示例：改为9000端口**
```python
uvicorn.run(app, host="0.0.0.0", port=9000)
```

### 方式2：启动时指定端口

```powershell
# 使用uvicorn命令指定端口
uvicorn server:app --port 9000

# 或
python -m uvicorn server:app --port 9000
```

---

## 📋 端口冲突问题

### 问题：端口被占用

```
Error: [Errno 10048] Address already in use
```

### 解决方法

**步骤1：查找占用端口的进程**

```powershell
# 查找8001端口
netstat -ano | findstr :8001

# 输出示例：
# TCP    0.0.0.0:8001    0.0.0.0:0    LISTENING    12345
#                                                    ^^^^^ PID
```

**步骤2：停止进程**

```powershell
# 停止特定进程
Stop-Process -Id 12345 -Force

# 或停止所有Python进程
Stop-Process -Name python -Force
```

**步骤3：检查端口是否释放**

```powershell
netstat -ano | findstr :8001
# 应该没有输出
```

---

## 🎯 你当前的问题

### 问题：运行了错误的server.py

**你运行的：**
```powershell
PS C:\Users\Mayn\AILanguageLearning-main\frontend\my-web-ui\backend> python server.py
                                           ^^^^^^^^^^^^^^^^^^^^^^
                                           错误的目录！
```

这个server.py：
- 在 `frontend/my-web-ui/backend/` 目录
- 端口：8000
- 功能：前端调试用
- **没有vocab-verbose路由** ❌

**应该运行：**
```powershell
PS C:\Users\Mayn\AILanguageLearning-main> python server.py
                                          ^^^^^^^^^^^^^^
                                          项目根目录！
```

这个server.py：
- 在项目根目录
- 端口：8001
- 功能：完整后端API + 数据库
- **包含vocab-verbose路由** ✅

---

## ✅ 解决步骤

### 1. 停止错误的服务器

```powershell
# 停止8000端口的服务器
Stop-Process -Name python -Force
```

### 2. 切换到正确目录

```powershell
# 返回项目根目录
cd C:\Users\Mayn\AILanguageLearning-main

# 确认目录（应该看到server.py）
ls server.py
```

### 3. 启动正确的服务器

```powershell
python server.py
```

**你应该看到：**
```
============================================================
Starting FastAPI Server...
============================================================
Server Address: http://localhost:8001  ← 8001端口！
...
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 4. 测试

浏览器访问：
```
http://localhost:8001/docs
```

找到 `vocab-verbose` 标签并测试！

---

## 🔄 如何切换端口

### 场景1：想用其他端口（比如9000）

**修改 server.py（根目录）：**

```python
# server.py 最后一行
uvicorn.run(app, host="0.0.0.0", port=9000)  # 改为9000
```

然后启动：
```powershell
python server.py
# 现在服务器运行在 http://localhost:9000
```

### 场景2：临时使用其他端口

不修改代码，启动时指定：

```powershell
uvicorn server:app --port 9000 --reload
```

---

## 📊 端口使用建议

### 开发环境标准端口

| 服务 | 推荐端口 | 原因 |
|------|---------|------|
| 前端（Vite） | 5173 | Vite默认 |
| 后端API | 8000-9000 | 常用范围 |
| 数据库 | 3306/5432/27017 | 各数据库默认 |

### 你的项目

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端UI | 5173 | React界面 |
| **后端API（数据库）** | **8001** | **主要使用** ✅ |
| 前端调试API | 8000 | 前端独立开发 |

---

## 🛠️ 实用工具脚本

我创建了一个端口检查脚本：

```powershell
.\check_ports.ps1
```

会显示：
- 哪些端口正在使用
- 对应的进程ID
- 如何停止进程

---

## 🎓 总结

### 端口概念
- **端口 = 房间号**
- 同一电脑可以运行多个服务器，每个占用不同端口
- 端口号范围：0-65535（常用：1024-49151）

### 你的项目
- **8000端口**：前端调试API（`frontend/my-web-ui/backend/server.py`）
- **8001端口**：后端真实API（**根目录** `server.py`）✅
- **5173端口**：前端UI（Vite）

### 如何切换
1. **修改代码**：改 `uvicorn.run(..., port=xxxx)`
2. **命令行指定**：`uvicorn server:app --port xxxx`
3. **环境变量**：`export PORT=xxxx` (Linux/Mac)

### 查看端口
```powershell
# 查看特定端口
netstat -ano | findstr :8001

# 停止占用进程
Stop-Process -Id <PID> -Force
```

---

## ✅ 现在开始

**在项目根目录运行：**

```powershell
cd C:\Users\Mayn\AILanguageLearning-main
python server.py
```

**访问：**
```
http://localhost:8001/docs
```

**测试详细日志：**
```
http://localhost:8001/api/v2/vocab-verbose/1
```

**切回PowerShell窗口查看详细的转换日志！** 🎉
