# Article 页面 Grammar & Vocab Notation 架构总结

## 📋 目录
1. [组件层级结构](#组件层级结构)
2. [数据流](#数据流)
3. [核心模块](#核心模块)
4. [下划线实现逻辑](#下划线实现逻辑)
5. [Span卡片实现逻辑](#span卡片实现逻辑)
6. [问题分析](#问题分析)
7. [重构建议](#重构建议)

---

## 组件层级结构

```
ArticleChatView (顶层容器)
├── NotationContext.Provider (✅ 已实现 - 提供统一的notation访问)
│   └── value: {
│       ├── Grammar: getGrammarNotationsForSentence, getGrammarRuleById, hasGrammarNotation
│       ├── Vocab: getVocabNotationsForSentence, getVocabExampleForToken, hasVocabNotation
│       └── 兼容层: isTokenAsked, getNotationContent, setNotationContent
│   }
├── useNotationCache (统一缓存管理器)
│   ├── grammarNotations (预加载)
│   ├── grammarRulesCache (预加载)
│   ├── vocabNotations (预加载)
│   └── vocabExamplesCache (预加载)
├── useAskedTokens (兼容层 - 向后兼容)
└── ArticleViewer
    └── SentenceContainer (句子容器)
        ├── [使用 useContext(NotationContext)] ✅
        ├── TokenSpan (token组件)
        │   ├── [使用 useContext(NotationContext)] ✅
        │   ├── 下划线样式 (inline style)
        │   └── notation/VocabNotationCard (vocab span卡片)
        └── notation/GrammarNotationCard (grammar span卡片 - 句子级)
```

---

## 数据流

### 1. 初始化阶段（页面加载时）

```
ArticleChatView 挂载
  ↓
useNotationCache(articleId) 初始化
  ↓
loadAllNotations(articleId)
  ├── 并行加载 grammar notations + vocab notations
  ├── 预加载所有 grammar rules
  └── 预加载所有 vocab examples
  ↓
数据存入缓存 (useState)
```

### 2. 渲染阶段（显示下划线）

```
ArticleViewer 渲染
  ↓
SentenceContainer 渲染每个句子
  ├── [通过 useContext(NotationContext) 获取 hasGrammarNotation] ✅
  ├── 检查是否有 grammar notation
  └── 渲染 TokenSpan
       ├── [通过 useContext(NotationContext) 获取 notation 功能] ✅
       ├── 检查是否有 grammar notation (isInGrammarNotation)
       ├── 检查是否有 vocab notation (hasVocabNotationForToken)
       └── 应用下划线样式
            ├── 绿色 (vocab)
            └── 灰色 (grammar)
```

### 3. 交互阶段（显示span卡片）

**Vocab Notation (Token级):**
```
用户 hover TokenSpan
  ↓
hasVocabVisual === true
  ↓
setShowNotation(true)
  ↓
渲染 TokenNotation
  ↓
调用 getVocabExampleForToken(textId, sentenceId, tokenIndex)
  ├── 首先检查 vocabExamplesCache
  └── 缓存命中 → 直接返回
```

**Grammar Notation (Sentence级):**
```
用户 hover SentenceContainer
  ↓
hasGrammar === true
  ↓
setShowGrammarCard(true)
  ↓
渲染 GrammarNotationCard
  ↓
使用 cachedGrammarRules + getGrammarRuleById
  └── 缓存命中 → 直接使用
```

---

## 核心模块

### 1. **useNotationCache** (`hooks/useNotationCache.js`)
**职责**: 统一的缓存管理器，负责预加载和提供访问接口

**主要功能**:
- ✅ 预加载 grammar notations 和 grammar rules
- ✅ 预加载 vocab notations 和 vocab examples
- ✅ 提供查询函数 (getGrammarNotationsForSentence, getVocabNotationsForSentence)
- ✅ 实时缓存更新 (addGrammarNotationToCache, addVocabNotationToCache)
- ✅ 创建新notation (createVocabNotation)

**缓存结构**:
```javascript
grammarNotations: Array<GrammarNotation>
grammarRulesCache: Map<grammarId, GrammarRule>
vocabNotations: Array<VocabNotation>
vocabExamplesCache: Map<"textId:sentenceId:tokenId", VocabExample>
```

### 2. **TokenSpan** (`components/TokenSpan.jsx`)
**职责**: 渲染单个token，处理下划线和vocab span卡片

**主要功能**:
- 计算下划线样式 (hasVocabVisual, isInGrammarNotation)
- 管理 TokenNotation 的显示状态
- 处理 hover 事件

**关键逻辑**:
```javascript
// 下划线优先级: vocab绿色 > grammar灰色
hasVocabVisual ? 'border-b-2 border-green-500' 
  : (isInGrammarNotation ? 'border-b-2 border-gray-400' : '')
```

### 3. **SentenceContainer** (`components/SentenceContainer.jsx`)
**职责**: 句子级容器，处理grammar span卡片

**主要功能**:
- 检查句子是否有 grammar notation
- 管理 GrammarNotationCard 的显示状态
- 处理句子 hover 事件

### 4. **GrammarNotationCard** (`components/GrammarNotationCard.jsx`)
**职责**: 显示语法规则详情的span卡片

**主要功能**:
- 优先使用缓存数据 (cachedGrammarRules, getGrammarRuleById)
- 从 grammar rule 的 examples 中匹配当前句子
- Fallback到API（缓存未命中时）

### 5. **TokenNotation** (`components/TokenNotation.jsx`)
**职责**: 显示词汇解释的span卡片

**主要功能**:
- 优先使用缓存数据 (getVocabExampleForToken)
- Fallback到API（缓存未命中时）
- 显示 context_explanation

### 6. **useAskedTokens** (`hooks/useAskedTokens.js`)
**职责**: 向后兼容层，用于标记"已提问"的token

**状态**: 逐渐被 `vocabNotations` 取代，但仍在 `TokenSpan` 中作为备用检查

---

## 下划线实现逻辑

### Grammar Notation 下划线 (灰色)

**位置**: `TokenSpan.jsx` 第66-72行

**逻辑**:
```javascript
// 1. 获取句子的grammar notations
const grammarNotations = getGrammarNotationsForSentence(sentenceId)

// 2. 检查token是否在marked_token_ids中
const isInGrammarNotation = grammarNotations.some(notation => {
  if (!notation.marked_token_ids || notation.marked_token_ids.length === 0) {
    return true  // 整句都有grammar notation
  }
  return notation.marked_token_ids.includes(tokenSentenceTokenId)
})

// 3. 应用样式
isInGrammarNotation ? 'border-b-2 border-gray-400' : ''
```

### Vocab Notation 下划线 (绿色)

**位置**: `TokenSpan.jsx` 第74-98行

**逻辑**:
```javascript
// 1. 获取句子的vocab notations (使用useMemo优化)
const vocabNotationsForSentence = useMemo(() => {
  return getVocabNotationsForSentence(sentenceId)
}, [getVocabNotationsForSentence, sentenceId])

// 2. 检查token是否有vocab notation (使用useMemo优化)
const hasVocabNotationForToken = useMemo(() => {
  return vocabNotationsForSentence.some(n => 
    Number(n?.token_id ?? n?.token_index) === Number(tokenSentenceTokenId)
  )
}, [vocabNotationsForSentence, tokenSentenceTokenId])

// 3. 优先级: vocab notation > asked tokens (兼容层)
const hasVocabVisual = hasVocabNotationForToken || (isAsked && !hasVocabNotationForToken)

// 4. 应用样式
hasVocabVisual ? 'border-b-2 border-green-500' : ''
```

---

## Span卡片实现逻辑

### Grammar Notation Card (句子级)

**触发**: 用户hover整个句子 (`SentenceContainer`)

**数据源**: `useNotationCache` 提供的缓存

**流程**:
```
SentenceContainer handleSentenceMouseEnter
  ↓
hasGrammar && grammarNotations.length > 0
  ↓
setShowGrammarCard(true)
  ↓
GrammarNotationCard 渲染
  ↓
优先使用缓存:
  cachedGrammarRules + getGrammarRuleById
  ↓
从 grammar rule.examples 中匹配当前句子
  ↓
显示 context_explanation
```

**位置**: `SentenceContainer.jsx` 第160-173行

### Vocab Notation Card (Token级)

**触发**: 用户hover有vocab notation的token (`TokenSpan`)

**数据源**: `useNotationCache` 提供的缓存

**流程**:
```
TokenSpan onMouseEnter
  ↓
hasVocabVisual === true
  ↓
setShowNotation(true)
  ↓
TokenNotation 渲染
  ↓
调用 getVocabExampleForToken(textId, sentenceId, tokenIndex)
  ├── 首先检查 vocabExamplesCache
  └── 缓存命中 → 直接返回
  ↓
显示 context_explanation
```

**位置**: `TokenSpan.jsx` 第218-229行

---

## 问题分析

### ✅ 优点

1. **缓存机制完善**: 所有数据在页面加载时预加载，hover时无需API调用
2. **性能优化**: 使用 `useMemo` 缓存计算结果，避免重复计算
3. **职责分离清晰**: 
   - `useNotationCache` 负责数据管理
   - `TokenSpan` 负责token级显示
   - `SentenceContainer` 负责句子级显示
4. **向后兼容**: 保留了 `useAskedTokens` 作为备用检查

### ⚠️ 存在的问题

#### 1. **重复的兼容层检查**
**位置**: `TokenSpan.jsx` 第53-55行, 第98行

```javascript
// 问题: 同时检查 isAsked 和 hasVocabNotationForToken
const isAsked = isTextToken && tokenSentenceTokenId != null
  ? isTokenAsked(articleId, tokenSentenceId, tokenSentenceTokenId)
  : false

const hasVocabVisual = hasVocabNotationForToken || (isAsked && !hasVocabNotationForToken)
```

**分析**: 
- `isAsked` 来自旧的 `useAskedTokens` hook
- `hasVocabNotationForToken` 来自新的 `vocabNotations`
- 两者功能重叠，增加了复杂度

#### 2. **Prop Drilling 过多** ✅ **已解决**
**位置**: ~~`ArticleChatView` → `ArticleViewer` → `SentenceContainer` → `TokenSpan`~~ 

**解决方案**: 已通过 `NotationContext` 解决

**重构前的问题**: 
- ~~8个与notation相关的props需要层层传递~~
- ~~容易出现遗漏或错误传递~~
- ~~难以维护~~

**重构后**:
- ✅ 所有 notation 相关功能通过 `NotationContext` 提供
- ✅ `ArticleViewer` 不再需要接收和转发 notation props（减少5个props）
- ✅ `SentenceContainer` 和 `TokenSpan` 通过 `useContext` 直接获取
- ✅ 代码更简洁，维护更容易

**仍保留的props（向后兼容）**:
- `isTokenAsked`, `getNotationContent`, `setNotationContent` - 保留在 ArticleChatView → ArticleViewer → SentenceContainer → TokenSpan 中作为备用，但优先级低于 Context

#### 3. **下划线逻辑分散**
**位置**: `TokenSpan.jsx` 中混在一起

**问题**:
- grammar 和 vocab 的下划线计算逻辑混在一起
- 优先级判断分散在多个地方

#### 4. **缓存访问方式不统一** ✅ **部分解决**
**问题**:
- ~~`TokenSpan` 直接从 `getVocabNotationsForSentence` 获取数据~~
- `GrammarNotationCard` 通过 `cachedGrammarRules` prop 接收

**解决方案**: 
- ✅ `TokenSpan` 和 `SentenceContainer` 现在都通过 `NotationContext` 访问
- ⚠️ `GrammarNotationCard` 仍通过 props 接收 `cachedGrammarRules` 和 `getGrammarRuleById`（因为它是从 `SentenceContainer` 传递的，可以考虑后续也改为使用 Context）

#### 5. **未使用的组件**
**位置**: `components/GrammarNotation.jsx`

**问题**: 
- 这个组件定义了但从未被使用
- `GrammarNotationCard` 直接在 `SentenceContainer` 中渲染

#### 6. **类型不一致**
**问题**: 
- `sentence_id` 有时是 0-based index (sentenceIdx)
- 有时是 1-based ID (sentenceId = sentenceIdx + 1)
- 容易出现类型转换错误

---

## 重构建议

### 方案A: 创建 Notation Context ✅ **已完成**

**目标**: 减少 prop drilling，统一缓存访问

**实施日期**: 已实现

**实现步骤**:

1. ✅ **创建 `NotationContext`** - `contexts/NotationContext.jsx`
```javascript
export const NotationContext = createContext(null)
```

2. ✅ **在 `ArticleChatView` 中提供 Context**
```javascript
const notationContextValue = {
  // Grammar 相关
  getGrammarNotationsForSentence,
  getGrammarRuleById,
  hasGrammarNotation,
  
  // Vocab 相关
  getVocabNotationsForSentence,
  getVocabExampleForToken,
  hasVocabNotation,
  
  // 兼容层（暂时保留用于向后兼容）
  isTokenAsked,
  getNotationContent,
  setNotationContent
}

<NotationContext.Provider value={notationContextValue}>
  <ArticleViewer ... />
</NotationContext.Provider>
```

3. ✅ **在子组件中使用 Context**
```javascript
// SentenceContainer.jsx
const { hasGrammarNotation, getGrammarNotationsForSentence, getGrammarRuleById } = 
  useContext(NotationContext)

// TokenSpan.jsx
const { 
  getVocabNotationsForSentence,
  getVocabExampleForToken,
  getGrammarNotationsForSentence 
} = useContext(NotationContext)
```

**结果**:
- ✅ 消除了 5 个 props 在 ArticleViewer 中的传递
- ✅ 消除了 3 个 props 在 SentenceContainer 中的传递
- ✅ 消除了 5 个 props 在 TokenSpan 中的传递
- ✅ 统一了缓存访问方式
- ✅ 代码更简洁，易于扩展和维护
- ✅ 保留了向后兼容性

**详细重构总结**: 参见 `CONTEXT_REFACTOR_SUMMARY.md`

### 方案B: 创建统一的 Notation Hook

**目标**: 封装所有notation相关逻辑

**步骤**:

1. **创建 `useNotationForToken` hook**
```javascript
// hooks/useNotationForToken.js
export function useNotationForToken(articleId, sentenceId, tokenId) {
  const { 
    getVocabNotationsForSentence,
    getGrammarNotationsForSentence 
  } = useNotationCache(articleId)
  
  // 统一计算逻辑
  const vocabNotation = useMemo(() => {
    const notations = getVocabNotationsForSentence(sentenceId)
    return notations.find(n => n.token_id === tokenId)
  }, [sentenceId, tokenId])
  
  const grammarNotation = useMemo(() => {
    const notations = getGrammarNotationsForSentence(sentenceId)
    return notations.find(n => 
      !n.marked_token_ids || 
      n.marked_token_ids.length === 0 || 
      n.marked_token_ids.includes(tokenId)
    )
  }, [sentenceId, tokenId])
  
  // 返回统一的下划线样式
  const underlineStyle = useMemo(() => {
    if (vocabNotation) return 'vocab' // 绿色
    if (grammarNotation) return 'grammar' // 灰色
    return null
  }, [vocabNotation, grammarNotation])
  
  return { vocabNotation, grammarNotation, underlineStyle }
}
```

2. **在 `TokenSpan` 中使用**
```javascript
const { vocabNotation, grammarNotation, underlineStyle } = 
  useNotationForToken(articleId, sentenceId, tokenSentenceTokenId)
```

**优点**:
- ✅ 逻辑封装更清晰
- ✅ 减少 `TokenSpan` 的复杂度
- ✅ 便于测试

### 方案C: 移除旧的兼容层（渐进式）

**目标**: 完全迁移到新API，移除 `useAskedTokens`

**步骤**:

1. **确认所有数据已迁移到 `vocabNotations`**
2. **移除 `TokenSpan` 中的 `isAsked` 检查**
3. **移除 `useAskedTokens` 相关代码**
4. **清理未使用的 props**

**优点**:
- ✅ 减少代码复杂度
- ✅ 单一数据源
- ✅ 更好的维护性

### 方案D: 统一类型处理

**目标**: 统一使用 1-based ID

**步骤**:

1. **在 `useNotationCache` 中统一转换为 1-based ID**
2. **在所有组件中使用 1-based ID**
3. **添加类型转换工具函数**

---

## 推荐的渐进式重构计划

### Phase 1: 创建 NotationContext ✅ **已完成**
- **时间**: 已完成
- **影响**: 减少 prop drilling，提升代码可维护性
- **风险**: 低
- **状态**: ✅ 已实施并通过测试
- **文件**: 
  - ✅ `contexts/NotationContext.jsx` (新建)
  - ✅ `ArticleChatView.jsx` (更新)
  - ✅ `ArticleViewer.jsx` (更新)
  - ✅ `SentenceContainer.jsx` (更新)
  - ✅ `TokenSpan.jsx` (更新)
- **结果**: 成功消除了 13 个 props 的传递，代码更简洁

### Phase 2: 创建统一的 useNotationForToken Hook (中优先级)
- **时间**: 2-3小时
- **影响**: 简化 `TokenSpan` 逻辑，封装计算
- **风险**: 中
- **状态**: ⏳ 待实施

### Phase 3: 移除旧的兼容层 (低优先级)
- **时间**: 1-2小时
- **影响**: 完全迁移到新API
- **风险**: 低（需要确认数据完整性）
- **状态**: ⏳ 待实施
- **前置条件**: 确认所有数据已迁移到 `vocabNotations`

### Phase 4: 清理未使用的组件 (低优先级)
- **时间**: 30分钟
- **影响**: 删除 `GrammarNotation.jsx` 等未使用组件
- **风险**: 低
- **状态**: ⏳ 待实施

### Phase 5: 统一 GrammarNotationCard 使用 Context (可选)
- **时间**: 1小时
- **影响**: 让 `GrammarNotationCard` 也通过 Context 访问，而不是通过 props
- **风险**: 低
- **状态**: ⏳ 待实施

---

## 总结

### 当前状态
- ✅ **功能完整**: 所有功能都正常工作
- ✅ **性能优化**: 缓存机制完善，使用 `useMemo` 优化
- ✅ **代码组织**: Prop drilling 问题已通过 NotationContext 解决
- ⚠️ **逻辑分散**: 下划线计算逻辑仍可在 TokenSpan 中进一步封装
- ⚠️ **兼容层**: 新旧API并存，增加复杂度（需要评估是否可以移除）

### 已完成的重构
**Phase 1: NotationContext** ✅
- 创建了统一的 Context 来管理所有 notation 相关功能
- 消除了 13 个 props 的层层传递
- 代码更简洁，维护更容易
- 保留了向后兼容性

### 建议
**短期** (已完成): 
- ✅ Phase 1 (NotationContext) - 已完成

**中期** (1-2周): 
- 评估是否需要 Phase 2 (统一Hook)，进一步简化 `TokenSpan` 逻辑
- 考虑 Phase 5 (统一 GrammarNotationCard 使用 Context)

**长期** (1个月+): 
- 评估是否需要 Phase 3 (移除兼容层)，完全迁移到新API
- Phase 4: 清理未使用的组件
- 保持代码整洁，定期清理未使用的代码
- 优化性能瓶颈

### 结论
当前架构**功能完整且性能良好**。通过实施 NotationContext，**代码组织问题已显著改善**。建议继续进行渐进式重构，逐步简化逻辑并移除冗余代码，但核心架构已经良好。

### 重构成果统计
- **减少的 Props**: 13 个
- **减少的代码行数**: 约 14 行
- **新增文件**: 1 个 (NotationContext.jsx)
- **修改文件**: 4 个
- **向后兼容**: ✅ 完全保留

详细的重构总结请参考: `CONTEXT_REFACTOR_SUMMARY.md`

