# 建议问题智能显示功能

## 📋 功能说明

根据用户选中的 token 数量，智能展示不同类型的建议问题：
- **单个词汇**：显示针对单词的问题
- **多个词汇（短语）**：显示针对短语的问题
- **整句话**：显示针对句子的问题

## 🎯 实现细节

### 1. SuggestedQuestions 组件

**文件：** `frontend/my-web-ui/src/modules/article/components/SuggestedQuestions.jsx`

#### 三组预设问题：

```javascript
// 单个token的建议问题（tokenCount === 1）
const singleTokenQuestions = [
  "这个词是什么意思？",
  "这个词怎么用？",
  "能给我一个例句吗？",
  "这个词有什么词根词缀吗？"
]

// 多个token（短语）的建议问题（1 < tokenCount < 10）
const multipleTokensQuestions = [
  "这个短语是什么意思？",
  "这个短语怎么使用？",
  "这是固定搭配吗？",
  "能给我一个例句吗？"
]

// 整句话的建议问题（tokenCount >= 10）
const sentenceQuestions = [
  "这句话是什么意思？",
  "这句话的语法结构是什么？",
  "这句话的主谓宾是什么？",
  "能解释一下这句话的用法吗？"
]
```

#### 智能选择逻辑：

```javascript
const getSuggestedQuestions = () => {
  if (tokenCount === 1) {
    return singleTokenQuestions        // 单个词
  } else if (tokenCount > 1 && tokenCount < 10) {
    return multipleTokensQuestions     // 短语
  } else {
    return sentenceQuestions          // 整句话
  }
}
```

### 2. 新增 Props

**SuggestedQuestions 组件：**
```javascript
tokenCount = 1  // 选中的token数量
```

**ChatView 组件：**
```javascript
selectedTokenCount = 1  // 从父组件接收的token数量
```

### 3. 数据流

```
用户选择 token
    ↓
ArticleViewer (useTokenSelection hook)
    ↓
ArticleChatView.handleTokenSelect()
    - selectedTokens.length 计算数量
    ↓
ChatView (接收 selectedTokenCount)
    ↓
SuggestedQuestions (接收 tokenCount)
    - 根据数量显示对应问题
```

## 📂 修改的文件

### 1. `SuggestedQuestions.jsx`
- ✅ 添加三组不同的问题数组
- ✅ 添加 `tokenCount` prop
- ✅ 实现智能选择逻辑 `getSuggestedQuestions()`

### 2. `ChatView.jsx`
- ✅ 添加 `selectedTokenCount` prop
- ✅ 传递 `tokenCount` 给 `SuggestedQuestions`

### 3. `ArticleChatView.jsx`
- ✅ 传递 `selectedTokenCount={selectedTokens.length || 1}` 给 `ChatView`

## 🎨 效果展示

### 选中单个词（如 "aufkreuzen"）
显示问题：
- ✨ 这个词是什么意思？
- ✨ 这个词怎么用？
- ✨ 能给我一个例句吗？
- ✨ 这个词有什么词根词缀吗？

### 选中短语（如 "fixed搭配"，2-9个词）
显示问题：
- ✨ 这个短语是什么意思？
- ✨ 这个短语怎么使用？
- ✨ 这是固定搭配吗？
- ✨ 能给我一个例句吗？

### 选中整句话（10个及以上词）
显示问题：
- ✨ 这句话是什么意思？
- ✨ 这句话的语法结构是什么？
- ✨ 这句话的主谓宾是什么？
- ✨ 能解释一下这句话的用法吗？

## 🔧 自定义问题

您可以根据需要修改 `SuggestedQuestions.jsx` 中的问题数组：

```javascript
// 编辑第 14-35 行的三个问题数组
const singleTokenQuestions = [
  "你的自定义问题1",
  "你的自定义问题2",
  // ...
]
```

## 🧪 测试步骤

1. **启动服务**
   ```bash
   # 后端
   cd frontend/my-web-ui/backend
   python server.py
   
   # 前端
   cd frontend/my-web-ui
   npm run dev
   ```

2. **测试单词选择**
   - 打开文章页面
   - 点击选中一个单词
   - 查看建议问题是否显示单词相关问题

3. **测试短语选择**
   - 拖拽选中2-5个词
   - 查看建议问题是否显示短语相关问题

4. **测试整句选择**
   - 选中整句话（多个词）
   - 查看建议问题是否显示句子相关问题

## 💡 未来改进建议

1. **动态阈值调整**：可以将 10 个 token 的阈值改为可配置
2. **更多问题类型**：可以添加更多细分类型（如固定搭配、成语等）
3. **AI 生成问题**：可以让后端 AI 根据选中内容动态生成建议问题
4. **用户自定义**：允许用户添加自己常用的问题模板

## ✅ 功能状态

- ✅ 单词问题：已实现
- ✅ 短语问题：已实现
- ✅ 句子问题：已实现
- ✅ 智能切换：已实现
- ✅ 无语法错误：已验证

