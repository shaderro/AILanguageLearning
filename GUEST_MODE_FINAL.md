# 游客模式最终实现

## ✅ 实现方案

### 游客数据存储
- 游客数据存储在 **localStorage**（JSON 格式）
- 每个游客ID独立存储：
  - `guest_data_guest_xxxxx_vocab` - 词汇
  - `guest_data_guest_xxxxx_grammar` - 语法规则

### 数据隔离
```
游客 A (guest_abc123)
  ├─ vocab: [apple, hello]
  └─ grammar: [现在进行时]

游客 B (guest_xyz789)
  ├─ vocab: [world, goodbye]
  └─ grammar: [被动语态]

User 1 (正式用户)
  ├─ vocab: 44条（数据库）
  └─ grammar: 10条（数据库）
```

## 🔄 用户流程

### 场景1：首次访问（游客模式）
```
打开应用
  ↓
自动创建游客ID: guest_abc123
  ↓
可以正常使用所有功能
  ↓
创建的数据保存到 localStorage
```

### 场景2：游客登录（数据迁移）
```
游客模式（有5条词汇）
  ↓
点击"登录" → User 1
  ↓
登录成功
  ↓
检测到游客数据
  ↓
弹出迁移对话框：
┌──────────────────────┐
│ 发现本地数据         │
│ 词汇: 5条            │
│ 语法: 3条            │
│                      │
│ [迁移到新账号]       │
│ [跳过]               │
└──────────────────────┘
  ↓
用户选择"迁移"
  ↓
调用API创建数据到 User 1
  ↓
清空游客本地数据
  ↓
✅ 数据迁移完成
```

### 场景3：跳过迁移
```
游客登录 → User 1
  ↓
弹出迁移对话框
  ↓
用户选择"跳过"
  ↓
游客数据保留在本地
  ↓
下次切换回游客时仍可访问
```

## 📁 文件结构

### 新增文件
```
frontend/my-web-ui/src/
├── contexts/
│   └── UserContext.jsx ✅ 全局用户状态
├── utils/
│   └── guestDataManager.js ✅ 游客数据管理
└── components/
    └── DataMigrationModal.jsx ✅ 数据迁移对话框
```

### 修改文件
```
- hooks/useApi.js ✅ 支持游客数据
- modules/word-demo/WordDemo.jsx ✅ 使用 UserContext
- modules/grammar-demo/GrammarDemo.jsx ✅ 使用 UserContext
- modules/auth/components/LoginModal.jsx ✅ 使用 UserContext
- modules/auth/components/RegisterModal.jsx ✅ 使用 UserContext
- App.jsx ✅ 添加迁移对话框
```

## 🎯 关键代码

### 游客数据保存
```javascript
// 游客创建词汇
guestDataManager.saveVocab('guest_abc123', {
  vocab_body: 'hello',
  explanation: '你好',
  is_starred: false
})

// 保存到 localStorage
// Key: guest_data_guest_abc123_vocab
// Value: [{vocab_id: 123, vocab_body: 'hello', ...}]
```

### 数据迁移
```javascript
// 登录成功后
const guestData = guestDataManager.getAllGuestData('guest_abc123')

// 迁移词汇
for (const vocab of guestData.vocabs) {
  await apiService.createVocab(vocab) // 调用API创建到新用户
}

// 清空游客数据
guestDataManager.clearGuestData('guest_abc123')
```

## 🧪 测试步骤

### 1. 游客模式测试
1. 清空 localStorage
   ```javascript
   localStorage.clear()
   location.reload()
   ```
2. ✅ 自动创建游客ID
3. ✅ Word Demo 和 Grammar Demo 正常显示（空列表）

### 2. 游客创建数据（需要额外实现）
⚠️ **注意：** 目前还没有实现游客的"创建词汇"功能
- 需要添加本地创建逻辑
- 或者暂时手动添加测试数据

手动添加测试数据：
```javascript
// 在控制台执行
import('../utils/guestDataManager.js').then(m => {
  const guestId = localStorage.getItem('guest_user_id')
  m.default.saveVocab(guestId, {
    vocab_body: 'hello',
    explanation: '你好',
    is_starred: false
  })
  m.default.saveGrammar(guestId, {
    rule_name: '现在进行时',
    rule_summary: 'be + doing',
    is_starred: false
  })
  console.log('✅ 测试数据已添加')
  location.reload()
})
```

### 3. 测试数据迁移
1. 游客模式下有数据
2. 点击"登录" → User 1
3. ✅ 弹出迁移对话框
4. ✅ 显示：词汇 X 条，语法 Y 条
5. 点击"迁移"
6. ✅ 数据创建到 User 1 下
7. ✅ 游客本地数据被清空

### 4. 测试跳过迁移
1. 游客有数据
2. 登录 → 选择"跳过"
3. ✅ 数据保留在本地
4. 退出 → 切换回游客
5. ✅ 数据still在

## ⚠️ 待实现

### 游客创建数据功能
目前游客可以查看数据（localStorage），但还需要实现：

1. **创建词汇** - WordDemo 中添加创建按钮
2. **创建语法** - GrammarDemo 中添加创建按钮
3. **本地保存逻辑** - 调用 guestDataManager

### 可选：游客创建示例
```javascript
// 在 WordDemo 中添加
const handleCreateVocab = (vocabData) => {
  if (isGuest) {
    // 游客模式：保存到本地
    guestDataManager.saveVocab(userId, vocabData)
    // 刷新列表
    queryClient.invalidateQueries(queryKeys.vocab.all(userId))
  } else {
    // 登录用户：调用API
    apiService.createVocab(vocabData)
  }
}
```

## 📋 总结

✅ UserContext 完成
✅ 游客ID自动创建
✅ 游客数据管理器
✅ 数据迁移对话框
✅ 登录/注册集成迁移逻辑
⏸️ 游客创建数据UI（可选，后续添加）

**现在可以测试游客模式和数据迁移流程！**

