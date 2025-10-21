# Token ID 使用分析报告

## 📊 Token ID 类型定义

### Token 数据结构（`data_classes_new.py`）

```python
@dataclass(frozen=True)
class Token:
    token_body: str
    token_type: Literal["text", "punctuation", "space"]
    global_token_id: Optional[int] = None      # 全文级别 ID（从0开始）
    sentence_token_id: Optional[int] = None    # 句子内 ID（从1开始）
    ...
```

### 示例数据（`hp1_processed_20250916_123831.json`）

```json
{
  "token_body": "Mr",
  "token_type": "text",
  "global_token_id": 0,      // ← 全文第1个token
  "sentence_token_id": 1     // ← 句子内第1个token
}
```

---

## 🎯 各功能使用的 Token ID

### 1️⃣ **Asked Tokens（已提问标记）** - 使用 `sentence_token_id` ✅

#### 数据结构：
```python
@dataclass
class AskedToken:
    user_id: str
    text_id: int
    sentence_id: int
    sentence_token_id: Optional[int]  # ← 使用句内ID
    type: Literal["token", "sentence"] = "token"
```

#### 存储键格式：
```
{text_id}:{sentence_id}:{sentence_token_id}
例: "1:3:5"  // 文章1，句子3，句内第5个token
```

#### 前端使用：
```javascript
// ChatView.jsx 第224行
const sentenceTokenId = token.sentence_token_id
markAsAsked(textId, sentenceId, sentenceTokenId)

// TokenSpan.jsx 第44-47行
const tokenSentenceTokenId = token?.sentence_token_id
isTokenAsked(articleId, tokenSentenceId, tokenSentenceTokenId)
```

#### 后端 API：
```python
# server_frontend_mock.py 第917-945行
@app.post('/api/user/asked-tokens')
async def mark_token_asked(payload: dict):
    sentence_token_id = payload.get('sentence_token_id')  # ← 句内ID
    manager.mark_token_asked(user_id, text_id, sentence_id, sentence_token_id)
```

**✅ 优点**：
- 稳定：句子内 token 顺序相对固定
- 简单：每个句子独立编号，易于理解
- 适合用户交互：用户看到的是"句子内第几个词"

---

### 2️⃣ **Vocab Example（词汇例句）** - 使用 `token_indices` （未指定类型）⚠️

#### 数据结构：
```python
@dataclass
class VocabExpressionExample:
    vocab_id: int
    text_id: int
    sentence_id: int
    context_explanation: str
    token_indices: list[int] = field(default_factory=list)  # ⚠️ 未明确说明
```

#### 当前实际数据（`vocab.json`）：
```json
{
  "vocab_id": 1,
  "examples": [{
    "text_id": 1,
    "sentence_id": 1,
    "token_indices": []  // ← 当前都为空
  }]
}
```

#### 后端添加例句：
```python
# vocab_manager.py 第67-73行
new_example = NewVocabExpressionExample(
    vocab_id=vocab_id,
    text_id=text_id,
    sentence_id=sentence_id,
    context_explanation=context_explanation,
    token_indices=[]  # ← 硬编码为空数组，未设置实际值
)
```

**⚠️ 问题**：
- `token_indices` 始终为空，未实际使用
- 未明确是 `global_token_id` 还是 `sentence_token_id`

---

### 3️⃣ **Token Selection（前端选择）** - 混合使用 ⚠️

#### 前端代码（`useTokenSelection.js`）：

```javascript
// 使用 global_token_id 作为唯一标识
const tokenId = token.global_token_id

// 但传给后端时使用 sentence_token_id
updatePayload.token = {
  token_body: token.token_body,
  sentence_token_id: token.sentence_token_id,  // ← 句内ID
  global_token_id: token.global_token_id       // ← 全文ID
}
```

#### 后端 SelectedToken：
```python
# selected_token.py (简化版本)
# 使用词位置索引（基于 split() 分词）
token_indices = []  # 相对位置，不是 token_id
```

**⚠️ 问题**：
- 前端用 `global_token_id` 做选择状态管理
- 传给后端时带了两个 ID，但后端只用了 `sentence_token_id`
- SelectedToken 的 `token_indices` 是分词位置，不是 token_id

---

## 📋 推荐使用规范

### ✅ **推荐：统一使用 `sentence_token_id`**

#### 理由：
1. **稳定性**：句子内编号不受文章修改影响
2. **已有基础**：Asked Tokens 已全面使用
3. **语义清晰**：`text_id + sentence_id + sentence_token_id` 组合唯一定位
4. **简化逻辑**：避免维护两套ID体系

#### 建议修改：

**1. Vocab Example 的 token_indices**
```python
# 修改前
token_indices=[]  # 空数组

# 修改后（建议）
token_indices=[sentence_token_id]  # 使用句内ID
# 或者对于多词表达
token_indices=[3, 4, 5]  # 句内第3、4、5个token
```

