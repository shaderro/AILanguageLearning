# 游客模式测试指南

## ✅ 已完成功能

1. **游客ID自动创建** - ✅
2. **游客数据存储（localStorage）** - ✅  
3. **登录用户数据（数据库）** - ✅
4. **无刷新切换用户** - ✅
5. **数据迁移对话框** - ✅

## 🧪 完整测试流程

### 步骤 1: 启动应用（游客模式）

```powershell
# 确保前端已启动
cd frontend/my-web-ui
npm run dev
```

在浏览器控制台执行：
```javascript
// 清空所有数据
localStorage.clear()
location.reload()
```

刷新后，控制台应该看到：
```
👤 [UserContext] 创建游客ID: guest_abc12345
```

### 步骤 2: 为游客添加测试数据

在控制台执行：
```javascript
// 手动添加游客测试数据
const guestId = localStorage.getItem('guest_user_id')

// 添加词汇
const vocab1 = {
  vocab_body: 'guest_word_1',
  explanation: '游客创建的词汇1',
  is_starred: false
}
const vocab2 = {
  vocab_body: 'guest_word_2',
  explanation: '游客创建的词汇2',
  is_starred: true
}

// 保存到 localStorage
const key = `guest_data_${guestId}_vocab`
localStorage.setItem(key, JSON.stringify([vocab1, vocab2]))

console.log('✅ 游客数据已添加')
location.reload()
```

### 步骤 3: 验证游客数据显示

刷新后：
1. 访问 Word Demo 页面
2. ✅ 应该看到 **2条词汇**
   - `guest_word_1`
   - `guest_word_2`
3. 控制台应该显示：
   ```
   👤 [useVocabList] 游客模式，加载本地数据: 2 条
   ```

### 步骤 4: 测试登录和数据迁移

1. 点击右上角"登录"
2. 输入：
   - User ID: `1`
   - 密码: `test123456`
3. 登录成功

**预期：自动弹出数据迁移对话框**

```
┌────────────────────────────┐
│ 发现本地数据               │
│ 词汇: 2条                  │
│ 语法: 0条                  │
│                            │
│ [迁移数据到新账号]         │
│ [跳过（稍后再迁移）]       │
└────────────────────────────┘
```

### 步骤 5: 测试迁移功能

点击"迁移数据到新账号"：

控制台应该显示：
```
🔄 [Migration] 开始迁移游客数据...
✅ [Migration] 词汇已迁移: guest_word_1
✅ [Migration] 词汇已迁移: guest_word_2
✅ [Migration] 迁移完成，共 2 条数据
🗑️ [GuestData] 已清空游客数据: guest_abc123
```

刷新页面，查看 Word Demo：
- ✅ 应该看到 **46条词汇**（44 + 2）
- ✅ 包含迁移过来的 `guest_word_1` 和 `guest_word_2`

### 步骤 6: 测试跳过迁移

1. 退出登录（切换回游客）
2. 再次添加游客数据
3. 登录 User 2
4. 弹出迁移对话框
5. 点击"跳过"
6. ✅ 游客数据保留
7. ✅ User 2 看不到游客数据（正常）
8. 退出 → 切换回游客
9. ✅ 游客数据still在

## 📊 数据流向

```
游客模式
├─ 创建数据 → localStorage
├─ 查看数据 ← localStorage
└─ 登录/注册
     ↓
   迁移对话框
     ├─ 选择迁移
     │  ├─ 读取 localStorage
     │  ├─ 调用 API 创建到数据库
     │  └─ 清空 localStorage
     │
     └─ 选择跳过
        └─ 保留 localStorage 数据

登录用户
├─ 创建数据 → 数据库（带 user_id）
├─ 查看数据 ← 数据库（过滤 user_id）
└─ 退出
     ↓
   游客模式（恢复游客ID）
```

## ✨ 核心优势

1. **游客友好** - 无需登录即可使用
2. **数据持久** - 游客数据保存在本地
3. **平滑迁移** - 一键迁移到正式账号
4. **灵活选择** - 可以跳过迁移
5. **无感切换** - 不刷新页面
6. **完全隔离** - 游客数据互不干扰

## 🎯 现在可以测试了！

重启前端后，按照上面的步骤测试游客模式和数据迁移功能。

**关键测试点：**
- ✅ 游客ID自动创建
- ✅ 游客数据本地存储
- ✅ 登录后弹出迁移对话框
- ✅ 迁移数据到新账号
- ✅ 跳过迁移保留本地数据
- ✅ 无刷新用户切换

**开始测试吧！** 🚀

