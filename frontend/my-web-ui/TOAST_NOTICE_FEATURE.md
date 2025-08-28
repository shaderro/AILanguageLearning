# 🍞 Toast Notice 功能文档

## 功能概述

Toast Notice 是一个轻量级的通知组件，用于在用户界面中显示临时的提示信息。目前集成在 Article Chat View 中，当AI回复消息后自动显示知识点总结提示。

## 🎯 主要特性

### 1. 视觉设计
- **4:3 圆角长方形**: 符合设计要求的宽高比
- **居中显示**: 在聊天窗口中央弹出
- **渐隐动画**: 2秒后平滑渐隐消失
- **蓝色主题**: 使用蓝色背景，白色文字

### 2. 交互体验
- **自动触发**: AI回复消息后自动显示
- **定时消失**: 2秒后自动渐隐
- **非阻塞**: 不影响用户继续操作
- **平滑动画**: 淡入淡出效果

### 3. 内容展示
- **图标**: 包含成功图标
- **标题**: "知识点总结"
- **消息**: 动态显示具体的知识点内容

## 🚀 使用方法

### 在 Article Chat View 中
1. 进入文章聊天页面
2. 发送任意消息给AI助手
3. 等待AI回复（1秒延迟）
4. AI回复后500ms，Toast自动显示
5. 2秒后自动渐隐消失

### 组件调用
```jsx
<ToastNotice
  message="React组件化开发知识点已总结加入列表"
  isVisible={showToast}
  onClose={handleToastClose}
  duration={2000}
/>
```

## 🎨 UI设计细节

### 样式特点
- **背景色**: `bg-blue-600` (蓝色)
- **文字色**: `text-white` (白色)
- **圆角**: `rounded-lg` (大圆角)
- **阴影**: `shadow-lg` (大阴影)
- **尺寸**: 4:3 宽高比，最小280px，最大400px

### 动画效果
- **显示**: `opacity-100 scale-100` (淡入+缩放)
- **隐藏**: `opacity-0 scale-95` (淡出+缩小)
- **过渡**: `transition-all duration-300 ease-in-out`

### 布局结构
```
Toast Notice
├── 外层容器 (fixed, 居中)
├── 内容容器 (4:3 比例)
│   ├── 图标 + 标题
│   └── 消息文本
└── 动画状态控制
```

## 🔧 技术实现

### 状态管理
```javascript
const [showToast, setShowToast] = useState(false)
const [toastMessage, setToastMessage] = useState('')
```

### 触发逻辑
```javascript
// AI回复后延迟显示Toast
setTimeout(() => {
  const randomPoint = knowledgePoints[Math.floor(Math.random() * knowledgePoints.length)]
  setToastMessage(`${randomPoint}知识点已总结加入列表`)
  setShowToast(true)
}, 500)
```

### 自动隐藏
```javascript
// 2秒后开始渐隐
const timer = setTimeout(() => {
  setIsFading(true)
  
  // 300ms后完全隐藏
  const fadeTimer = setTimeout(() => {
    setIsShowing(false)
    onClose && onClose()
  }, 300)
}, duration)
```

## 📊 知识点列表

当前包含的React相关知识点：
- React组件化开发
- 虚拟DOM技术
- JSX语法特性
- 状态管理原理
- 生命周期钩子
- 事件处理机制
- 条件渲染技巧
- 列表渲染优化

## 🎯 自定义配置

### 可配置参数
- `message`: 显示的消息内容
- `duration`: 显示时长（默认2000ms）
- `isVisible`: 控制显示/隐藏
- `onClose`: 关闭回调函数

### 样式自定义
可以通过修改CSS类名来自定义：
- 背景色: `bg-blue-600`
- 文字大小: `text-sm`
- 圆角大小: `rounded-lg`
- 阴影效果: `shadow-lg`

## 🔮 未来扩展

1. **多种类型**: 支持成功、警告、错误等不同类型
2. **自定义位置**: 支持顶部、底部、左上角等不同位置
3. **手动关闭**: 添加关闭按钮，支持手动关闭
4. **队列管理**: 支持多个Toast同时显示
5. **主题切换**: 支持深色/浅色主题
6. **国际化**: 支持多语言显示

## 📁 文件结构

```
src/modules/shared/components/
└── ToastNotice.jsx          # Toast通知组件

src/modules/article/components/
└── ChatView.jsx            # 集成了Toast的聊天组件
```

## 🎉 使用效果

当用户在Article Chat View中与AI助手对话时：
1. 发送消息 → AI回复 → Toast显示知识点总结
2. 用户体验流畅，不会打断对话流程
3. 提供有价值的知识点反馈
4. 增强学习体验和交互感
