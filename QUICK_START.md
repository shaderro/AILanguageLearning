# 快速开始 - 查看详细日志

## ✅ 完整步骤（从零开始）

### 步骤1：打开第一个PowerShell窗口

```powershell
# 进入项目目录
cd C:\Users\Mayn\AILanguageLearning-main

# 启动服务器
python server.py
```

**看到这个输出就成功了：**
```
============================================================
Starting FastAPI Server...
============================================================

Server Address: http://localhost:8001
...
INFO:     Uvicorn running on http://0.0.0.0:8001
```

⚠️ **重要：保持这个窗口开着！不要关闭！**

---

### 步骤2：在浏览器中测试（最简单）

打开浏览器，访问：

```
http://localhost:8001/docs
```

找到 **vocab-verbose** 标签，测试任意端点。

**然后立即切换回PowerShell窗口1，查看详细日志！**

---

### 步骤3（可选）：使用第二个PowerShell窗口测试

**打开第二个PowerShell窗口：**

```powershell
# 进入项目目录
cd C:\Users\Mayn\AILanguageLearning-main

# 运行测试脚本
.\test_verbose_api.ps1
```

或者手动测试：

```powershell
# 测试获取词汇
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab-verbose/1" -Method Get
```

**立即切换回窗口1查看日志！**

---

## 🎯 最简单的方法

1. **窗口1：启动服务器**
   ```powershell
   cd C:\Users\Mayn\AILanguageLearning-main
   python server.py
   ```

2. **浏览器：访问Swagger**
   ```
   http://localhost:8001/docs
   ```

3. **在Swagger中点击测试，然后立即看窗口1的日志**

就这么简单！

---

## ⚠️ 常见问题

### Q: "无法连接到远程服务器"

**原因：** 服务器没有运行

**解决：** 
1. 检查窗口1是否显示 "Uvicorn running"
2. 如果没有，重新运行 `python server.py`

### Q: 看不到详细日志

**原因：** 使用了普通端点而不是verbose端点

**解决：** 
- 使用 `/api/v2/vocab-verbose/` 而不是 `/api/v2/vocab/`
- 在Swagger中找 **vocab-verbose** 标签

---

## 📊 你会看到的详细日志

```
🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵
[FastAPI] 新的API请求进入
🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵🔵

======================================================================
[VocabManagerDB] 初始化完成
======================================================================

======================================================================
[STEP] 开始获取词汇: ID=1
======================================================================

[步骤1] 从数据库获取 ORM Model
  source: SourceType.AUTO (类型: SourceType)  ← 枚举

[步骤2] 使用 VocabAdapter 转换: Model → DTO
  转换 source: SourceType枚举 → 字符串
  SourceType.AUTO → 'auto'  ← 关键转换！

[步骤2.3] VocabDTO 字段详情:
  source: 'auto' (类型: str)  ← 已经是字符串

[转换前后对比]:
  source类型    | SourceType    | str

[完成] 返回 VocabDTO 给 FastAPI
```

---

## ✅ 成功标志

- ✅ 服务器窗口显示详细的步骤日志
- ✅ 清楚看到 `SourceType.AUTO` → `'auto'` 的转换
- ✅ 理解了为什么FastAPI不需要处理转换

---

## 🔄 如果需要重启

```powershell
# 停止服务器（在服务器窗口按 Ctrl+C）

# 或者强制停止
Stop-Process -Name python -Force

# 重新启动
python server.py
```

---

现在开始吧！只需要2个窗口：
1. **PowerShell运行服务器**
2. **浏览器访问 http://localhost:8001/docs**

