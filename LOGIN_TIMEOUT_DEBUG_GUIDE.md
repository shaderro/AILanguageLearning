# 登录超时问题诊断指南

## 🔍 问题描述

线上版本有时会出现登录请求超时失败的问题，前端显示 `timeout of 30000ms exceeded`。

## 📊 已实施的优化

### 1. 后端日志增强
- ✅ 添加了详细的性能监控日志
- ✅ 记录请求开始时间
- ✅ 记录数据库查询耗时
- ✅ 记录密码验证耗时
- ✅ 记录 Token 生成耗时
- ✅ 记录总耗时

### 2. 数据库配置优化
- ✅ 添加了查询超时设置（25秒，略小于前端30秒超时）
- ✅ 优化了连接池配置
- ✅ 添加了连接前检查（pool_pre_ping）

### 3. 前端日志增强
- ✅ 添加了请求拦截器，记录请求开始时间
- ✅ 添加了响应拦截器，记录请求耗时
- ✅ 详细记录超时错误信息

## 🔎 如何定位问题

### 步骤 1: 查看后端日志

当登录超时发生时，查看后端日志，应该能看到类似以下的信息：

```
🔐 [Login API] 登录请求开始: email=xxx@example.com
🔍 [Login API] 使用 email 查询: xxx@example.com
⏱️ [Login API] 数据库查询耗时: X.XXX秒
✅ [Login API] 用户找到: user_id=X, email=xxx@example.com
⏱️ [Login API] 密码验证耗时: X.XXX秒
⏱️ [Login API] Token 生成耗时: X.XXX秒
✅ [Login API] 登录成功: user_id=X, 总耗时: X.XXX秒
```

**关键指标：**
- 如果**没有看到任何日志** → 请求可能没有到达后端（网络问题、CORS、代理问题）
- 如果**数据库查询耗时很长**（> 5秒）→ 数据库连接或查询性能问题
- 如果**总耗时接近30秒** → 某个步骤很慢，需要进一步优化

### 步骤 2: 查看前端日志

前端控制台应该显示：

```
📤 [authApi] 请求开始: POST /api/auth/login
📥 [authApi] 请求完成: POST /api/auth/login, 耗时: XXXms
```

如果超时：
```
❌ [authApi] 请求失败: POST /api/auth/login, 耗时: 30000ms
⏱️ [authApi] 请求超时详情: { url, method, timeout, duration, message }
```

### 步骤 3: 检查数据库连接

如果数据库查询耗时很长，检查：

1. **数据库连接池状态**
   - 连接池是否已满？
   - 是否有连接泄漏？

2. **数据库性能**
   - 数据库服务器负载是否过高？
   - 网络延迟是否正常？
   - 是否有慢查询？

3. **环境变量**
   - `DATABASE_URL` 是否正确？
   - `ENV` 环境变量是否正确？

### 步骤 4: 检查网络

1. **CORS 配置**
   - 检查后端 CORS 配置是否正确
   - 检查前端 API_BASE_URL 是否正确

2. **代理/防火墙**
   - 检查是否有代理或防火墙阻止请求
   - 检查网络延迟

3. **SSL/TLS**
   - 如果使用 HTTPS，检查证书是否有效

## 🛠️ 可能的解决方案

### 方案 1: 增加超时时间（临时方案）

如果确认是网络延迟问题，可以临时增加前端超时时间：

```javascript
// frontend/my-web-ui/src/modules/auth/services/authService.js
timeout: 60000, // 增加到 60 秒
```

**注意：** 这只是临时方案，根本问题是需要优化数据库查询或网络连接。

### 方案 2: 优化数据库查询

如果数据库查询很慢：

1. **添加索引**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
   CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id);
   ```

2. **优化查询逻辑**
   - 确保查询使用了索引
   - 避免全表扫描

### 方案 3: 优化数据库连接

1. **增加连接池大小**
   ```python
   pool_size=10,  # 从 5 增加到 10
   max_overflow=20,  # 从 10 增加到 20
   ```

2. **调整连接回收时间**
   ```python
   pool_recycle=1800,  # 从 3600 秒减少到 1800 秒（30分钟）
   ```

### 方案 4: 添加重试机制

如果确认是临时网络问题，可以添加重试机制：

```javascript
// 在 authService.js 中添加重试逻辑
login: async (userId, password, email = null) => {
  const maxRetries = 2
  let lastError = null
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      const requestBody = { password }
      if (userId) requestBody.user_id = userId
      if (email) requestBody.email = email
      
      const response = await authApi.post('/api/auth/login', requestBody)
      return response.data
    } catch (error) {
      lastError = error
      if (i < maxRetries && (error.code === 'ECONNABORTED' || error.message?.includes('timeout'))) {
        console.log(`🔄 [authService] 登录超时，重试 ${i + 1}/${maxRetries}...`)
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))) // 递增延迟
        continue
      }
      throw error
    }
  }
  
  throw lastError
}
```

## 📝 需要收集的信息

当问题再次发生时，请收集以下信息：

1. **后端日志**（完整的登录请求日志）
2. **前端控制台日志**（包括请求开始、完成、错误信息）
3. **网络时间线**（浏览器开发者工具 Network 标签）
4. **数据库状态**（连接数、查询时间等）
5. **环境信息**（ENV、DATABASE_URL、API_BASE_URL）

## 🎯 下一步行动

1. ✅ 部署更新后的代码（包含日志和优化）
2. ⏳ 监控日志，等待问题再次发生
3. ⏳ 根据日志定位具体问题
4. ⏳ 实施针对性的解决方案

## 📞 联系支持

如果问题持续存在，请提供：
- 完整的后端日志
- 完整的前端控制台日志
- 网络时间线截图
- 问题发生的时间和环境信息
