# 🎯 如何启动正确的服务器并看到详细日志

## ❌ 你现在的问题

**你的PowerShell显示：**
```
PS C:\Users\Mayn\AILanguageLearning-main\frontend\my-web-ui\backend>
```

**你运行了：**
```powershell
python server.py
```

**结果：**
- 启动的是前端调试服务器
- 端口：8000 ❌
- 没有详细日志 ❌
- 没有vocab-verbose路由 ❌

---

## ✅ 正确的做法

### 第1步：切换到正确的目录

**在你的PowerShell中运行：**

```powershell
cd C:\Users\Mayn\AILanguageLearning-main
```

**确认目录正确：**
```powershell
pwd
```

**应该显示：**
```
Path
----
C:\Users\Mayn\AILanguageLearning-main
```

**不应该是：**
```
❌ C:\Users\Mayn\AILanguageLearning-main\frontend\my-web-ui\backend
```

---

### 第2步：启动服务器

```powershell
python server.py
```

**正确的输出应该是：**
```
============================================================
Starting FastAPI Server...
============================================================

Server Address: http://localhost:8001  ← 8001端口！
API Documentation: http://localhost:8001/docs
Health Check: http://localhost:8001/api/health

Press Ctrl+C to stop the server

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001  ← 8001！
```

**如果你看到 8000，说明目录错了！**

---

### 第3步：测试详细日志

**保持PowerShell窗口可见！**

然后在浏览器访问：
```
http://localhost:8001/api/v2/vocab-verbose/1
```

**立即切换回PowerShell窗口！**

你会看到完整的转换日志：
```
[FastAPI] 新的API请求进入
[FastAPI] 创建数据库 Session...

======================================================================
[VocabManagerDB] 初始化完成
======================================================================

[步骤1] 从数据库获取 ORM Model
  source: SourceType.AUTO (类型: SourceType)

[步骤2] 使用 VocabAdapter 转换: Model → DTO
  SourceType.AUTO → 'auto'

[步骤3] VocabDTO 字段详情:
  source: 'auto' (类型: str)

[转换前后对比]:
  source类型    | SourceType    | str

[完成] 返回 VocabDTO 给 FastAPI
```

---

## 🎯 一张图看懂

### 错误的启动方式 ❌

```
你的位置: frontend\my-web-ui\backend\
运行命令: python server.py
          ↓
启动了: frontend\my-web-ui\backend\server.py
端口: 8000
功能: 前端调试API（Mock数据）
日志: 没有详细转换日志
```

### 正确的启动方式 ✅

```
你的位置: AILanguageLearning-main\ (项目根目录)
运行命令: python server.py
          ↓
启动了: AILanguageLearning-main\server.py
端口: 8001
功能: 后端真实API（连接数据库）
日志: 有详细转换日志！✨
```

---

## 📋 检查清单

在启动服务器前，确认：

```powershell
# 1. 检查当前目录
pwd
# 应该是：C:\Users\Mayn\AILanguageLearning-main

# 2. 列出文件，确认server.py存在
ls server.py
# 应该能看到文件

# 3. 检查端口是否被占用
netstat -ano | findstr :8001
# 应该没有输出（端口空闲）

# 4. 启动服务器
python server.py

# 5. 检查端口（应该是8001）
# 看输出中的 "Uvicorn running on http://0.0.0.0:8001"
```

---

## 🆘 如果还是8000端口

### 可能原因1：目录错误

```powershell
# 检查目录
pwd

# 如果不是根目录，切换
cd C:\Users\Mayn\AILanguageLearning-main
```

### 可能原因2：运行了错误的文件

```powershell
# 确保运行的是根目录的server.py
Get-Content server.py -Head 5

# 应该看到：
# #!/usr/bin/env python3
# """
# Asked Tokens API 服务器
# 专门处理 asked tokens 相关的 API 端点
# """
```

### 可能原因3：多个Python进程

```powershell
# 停止所有Python进程
Stop-Process -Name python -Force

# 重新启动
python server.py
```

---

## 🎉 成功的标志

### PowerShell输出

```
============================================================
Starting FastAPI Server...
============================================================

Server Address: http://localhost:8001  ← 必须是8001
API Documentation: http://localhost:8001/docs
...
INFO:     Uvicorn running on http://0.0.0.0:8001  ← 必须是8001
```

### 浏览器测试

访问：`http://localhost:8001/docs`

应该看到 `vocab-verbose` 标签

### 详细日志测试

1. 访问：`http://localhost:8001/api/v2/vocab-verbose/1`
2. 切换回PowerShell窗口
3. 看到详细的转换日志

---

## 💡 记住

- **项目根目录** = `C:\Users\Mayn\AILanguageLearning-main`
- **正确的server.py** = 根目录下的 `server.py`
- **正确的端口** = 8001（不是8000）
- **详细日志端点** = `/api/v2/vocab-verbose/`

现在试试：
```powershell
cd C:\Users\Mayn\AILanguageLearning-main
python server.py
```

应该看到8001端口！🚀

