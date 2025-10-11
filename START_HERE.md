# 🚀 快速开始 - 3步验证Vocab API

## 准备

确保你在项目根目录：`C:\Users\Mayn\AILanguageLearning-main`

---

## ✅ 方式1：使用PowerShell脚本（最简单）

### 第1步：启动后端

**打开第一个PowerShell窗口**，运行：

```powershell
.\start_backend.ps1
```

看到这样的输出就成功了：
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

⚠️ **保持这个窗口开着，不要关闭！**

---

### 第2步：测试API

**打开第二个PowerShell窗口**（保持第一个运行），运行：

```powershell
.\test_api.ps1
```

如果看到这样的输出，说明成功：
```
[1] 测试健康检查...
  [OK] 服务器健康状态: healthy
  [OK] Vocab服务: active (database)

[2] 测试获取词汇列表...
  [OK] 获取成功: X 个词汇
```

---

### 第3步：在浏览器中测试

打开浏览器，访问：

```
http://localhost:8001/docs
```

你会看到Swagger UI（交互式API文档），可以直接测试所有API端点！

---

## ✅ 方式2：手动启动（如果脚本不工作）

### 第1步：启动后端

**PowerShell窗口1：**

```powershell
python server.py
```

等待看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

⚠️ **保持这个窗口开着！**

---

### 第2步：测试健康检查

**PowerShell窗口2：**

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method Get
```

应该看到：
```
status  : healthy
message : Language Learning API is running
services: @{asked_tokens=active; vocab_v2=active (database)}
```

---

### 第3步：测试获取词汇

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/?limit=3" -Method Get
```

应该看到词汇列表！

---

### 第4步：浏览器测试

访问：`http://localhost:8001/docs`

---

## 📋 验证要点

在Swagger UI中测试任意API端点，验证：

1. ✅ **source字段是字符串**
   ```json
   "source": "auto"  // 不是数字，不是枚举
   ```

2. ✅ **examples字段是数组**
   ```json
   "examples": [...]  // 不是对象
   ```

3. ✅ **所有操作正常**
   - 可以获取词汇
   - 可以创建词汇
   - 可以搜索词汇

---

## ⚠️ 如果遇到问题

### 问题1：端口被占用

```
Error: Address already in use
```

**解决方法：**

```powershell
# 查找占用8001端口的进程
netstat -ano | findstr :8001

# 找到PID后，停止进程
Stop-Process -Id <PID> -Force
```

---

### 问题2：Python未找到

```
python : 无法将"python"项识别为 cmdlet
```

**解决方法：**

```powershell
# 尝试使用py命令
py server.py

# 或者使用完整路径
python.exe server.py
```

---

### 问题3：无法加载PowerShell脚本

```
无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本
```

**解决方法A：** 修改执行策略（推荐）

```powershell
# 以管理员身份运行PowerShell，然后执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**解决方法B：** 直接运行命令（不用脚本）

```powershell
# 直接运行Python命令
python server.py
```

---

## 🎯 成功标志

如果你看到：

1. ✅ 服务器输出：`INFO:     Uvicorn running on http://0.0.0.0:8001`
2. ✅ 测试脚本输出：`[OK] 服务器健康状态: healthy`
3. ✅ 浏览器可以访问：`http://localhost:8001/docs`
4. ✅ 在Swagger中可以测试API并看到正确的响应

**恭喜！验证成功！** 🎉

---

## 📚 更多信息

- 详细验证步骤：`VERIFICATION_GUIDE.md`
- Swagger测试指南：`SWAGGER_TEST_GUIDE.md`
- 前端集成指南：`FRONTEND_INTEGRATION_GUIDE.md`
- 完整文档：`VOCAB_DATABASE_COMPLETE.md`

---

## 🔜 下一步

验证成功后，你可以：

1. **在Swagger UI中测试**
   - 创建词汇
   - 查询词汇
   - 搜索词汇
   - 查看统计

2. **启动前端**（可选）
   ```powershell
   .\start_frontend.ps1
   ```
   然后访问：`http://localhost:5173`

3. **查看数据转换过程**
   ```powershell
   python verify_vocab_conversion.py
   ```
   看到 Model(枚举) → DTO(字符串) 的转换

---

## 💡 提示

- 后端必须一直运行才能测试
- 使用 **Ctrl+C** 停止服务器
- Swagger UI是测试API最简单的方式
- 所有数据转换都在后端自动完成，前端只需调用API

