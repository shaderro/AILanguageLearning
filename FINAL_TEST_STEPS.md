# 🧪 用户数据隔离最终测试步骤

## ✅ 已修复
- 前端请求拦截器现在会自动添加 Authorization Bearer token

## 📋 完整测试流程

### 1. 重启前端
**重要：必须重新编译前端！**

```powershell
# 停止前端（如果正在运行）
# 按 Ctrl+C

# 重新启动前端
cd frontend/my-web-ui
npm run dev
```

### 2. 清空浏览器缓存
- 打开浏览器控制台（F12）
- 右键刷新按钮 → "清空缓存并硬性重新加载"
- 或者按 Ctrl + Shift + Delete 清除缓存

### 3. 测试 User 1（应该看到数据）

#### 3.1 登录
1. 访问 http://localhost:5173
2. 点击右上角"登录"
3. 输入：
   - User ID: `1`
   - 密码: `test123456`
4. 点击"登录"
5. ✅ 应该成功登录，显示 "User 1"

#### 3.2 查看词汇
1. 导航到词汇页面（或查看词汇列表）
2. ✅ 应该看到 **41 条词汇**
3. 打开浏览器控制台，查看请求：
   ```
   🌐 API Request: GET /api/v2/vocab/
   🔑 Added Authorization header  ← 应该看到这行！
   ```

#### 3.3 验证 Token
- 在控制台执行：
  ```javascript
  localStorage.getItem('access_token')
  ```
- 应该返回一个 JWT token（长字符串）

### 4. 测试 User 2（数据隔离验证）

#### 4.1 退出并登录 User 2
1. 点击右上角用户名 → 退出登录
2. 重新登录：
   - User ID: `2`
   - 密码: `mypassword123`
3. ✅ 应该成功登录，显示 "User 2"

#### 4.2 验证数据隔离
1. 查看词汇列表
2. ✅ 应该看到 **0 条词汇**（数据隔离成功！）
3. 控制台应该显示：
   ```
   🌐 API Request: GET /api/v2/vocab/
   🔑 Added Authorization header
   Status: 200 OK
   Response: { data: [], count: 0 }
   ```

#### 4.3 创建测试数据
1. User 2 创建词汇：
   - 词汇: `apple`
   - 解释: `水果：苹果`
2. ✅ 创建成功
3. 刷新页面
4. ✅ 应该看到 1 条词汇

### 5. 测试独立性

#### 5.1 切换回 User 1
1. 退出登录
2. 登录 User 1
3. 查看词汇列表
4. ✅ 应该看到 **41 条词汇**（不包含 User 2 的 "apple"）

#### 5.2 User 1 也创建 "apple"
1. User 1 创建词汇：
   - 词汇: `apple`
   - 解释: `苹果公司`
2. ✅ 应该创建成功（唯一约束是用户级别）
3. ✅ 现在 User 1 有 42 条词汇

#### 5.3 再次验证隔离
1. 切换到 User 2
2. 查看 "apple"
3. ✅ User 2 只能看到自己的 "apple"（解释：水果：苹果）
4. 切换回 User 1
5. ✅ User 1 只能看到自己的 "apple"（解释：苹果公司）

### 6. 测试交叉访问保护

#### 6.1 获取 User 1 的某个 vocab_id
1. 登录 User 1
2. 打开浏览器控制台
3. 查看某个词汇的详情，记录 `vocab_id`（如 `vocab_id=5`）

#### 6.2 尝试用 User 2 访问
1. 切换到 User 2
2. 在控制台执行：
   ```javascript
   fetch('http://localhost:8001/api/v2/vocab/5', {
     headers: {
       'Authorization': `Bearer ${localStorage.getItem('access_token')}`
     }
   }).then(r => r.json()).then(console.log)
   ```
3. ✅ 应该返回 **404 Not Found**（访问被拒绝！）

## ✅ 成功标准

1. ✅ User 1 登录后看到 41 条词汇
2. ✅ User 2 登录后看到 0 条词汇
3. ✅ 两个用户可以创建同名词汇
4. ✅ 用户只能看到自己的数据
5. ✅ 用户不能访问其他人的数据（404）
6. ✅ 请求头包含 `Authorization: Bearer <token>`

## ❌ 如果还是失败

### 检查清单

1. **前端是否重新编译？**
   ```powershell
   # 停止前端后重新运行
   npm run dev
   ```

2. **浏览器缓存是否清空？**
   - Ctrl + Shift + R（硬刷新）

3. **Token 是否存在？**
   ```javascript
   localStorage.getItem('access_token')
   ```

4. **请求头是否包含 Authorization？**
   - 打开 Network 标签
   - 查看请求头

5. **后端是否报错？**
   - 查看后端终端日志

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 403 Forbidden | Token 缺失或无效 | 重新登录获取新 token |
| 401 Unauthorized | Token 过期 | 重新登录 |
| 404 Not Found | vocab_id 不属于当前用户 | 正常（说明隔离生效） |
| 500 Server Error | 后端代码错误 | 查看后端日志 |

把错误信息发给我，我会立即修复！

