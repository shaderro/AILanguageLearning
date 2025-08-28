# 📖 Vocab Explanation 功能文档

## 功能概述

Vocab Explanation 是一个词汇解释提示组件，当用户hover到Article View中的第一个token时自动显示，提供该词汇的详细解释。组件采用紧凑的圆角长方形设计，具有平滑的渐隐动画效果。

## 🎯 主要特性

### 1. 视觉设计
- **圆角长方形**: 紧凑的圆角设计
- **紧凑布局**: 最小padding，节省空间
- **深色主题**: 深灰色背景，白色文字
- **小三角形指示器**: 指向hover的词汇

### 2. 交互体验
- **Hover触发**: 鼠标悬停第一个token时显示
- **自动定位**: 根据token位置自动计算显示位置
- **渐隐动画**: 离开时平滑渐隐
- **非阻塞**: 不影响其他交互操作

### 3. 内容展示
- **标题**: "这个词的意思是..."
- **词汇**: 高亮显示目标词汇
- **解释**: 详细的词汇定义

## 🚀 使用方法

### 在 Article View 中
1. 进入文章查看页面
2. 将鼠标悬停到第一个词汇（通常是"React"）
3. Vocab Explanation 自动显示在词汇上方
4. 移开鼠标时自动渐隐

### 组件调用
```jsx
<VocabExplanation
  word="React"
  definition="一个用于构建用户界面的JavaScript库，由Facebook开发和维护，被广泛用于构建单页应用程序。"
  isVisible={showVocab}
  position={vocabPosition}
/>
```

## 🎨 UI设计细节

### 样式特点
- **背景色**: `bg-gray-800` (深灰色)
- **文字色**: `text-white` (白色)
- **圆角**: `rounded-lg` (大圆角)
- **阴影**: `shadow-lg` (大阴影)
- **内边距**: `px-3 py-2` (紧凑布局)

### 动画效果
- **显示**: `opacity-100 scale-100` (淡入+缩放)
- **隐藏**: `opacity-0 scale-95` (淡出+缩小)
- **过渡**: `transition-all duration-300 ease-in-out`

### 定位逻辑
```javascript
// 计算显示位置
const rect = event.currentTarget.getBoundingClientRect()
setVocabPosition({
  x: rect.left + rect.width / 2,  // 水平居中
  y: rect.top                     // 垂直对齐
})

// CSS变换
transform: 'translate(-50%, -100%) translateY(-8px)'
```

## 🔧 技术实现

### 状态管理
```javascript
const [vocabPosition, setVocabPosition] = useState({ x: 0, y: 0 })
const [showVocab, setShowVocab] = useState(false)
```

### 事件处理
```javascript
// Hover进入事件
const handleFirstTokenHover = (event, token) => {
  const rect = event.currentTarget.getBoundingClientRect()
  setVocabPosition({
    x: rect.left + rect.width / 2,
    y: rect.top
  })
  setShowVocab(true)
}

// Hover离开事件
const handleFirstTokenLeave = () => {
  setShowVocab(false)
}
```

### 条件渲染
```javascript
// 只在第一个token上添加hover事件
const isFirstToken = index === 0

onMouseEnter={isFirstToken ? (e) => handleFirstTokenHover(e, token) : undefined}
onMouseLeave={isFirstToken ? handleFirstTokenLeave : undefined}
```

## 📊 组件结构

### VocabExplanation 组件
```
VocabExplanation
├── 外层容器 (fixed定位, z-index: 50)
├── 内容容器 (圆角长方形)
│   ├── 标题: "这个词的意思是..."
│   └── 内容: 词汇 + 解释
└── 指示器 (小三角形)
```

### 集成到 ArticleViewer
```
ArticleViewer
├── 文章标题
├── Token列表 (第一个token有hover事件)
├── 选择统计
└── VocabExplanation (条件渲染)
```

## 🎯 自定义配置

### 可配置参数
- `word`: 要解释的词汇
- `definition`: 词汇的详细解释
- `isVisible`: 控制显示/隐藏
- `position`: 显示位置坐标

### 样式自定义
可以通过修改CSS类名来自定义：
- 背景色: `bg-gray-800`
- 文字大小: `text-sm`
- 圆角大小: `rounded-lg`
- 阴影效果: `shadow-lg`

## 🔮 未来扩展

1. **多词汇支持**: 为所有token添加解释功能
2. **动态内容**: 从API获取词汇解释
3. **多种样式**: 支持不同类型的词汇解释
4. **交互增强**: 点击查看更详细信息
5. **历史记录**: 记录用户查看过的词汇
6. **个性化**: 根据用户水平调整解释深度

## 📁 文件结构

```
src/modules/shared/components/
└── VocabExplanation.jsx        # 词汇解释组件

src/modules/article/components/
└── ArticleViewer.jsx          # 集成了VocabExplanation的文章查看器
```

## 🎉 使用效果

当用户在Article View中浏览文章时：
1. 鼠标悬停第一个词汇 → Vocab Explanation显示
2. 显示词汇的详细解释和定义
3. 移开鼠标 → 平滑渐隐消失
4. 提供即时的词汇学习辅助
5. 增强阅读体验和理解

## 💡 设计亮点

- **精确定位**: 自动计算最佳显示位置
- **流畅动画**: 平滑的显示和隐藏过渡
- **紧凑设计**: 最小化占用空间
- **直观指示**: 小三角形指向目标词汇
- **响应式**: 适配不同屏幕尺寸
