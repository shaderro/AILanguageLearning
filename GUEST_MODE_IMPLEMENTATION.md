# 游客模式实现完成

## ✅ 已实现功能

### 游客ID自动创建
- 首次访问时自动生成游客ID：`guest_xxxxx`
- 保存到 localStorage（持久化）
- 退出登录后切换回游客模式

### UserContext 增强
- 新增 `isGuest` 状态
- 支持游客模式和登录模式切换
- 自动管理游客ID生命周期

## 🔄 用户流程

### 场景1：首次访问
```
打开应用
  ↓
UserContext 初始化
  ↓
检查 localStorage
  ↓
没有 userId 和 token
  ↓
创建游客ID：guest_abc12345
  ↓
保存到 localStorage
  ↓
设置 isGuest = true
  ↓
✅ 游客模式激活
```

### 场景2：游客登录
```
游客模式（guest_abc12345）
  ↓
点击"登录"
  ↓
输入 User ID: 1, 密码
  ↓
登录成功
  ↓
切换到 User 1
  ↓
isGuest = false
  ↓
✅ 正式用户模式
```

### 场景3：退出登录
```
User 1 登录中
  ↓
点击"退出"
  ↓
清除登录信息
  ↓
恢复游客ID：guest_abc12345
  ↓
isGuest = true
  ↓
✅ 切换回游客模式
```

### 场景4：再次访问
```
关闭浏览器
  ↓
重新打开应用
  ↓
检查 localStorage
  ↓
如果有 token：验证并自动登录
如果没有 token：使用游客ID（guest_abc12345）
  ↓
✅ 保持游客身份
```

## 📊 UserContext 状态

```javascript
{
  userId: 'guest_abc12345' | 1 | 2 | ...,
  token: null | 'eyJhbGc...',
  isAuthenticated: false | true,
  isGuest: true | false,
  isLoading: false,
  login: Function,
  register: Function,
  logout: Function
}
```

### 状态组合

| userId | token | isAuthenticated | isGuest | 说明 |
|--------|-------|-----------------|---------|------|
| `guest_xxx` | `null` | `false` | `true` | 游客模式 |
| `1` | `eyJ...` | `true` | `false` | User 1 登录 |
| `2` | `eyJ...` | `true` | `false` | User 2 登录 |

## 🎯 使用方式

### 组件中使用
```jsx
function MyComponent() {
  const { userId, isGuest, isAuthenticated } = useUser()
  
  if (isGuest) {
    return <div>👤 游客模式（ID: {userId}）</div>
  }
  
  return <div>👤 User {userId}</div>
}
```

### 条件渲染
```jsx
function ProtectedFeature() {
  const { isAuthenticated, isGuest } = useUser()
  
  if (isGuest) {
    return <div>请登录后使用此功能</div>
  }
  
  return <SecretContent />
}
```

### 显示登录提示
```jsx
function Header() {
  const { isGuest, userId } = useUser()
  
  return (
    <div>
      {isGuest ? (
        <span>👤 游客模式 | <a>立即登录</a></span>
      ) : (
        <span>👤 User {userId}</span>
      )}
    </div>
  )
}
```

## ⚠️ API 认证注意事项

由于 API 需要认证（Bearer token），游客模式下：

### 当前行为（需要 token）
- 游客访问需要认证的 API（如 `/api/v2/vocab/`）
- ❌ 返回 403 Forbidden（没有 token）

### 解决方案选项

**选项A：API 支持游客模式**
- 修改 API，允许无 token 访问
- 返回空数据或公共数据
- 适合：需要游客能查看数据的场景

**选项B：游客只能看登录提示**
- 游客模式下不调用需要认证的 API
- 显示"请登录后查看"提示
- 适合：必须登录才能使用的应用

**选项C：自动登录游客账号**
- 创建特殊的游客账号（如 User 0）
- 游客模式下自动登录此账号
- 获得真实的 token
- 适合：需要游客有基本功能的场景

### 当前实现
- ✅ 创建游客ID
- ⚠️ 游客没有 token，会触发 403
- 建议：在 useVocabList 和 useGrammarList 中添加判断

## 🔧 推荐的下一步

### 修改数据获取 Hooks
```javascript
// hooks/useApi.js
export const useVocabList = (userId = null) => {
  const { isGuest } = useUser()
  
  return useQuery({
    queryKey: queryKeys.vocab.all(userId),
    queryFn: apiService.getVocabList,
    enabled: userId !== null && !isGuest,  // 游客不查询
    staleTime: 5 * 60 * 1000,
  });
};
```

### 显示游客提示
```jsx
function WordDemo() {
  const { isGuest } = useUser()
  
  if (isGuest) {
    return (
      <div className="text-center p-8">
        <h2>请登录后查看词汇</h2>
        <button>立即登录</button>
      </div>
    )
  }
  
  // 正常显示数据...
}
```

## 🧪 测试步骤

1. **清空 localStorage**
   ```javascript
   localStorage.clear()
   location.reload()
   ```

2. **检查游客ID**
   ```javascript
   console.log('User ID:', localStorage.getItem('guest_user_id'))
   // 应该看到：guest_xxxxx
   ```

3. **登录转换**
   - 登录 User 1
   - ✅ 从游客模式切换到正式用户
   - ✅ isGuest = false

4. **退出恢复**
   - 点击退出
   - ✅ 切换回游客模式
   - ✅ 游客ID不变（guest_xxxxx）

## 📝 总结

✅ 游客ID自动创建和管理
✅ 游客/登录模式自动切换
✅ 游客ID持久化保存
⏸️ 游客访问受保护API的处理（待定）

**建议：先测试游客ID创建，然后决定游客是否需要访问API。**

