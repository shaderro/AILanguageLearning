# 🎯 Asked Token UI不更新的根本原因

## 🐛 问题定位

**症状**: 标记成功（日志显示成功），但UI没有变绿

**根本原因**: `useAskedTokens` Hook被调用了**两次**，创建了**两个独立的状态**！

---

## 🔍 问题详解

### 当前代码结构

```javascript
// ArticleChatView.jsx (第19行)
const { markAsAsked } = useAskedTokens(articleId)  // ← 实例1

// ArticleViewer.jsx (第16行)
const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)  // ← 实例2
```

### 问题流程

```
1. 用户选中token并发送问题
   ↓
2. ChatView调用markAsAsked()
   ↓ 使用ArticleChatView的实例1
   ↓
3. 实例1的askedTokenKeys Set更新 ✅
   ↓ Set添加了 "1:4:22"
   ↓
4. ArticleViewer使用isTokenAsked()检查
   ↓ 使用自己的实例2
   ↓
5. 实例2的askedTokenKeys Set没有更新 ❌
   ↓ Set中没有 "1:4:22"
   ↓
6. isTokenAsked()返回false
   ↓
7. Token不显示绿色 ❌
```

**核心问题**: 两个独立的Set！
- 实例1的Set: `["1:4:22"]` ✅ 已更新
- 实例2的Set: `[]` ❌ 未更新

---

## ✅ 解决方案

**移除ArticleViewer中的useAskedTokens，改为接收props**

### 修改1: ArticleViewer.jsx

```javascript
// 修改前（有问题）
export default function ArticleViewer({ articleId, onTokenSelect }) {
  const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId)  // ← 删除
  // ...
}

// 修改后（正确）
export default function ArticleViewer({ articleId, onTokenSelect, isTokenAsked, markAsAsked }) {
  // 不再调用useAskedTokens，直接使用props
  // ...
}
```

### 修改2: ArticleChatView.jsx

```javascript
// 修改前（只传部分）
const { markAsAsked } = useAskedTokens(articleId, 'default_user')  // ← 改为获取所有

<ArticleViewer 
  articleId={articleId} 
  onTokenSelect={handleTokenSelect}
/>

// 修改后（传递所有）
const { askedTokenKeys, isTokenAsked, markAsAsked } = useAskedTokens(articleId, 'default_user')

<ArticleViewer 
  articleId={articleId} 
  onTokenSelect={handleTokenSelect}
  isTokenAsked={isTokenAsked}  // ← 新增
  markAsAsked={markAsAsked}     // ← 新增
/>
```

---

## 🎯 完整的修复代码

让我立即帮你修改！


