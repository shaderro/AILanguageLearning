# Vocab API 验证指南（PowerShell）

## 📋 准备工作

确保你在项目根目录：`C:\Users\Mayn\AILanguageLearning-main`

---

## 🚀 方式1：使用PowerShell脚本（推荐）

### 步骤1：打开第一个PowerShell窗口 - 启动后端

```powershell
# 在项目根目录运行
.\start_backend.ps1
```

**预期输出：**
```
================================
启动 FastAPI 后端服务器
================================

服务器将在以下地址运行:
  - API地址: http://localhost:8001
  - Swagger文档: http://localhost:8001/docs
  - 健康检查: http://localhost:8001/api/health

按 Ctrl+C 停止服务器

INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

✅ **保持这个窗口运行！**

---

### 步骤2：打开第二个PowerShell窗口 - 测试API

在**新的PowerShell窗口**中：

```powershell
.\test_api.ps1
```

**预期输出：**
```
================================
测试 Vocab API
================================

[1] 测试健康检查...
  [OK] 服务器健康状态: healthy
  [OK] Vocab服务: active (database)

[2] 测试获取词汇列表...
  [OK] 获取成功: 3 个词汇
  第一个词汇:
    - ID: 1
    - 内容: challenging
    - 来源: auto
    - 收藏: True

[3] 测试搜索功能...
  [OK] 搜索成功: 找到 2 个结果

[4] 测试统计功能...
  [OK] 统计获取成功:
    - 总词汇: 29
    - 收藏: 2
    - 自动生成: 29
    - 手动添加: 0

================================
测试完成
================================

你现在可以访问:
  - Swagger UI: http://localhost:8001/docs
  - 在浏览器中测试所有API端点
```

---

### 步骤3：在浏览器中验证

打开浏览器访问：

**Swagger UI（交互式API文档）：**
```
http://localhost:8001/docs
```

你会看到所有API端点，可以直接测试：
- GET /api/v2/vocab/ - 获取所有词汇
- GET /api/v2/vocab/{id} - 获取单个词汇
- POST /api/v2/vocab/ - 创建词汇
- 等等...

**API健康检查：**
```
http://localhost:8001/api/health
```

---

### 步骤4：启动前端（可选）

在**第三个PowerShell窗口**中：

```powershell
.\start_frontend.ps1
```

**预期输出：**
```
================================
启动前端开发服务器
================================

正在切换到前端目录...

前端将在以下地址运行:
  - 前端地址: http://localhost:5173

按 Ctrl+C 停止服务器

  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

然后访问：`http://localhost:5173`

---

## 🔧 方式2：手动命令（逐步验证）

### 步骤1：启动后端

```powershell
# 在项目根目录
python server.py
```

### 步骤2：验证服务器（新窗口）

```powershell
# 测试健康检查
Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method Get | ConvertTo-Json

# 测试获取词汇
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/?limit=5" -Method Get | ConvertTo-Json -Depth 5

# 测试搜索
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/search/?keyword=test" -Method Get | ConvertTo-Json

# 测试统计
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/stats/summary" -Method Get | ConvertTo-Json
```

### 步骤3：测试创建词汇

```powershell
$body = @{
    vocab_body = "powershell_test"
    explanation = "通过PowerShell创建的测试词汇"
    source = "manual"
    is_starred = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json
```

### 步骤4：查询刚创建的词汇

```powershell
# 假设返回的ID是30
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/30" -Method Get | ConvertTo-Json -Depth 5
```

