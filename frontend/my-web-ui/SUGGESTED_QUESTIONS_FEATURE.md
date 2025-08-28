# 💭 Suggested Questions 功能文档

## 功能概述

Suggested Questions 是一个智能建议问题组件，当用户在Article View中选择token后，会在聊天窗口的输入框上方显示相关的问题建议。用户点击任意建议问题后，系统会自动发送该问题并生成相应的AI回复。

## 🎯 主要特性

### 1. 视觉设计
- **长方形组件**: 与聊天窗口同宽
- **两边对齐**: 与聊天窗口边缘对齐
- **浅色背景**: 灰色背景，与聊天界面协调
- **按钮样式**: 圆角边框，悬停效果

### 2. 交互体验
- **条件显示**: 只在选择token后显示
- **状态重置**: 每次显示时重置所有问题为未选中状态
- **一键发送**: 点击问题自动发送
- **状态反馈**: 选中问题高亮显示
- **自动回复**: 发送后自动生成AI回复
- **智能取消**: 输入内容或点击其他位置时取消高亮

### 3. 内容展示
- **提示文字**: "你可能想问..."
- **问题列表**: 4个预设的智能问题
- **引用关联**: 问题与选中的文本关联

## 🚀 使用方法

### 在 Article Chat View 中
1. 在Article View中选择任意token
2. 聊天窗口上方出现Suggested Questions组件
3. 点击任意建议问题
4. 系统自动发送问题并生成AI回复

### 组件调用
```jsx
<SuggestedQuestions
  quotedText={quotedText}
  onQuestionSelect={handleSuggestedQuestionSelect}
  isVisible={!!quotedText}
/>
```

## 🎨 UI设计细节

### 布局结构
```
Suggested Questions
├── 外层容器 (w-full, 与聊天窗口同宽)
├── 标题区域 ("你可能想问...")
└── 问题按钮区域 (flex布局)
    ├── 问题1: "这句话是什么意思？"
    ├── 问题2: "这句话的语法结构是什么？"
    ├── 问题3: "这个词汇怎么使用？"
    └── 问题4: "能给我一个例句吗？"
```

### 样式特点
- **容器**: `bg-gray-50 border-t border-gray-200`
- **标题**: `text-sm text-gray-600`
- **按钮**: `px-3 py-1.5 text-sm rounded-lg border`
- **悬停**: `hover:bg-blue-50 hover:border-blue-300`
- **选中**: `bg-blue-500 text-white border-blue-500`

### 响应式设计
- **宽度**: `w-full` (与聊天窗口同宽)
- **内边距**: `px-4 py-3` (两边对齐)
- **按钮**: `flex flex-wrap gap-2` (自适应换行)

## 🔧 技术实现

### 状态管理
```javascript
const [selectedQuestion, setSelectedQuestion] = useState(null)

// 当组件显示时，重置选中状态
useEffect(() => {
  if (isVisible) {
    setSelectedQuestion(null)
  }
}, [isVisible])

// 当输入框有内容时，取消高亮
useEffect(() => {
  if (inputValue.trim() !== '') {
    setSelectedQuestion(null)
  }
}, [inputValue])
```

### 问题列表
```javascript
const suggestedQuestions = [
  "这句话是什么意思？",
  "这句话的语法结构是什么？",
  "这个词汇怎么使用？",
  "能给我一个例句吗？"
]
```

### 事件处理
```javascript
const handleQuestionClick = (question) => {
  setSelectedQuestion(question)
  onQuestionSelect(question)
  // 通知父组件问题被点击
  if (onQuestionClick) {
    onQuestionClick(question)
  }
}

// 点击其他位置取消高亮
const handleContainerClick = (e) => {
  // 如果点击的是容器而不是按钮，取消高亮
  if (e.target === e.currentTarget) {
    setSelectedQuestion(null)
  }
}

const handleSuggestedQuestionSelect = (question) => {
  // 自动发送选中的问题
  const userMessage = {
    id: Date.now(),
    text: question,
    isUser: true,
    timestamp: new Date(),
    quote: quotedText || null
  }
  
  setMessages(prev => [...prev, userMessage])
  
  // 清除引用并生成AI回复
  if (onClearQuote) {
    onClearQuote()
  }
  
  // 延迟生成AI回复
  setTimeout(() => {
    const autoReply = {
      id: Date.now() + 1,
      text: `关于"${quotedText}"，${question} 这是一个很好的问题！让我为你详细解释一下...`,
      isUser: false,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, autoReply])
  }, 1000)
}
```

## 📊 组件结构

### SuggestedQuestions 组件
```
SuggestedQuestions
├── 条件渲染 (isVisible && quotedText)
├── 外层容器 (w-full, bg-gray-50)
├── 标题区域 ("你可能想问...")
└── 问题按钮区域
    └── 4个问题按钮 (map渲染)
```

### 集成到 ChatView
```
ChatView
├── 聊天头部
├── 消息区域
├── 引用显示 (条件)
├── Suggested Questions (条件) ← 新增
├── 输入区域
└── Toast Notice
```

## 🎯 交互流程

### 完整流程
1. **选择Token**: 用户在Article View中选择文本
2. **显示引用**: 聊天窗口显示选中的文本
3. **显示建议**: Suggested Questions组件出现（所有问题未选中状态）
4. **点击问题**: 用户点击任意建议问题（问题高亮）
5. **自动发送**: 系统自动发送问题消息
6. **AI回复**: 生成相关的AI回复
7. **清除状态**: 清除引用和建议问题
8. **Toast提示**: 显示知识点总结

### 状态管理流程
- **显示时**: 重置所有问题为未选中状态
- **点击问题**: 选中问题高亮显示
- **输入内容**: 自动取消所有问题高亮
- **点击其他位置**: 取消当前选中问题的高亮

### 状态变化
```
无选择 → 选择Token → 显示建议(未选中) → 点击问题(高亮) → 发送消息 → 清除状态
                ↓
            输入内容 → 取消高亮
                ↓
            点击其他位置 → 取消高亮
```

## 🔮 未来扩展

1. **智能问题**: 根据选中内容动态生成问题
2. **个性化**: 根据用户历史调整问题类型
3. **多语言**: 支持不同语言的问题建议
4. **问题分类**: 按语法、词汇、理解等分类
5. **学习进度**: 根据用户掌握程度调整问题难度
6. **问题历史**: 记录用户常用的问题类型

## 📁 文件结构

```
src/modules/article/components/
├── SuggestedQuestions.jsx    # 建议问题组件
└── ChatView.jsx             # 集成了SuggestedQuestions的聊天组件
```

## 🎉 使用效果

当用户在Article Chat View中与AI助手交互时：
1. 选择文本 → 显示引用和建议问题
2. 点击建议问题 → 自动发送并生成回复
3. 提供智能的学习引导
4. 简化用户输入流程
5. 增强学习体验和交互效率

## 💡 设计亮点

- **智能建议**: 提供相关的学习问题
- **一键操作**: 简化用户输入流程
- **视觉协调**: 与聊天界面完美融合
- **响应式布局**: 适配不同屏幕尺寸
- **状态管理**: 精确控制显示和隐藏
- **用户体验**: 流畅的交互流程
