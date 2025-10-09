# Asked Tokens 标记功能

## 📋 功能概述

在文章阅读页面自动加载并显示已提问的 token，用绿色下划线标记。

## 🎯 功能实现

### 1️⃣ **API 层** (`services/api.js`)

新增两个方法：

```javascript
// 获取文章的已提问 tokens
apiService.getAskedTokens(userId, textId)

// 标记 token 为已提问
apiService.markTokenAsked(userId, textId, sentenceId, sentenceTokenId)
```

**后端接口**：
- `GET /api/user/asked-tokens?user_id=xxx&text_id=xxx`
- `POST /api/user/asked-tokens` 

### 2️⃣ **自定义 Hook** (`hooks/useAskedTokens.js`)

管理 asked tokens 状态：

```javascript
const { 
  askedTokenKeys,    // Set - 已提问token的key集合
  isLoading,         // 加载状态
  error,             // 错误信息
  isTokenAsked,      // 检查函数
  markAsAsked        // 标记函数
} = useAskedTokens(articleId, userId)
```

**特性**：
- ✅ 页面加载时自动获取
- ✅ 使用 Set 结构高效查询
- ✅ 支持动态标记新 token

### 3️⃣ **UI 标记** (`components/TokenSpan.jsx`)

视觉效果：
- **绿色下划线**：`border-b-2 border-green-500`
- **自动检测**：根据 `text_id:sentence_id:sentence_token_id` 判断

## 🔑 数据格式

**Asked Token Key 格式**：
```
{text_id}:{sentence_id}:{sentence_token_id}
```

**示例**：
```
1:3:5  // 文章1，句子3，token 5
```

## 🔄 工作流程

```
1. ArticleViewer 加载
   ↓
2. useAskedTokens 自动调用 API
   ↓
3. 获取 Set<string> 格式的 askedTokenKeys
   ↓
4. TokenSpan 检查每个 token 是否在集合中
   ↓
5. 已提问的 token 显示绿色下划线
```

## 📦 文件变更

```
✅ services/api.js                    - 新增 API 方法
✅ hooks/useAskedTokens.js            - 新建 Hook
✅ components/ArticleViewer.jsx       - 集成 Hook
✅ components/TokenSpan.jsx           - 添加视觉标记
```

## 🚀 使用示例

```jsx
// ArticleViewer 中
const { isTokenAsked } = useAskedTokens(articleId)

// TokenSpan 中
const isAsked = isTokenAsked(articleId, token.sentence_id, token.sentence_token_id)
```

## 🎨 样式效果

- **未提问 token**：普通样式
- **已提问 token**：<span style="border-bottom: 2px solid #22c55e;">绿色下划线</span>
- **选中状态**：黄色背景（保持不变）

## 📝 注意事项

1. **默认用户**：当前使用 `default_user`
2. **数据存储**：后端支持数据库和 JSON 两种模式
3. **性能优化**：使用 Set 结构，O(1) 查询复杂度
4. **容错处理**：API 失败时返回空集合，不影响正常显示

---

**功能完成时间**：2025-10-09  
**状态**：✅ 已完成，无 Linter 错误