### 步骤5：删除测试词汇

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/v2/vocab/30" -Method Delete | ConvertTo-Json
```

---

## 📊 验证数据转换

### 运行Python验证脚本

```powershell
# 验证数据转换过程
python verify_vocab_conversion.py
```

**查看输出：**
- Model.source: SourceType.AUTO (枚举)
- DTO.source: 'auto' (字符串)
- 转换成功！

---

## 🌐 在Swagger UI中测试

### 1. 访问Swagger UI

```
http://localhost:8001/docs
```

### 2. 测试"获取所有词汇"

1. 找到 `GET /api/v2/vocab/` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 设置参数：
   - skip: 0
   - limit: 5
   - starred_only: false
5. 点击 **"Execute"**
6. 查看响应

**验证要点：**
- ✅ `source` 字段是字符串（"auto"/"qa"/"manual"）
- ✅ `examples` 字段是数组
- ✅ 响应格式正确

### 3. 测试"创建词汇"

1. 找到 `POST /api/v2/vocab/` 端点
2. 点击展开
3. 点击 **"Try it out"**
4. 在 Request body 输入：

```json
{
  "vocab_body": "swagger_test_vocab",
  "explanation": "通过Swagger创建的测试词汇",
  "source": "manual",
  "is_starred": true
}
```

5. 点击 **"Execute"**
6. 记下返回的 `vocab_id`

### 4. 测试"查询词汇"

1. 找到 `GET /api/v2/vocab/{vocab_id}` 端点
2. 输入刚才创建的 `vocab_id`
3. 点击 **"Execute"**
4. 验证返回的数据

### 5. 测试"删除词汇"

1. 找到 `DELETE /api/v2/vocab/{vocab_id}` 端点
2. 输入要删除的 `vocab_id`
3. 点击 **"Execute"**

---

## ✅ 验证清单

完成以下检查：

### 后端验证
- [ ] 服务器成功启动（端口8001）
- [ ] 健康检查返回正常
- [ ] 可以获取词汇列表
- [ ] 可以获取单个词汇
- [ ] 可以创建词汇
- [ ] 可以更新词汇
- [ ] 可以删除词汇
- [ ] 搜索功能正常
- [ ] 统计功能正常

### 数据格式验证
- [ ] `source` 字段是字符串（不是枚举或数字）
- [ ] `examples` 字段是数组（不是对象）
- [ ] `token_indices` 是数组（不是字符串）
- [ ] `is_starred` 是布尔值

### Swagger UI验证
- [ ] 可以访问 http://localhost:8001/docs
- [ ] 可以看到所有API端点
- [ ] 可以在Swagger中测试API
- [ ] 请求和响应格式正确

### 数据转换验证
- [ ] 运行 `verify_vocab_conversion.py` 成功
- [ ] 看到 Model → DTO 转换过程
- [ ] 枚举类型正确转换为字符串

---

## 🔍 查看详细转换过程

如果想看详细的数据转换步骤：

```powershell
python test_vocab_flow_detailed.py
```

这会展示：
1. 数据库连接
2. VocabManagerDB创建
3. Model → DTO 转换
4. 创建、查询、更新、删除流程
5. 例句关联
6. FastAPI返回格式

---

## ⚠️ 常见问题

### Q1: 端口被占用

**错误：** `Error: [Errno 10048] Address already in use`

**解决：**
```powershell
# 查找占用8001端口的进程
netstat -ano | findstr :8001

# 停止进程（替换PID）
Stop-Process -Id <PID> -Force
```

### Q2: Python命令未找到

**错误：** `python : 无法将"python"项识别为 cmdlet`

**解决：**
```powershell
# 使用完整路径
py server.py

# 或者
python.exe server.py
```

### Q3: 无法加载脚本

**错误：** `无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本`

**解决：**
```powershell
# 以管理员身份运行PowerShell，然后执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或者直接运行命令而不是脚本
python server.py
```

### Q4: 前端启动失败

**错误：** `npm : 无法将"npm"项识别为 cmdlet`

**解决：**
```powershell
# 检查Node.js是否安装
node --version
npm --version

# 如果未安装，需要先安装Node.js
```

---

## 📝 快速命令参考

```powershell
# 启动后端
.\start_backend.ps1

# 测试API
.\test_api.ps1

# 启动前端
.\start_frontend.ps1

# 验证数据转换
python verify_vocab_conversion.py

# 查看详细流程
python test_vocab_flow_detailed.py

# 直接测试API（一行命令）
Invoke-RestMethod http://localhost:8001/api/health | ConvertTo-Json

# 获取词汇列表
Invoke-RestMethod http://localhost:8001/api/v2/vocab/ | ConvertTo-Json
```

---

## 🎯 验证成功标志

如果看到以下内容，说明一切正常：

1. ✅ 服务器启动成功
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8001
   ```

2. ✅ 测试脚本全部通过
   ```
   [OK] 服务器健康状态: healthy
   [OK] 获取成功: X 个词汇
   [OK] 搜索成功: 找到 X 个结果
   [OK] 统计获取成功
   ```

3. ✅ Swagger UI可以访问并测试

4. ✅ 数据格式正确
   - source 是字符串
   - examples 是数组

---

## 🎉 完成

完成以上步骤后，你已经成功验证了：

- ✅ 后端FastAPI服务器正常运行
- ✅ 所有API端点工作正常
- ✅ 数据转换正确（枚举→字符串）
- ✅ 数据库连接正常
- ✅ CRUD操作正常

现在可以开始前端集成或适配其他功能了！

