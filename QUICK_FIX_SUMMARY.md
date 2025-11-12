# 快速修复总结

## ✅ 已修复

### 1. React Query queryKey 错误
**问题：** queryKey 必须是数组，但某些地方使用了函数而不是调用
**修复：** 
- ✅ useArticles(userId) - 现在正确调用
- ✅ useArticle(id, userId) - 现在正确调用
- ✅ ArticleSelection - 传入 userId
- ✅ ArticleViewer - 传入 userId

### 2. 游客数据显示问题
**可能原因：** 
- localStorage 中没有游客数据
- guestDataManager 读取路径错误

**调试工具：** `debug_guest_data.html`

---

## 🧪 立即测试

### 步骤 1: 重启前端
```powershell
cd frontend/my-web-ui
npm run dev
```

### 步骤 2: 检查控制台错误
刷新页面，控制台应该**不再有 queryKey 错误**

### 步骤 3: 添加游客测试数据
打开 `debug_guest_data.html`：
1. 点击"查看所有数据" - 检查当前状态
2. 点击"添加测试数据" - 添加测试词汇和语法
3. 点击"检查游客数据" - 验证数据格式

或在应用控制台执行：
```javascript
const guestId = localStorage.getItem('guest_user_id')
localStorage.setItem(`guest_data_${guestId}_vocab`, JSON.stringify([
  {vocab_id: 1, vocab_body: 'test', explanation: '测试', is_starred: false}
]))
console.log('✅ 已添加测试数据')
location.reload()
```

### 步骤 4: 验证显示
1. 刷新页面
2. 控制台应该看到：
   ```
   👤 [useVocabList] 游客模式，加载本地数据: 1 条
   ```
3. Word Demo 页面应该显示 1 条词汇

### 步骤 5: 测试迁移
1. 登录 User 1
2. 应该弹出迁移对话框
3. 对话框应该显示：
   - 词汇: 1条
   - 语法: 0条

如果还是没有显示，在控制台执行：
```javascript
// 检查 guestDataManager
const guestId = localStorage.getItem('guest_user_id')
console.log('Guest ID:', guestId)

// 手动导入和测试
import('../utils/guestDataManager.js').then(m => {
  const data = m.default.getAllGuestData(guestId)
  console.log('游客数据:', data)
  console.log('有数据?', m.default.hasGuestData(guestId))
})
```

---

**现在重启前端，用 `debug_guest_data.html` 添加测试数据，然后测试！**