**2. 前端选择状态管理**
```javascript
// 修改前
const tokenId = token.global_token_id  // 全文ID

// 修改后（建议，可选）
const tokenId = `${sentenceIdx}:${token.sentence_token_id}`  // 复合键
// 优点：避免跨句子ID冲突
```

---

## 🔄 Global Token ID 的价值

虽然推荐主要使用 `sentence_token_id`，但 `global_token_id` 也有用途：

### 适用场景：
1. **全文统计**：统计整篇文章的词频、难度分布
2. **跨句子引用**：如果需要标记"文章第X个词"
3. **文章级别标注**：全文范围的语法结构分析

### 不适合：
- ❌ 用户交互（用户不关心"全文第几个词"）
- ❌ 句子级别操作（句子改变会影响后续所有 token）

---

## ✅ 使用状况总结（优化后）

| 功能 | 使用的 ID | 状态 | 说明 |
|------|----------|------|------|
| **Asked Tokens** | `sentence_token_id` | ✅ 正确 | 保持不变 |
| **前端选择（唯一键）** | `sentence_token_id` | ✅ **已优化** | 只使用句内ID |
| **前端传参** | `sentence_token_id` | ✅ **已优化** | 移除 global_token_id |
| **后端 SelectedToken** | 词位置索引 | ⚠️ 遗留 | 功能正常，未来可优化 |
| **Vocab Example** | `token_indices` | ✅ **已修复** | 存储实际 sentence_token_id |
| **Grammar Example** | 无 token_indices | ✅ 合理 | 语法是句子级别，不需要 |

---

## ✅ 已完成的优化

### 修复1：Vocab Example 的 token_indices ✅

**修改文件**：
- `backend/data_managers/vocab_manager.py` 第54行
- `backend/data_managers/data_controller.py` 第187-198行  
- `backend/assistants/main_assistant.py` 第426-434行、第547-555行

**改进内容**：
```python
# 修复前
new_example = NewVocabExpressionExample(
    token_indices=[]  # ❌ 硬编码空数组
)

# 修复后
new_example = NewVocabExpressionExample(
    token_indices=token_indices  # ✅ 使用实际值
)
```

**新增辅助方法**：
```python
# main_assistant.py 第565-613行
def _get_token_indices_from_selection(self, sentence):
    """从 session_state 提取 sentence_token_id 列表"""
    # 1. 获取选中的文本
    # 2. 在句子的 tokens 中查找匹配
    # 3. 返回 sentence_token_id 列表
```

**效果**：
- ✅ `token_indices` 现在存储实际的 `sentence_token_id`
- ✅ 数据完整，可用于未来高亮显示
- ✅ 示例：`"token_indices": [3, 4, 5]` 表示句内第3、4、5个token

---

### 修复2：前端统一使用 sentence_token_id ✅

**修改文件**：
- `frontend/my-web-ui/src/modules/article/utils/tokenUtils.js` 第24-32行
- `frontend/my-web-ui/src/modules/article/components/ChatView.jsx` 第184行、第499行

**改进内容**：
```javascript
// 修复前
export const getTokenId = (token) => {
  const gid = token?.global_token_id
  const sid = token?.sentence_token_id
  return `${gid}-${sid}`  // ❌ 使用全文ID
}

// 修复后
export const getTokenId = (token) => {
  const sid = token?.sentence_token_id
  return sid  // ✅ 只使用句内ID
}
```

```javascript
// 前端传参优化
updatePayload.token = {
  token_body: token.token_body,
  sentence_token_id: token.sentence_token_id
  // ✅ 移除了 global_token_id
}
```

**效果**：
- ✅ 前后端统一使用 `sentence_token_id`
- ✅ 减少数据传输（移除冗余字段）
- ✅ 代码更简洁
- ✅ 与 Asked Tokens 功能保持一致

---

## 🔧 遗留优化（可选，低优先级）

### SelectedToken 的 token_indices 优化 🟢
- **当前状态**：使用词位置索引（基于 `split()`）
- **建议**：改为直接使用 `sentence_token_id`
- **影响**：功能正常，优先级低

---

## 💡 总结

**✅ 系统现已完全统一使用 `sentence_token_id`（句内ID）！**

### 已完成的优化：
- ✅ **Vocab Example** - 现在存储实际的 `sentence_token_id`
- ✅ **前端选择** - 只使用 `sentence_token_id` 作为唯一键
- ✅ **前端传参** - 移除冗余的 `global_token_id`
- ✅ **Asked Tokens** - 已经在使用 `sentence_token_id`
- ✅ **前后端一致** - 统一的标识体系

### Global Token ID 的保留：
- 📊 **保留在数据中**，用于全文统计和分析
- 🎯 **不用于用户交互**，避免复杂性
- 📈 **未来扩展**：全文词频分析、难度分布等

### 系统优势：
- ✅ **稳定性**：句子修改不影响句内编号
- ✅ **简洁性**：`text_id + sentence_id + sentence_token_id` 三元组唯一定位
- ✅ **一致性**：前后端使用相同的标识体系
- ✅ **可扩展**：token_indices 支持多词表达（如 [3, 4, 5]）

