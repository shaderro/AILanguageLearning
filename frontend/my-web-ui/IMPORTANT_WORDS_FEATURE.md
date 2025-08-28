# 🔤 Important Words 重点词汇功能文档

## 功能概述

Important Words 功能为Article View中的重点词汇提供特殊标记和交互体验。重点词汇会以加粗样式显示，当用户hover时会出现Vocab Explanation组件，提供详细的词汇解释。

## 🎯 主要特性

### 1. 视觉设计
- **加粗显示**: 重点词汇使用`font-bold`样式
- **特殊背景**: 浅黄色背景(`bg-yellow-50`)突出显示
- **悬停效果**: hover时背景变为`bg-yellow-100`
- **颜色区分**: 重点词汇使用深灰色文字(`text-gray-800`)

### 2. 交互体验
- **Hover触发**: 鼠标悬停重点词汇时显示解释
- **动态定位**: 根据词汇位置自动计算显示位置
- **边界检测**: 自动调整位置避免被屏幕边缘切掉
- **智能显示**: 优先显示在词汇下方（40px偏移），空间不足时显示在上方
- **平滑动画**: Vocab Explanation的渐隐效果
- **精确解释**: 每个重点词汇都有对应的详细定义

### 3. 内容展示
- **词汇列表**: 8个React相关的重点词汇
- **详细定义**: 每个词汇都有完整的解释
- **统计信息**: 显示重点词汇总数和选中数量

## 🚀 使用方法

### 在 Article View 中
1. 进入文章查看页面
2. 重点词汇以加粗样式显示（浅黄色背景）
3. 将鼠标悬停到任意重点词汇上
4. Vocab Explanation自动显示词汇解释
5. 移开鼠标时解释自动消失

### 重点词汇列表
- **React**: 一个用于构建用户界面的JavaScript库
- **JavaScript**: 一种高级的、解释型的编程语言
- **组件**: React中的基本构建块，是可重用的UI元素
- **虚拟DOM**: React的核心概念，轻量级JavaScript对象
- **JSX**: JavaScript XML的缩写，React中用于描述UI的语法扩展
- **状态**: React组件中的数据，改变时触发重新渲染
- **生命周期**: React组件从创建到销毁的整个过程
- **事件处理**: React中处理用户交互的方式

## 🎨 UI设计细节

### 样式特点
- **重点词汇**: `bg-yellow-50 text-gray-800 font-bold`
- **悬停效果**: `hover:bg-yellow-100`
- **选中状态**: `bg-blue-500 text-white` (覆盖重点词汇样式)
- **普通词汇**: `bg-gray-100 text-gray-700`

### 布局结构
```
ArticleViewer
├── 文章标题
├── Token列表
│   ├── 普通词汇 (灰色背景)
│   ├── 重点词汇 (黄色背景 + 加粗)
│   └── 选中词汇 (蓝色背景)
├── 统计信息
│   ├── 选中词汇数量
│   ├── 选中重点词汇数量
│   └── 重点词汇总数
└── Vocab Explanation (条件显示)
```

## 🔧 技术实现

### 状态管理
```javascript
const [currentVocabWord, setCurrentVocabWord] = useState('')
const [currentVocabDefinition, setCurrentVocabDefinition] = useState('')

// 重点词汇列表
const importantWords = new Set([
  'React', 'JavaScript', '组件', '虚拟DOM', 'JSX', '状态', '生命周期', '事件处理'
])

// 词汇定义映射
const vocabDefinitions = {
  'React': '一个用于构建用户界面的JavaScript库...',
  'JavaScript': '一种高级的、解释型的编程语言...',
  // ... 其他词汇定义
}
```

### 事件处理
```javascript
const handleVocabHover = (event, token) => {
  const rect = event.currentTarget.getBoundingClientRect()
  setVocabPosition({
    x: rect.left + rect.width / 2,
    y: rect.top
  })
  setCurrentVocabWord(token)
  setCurrentVocabDefinition(vocabDefinitions[token] || '暂无定义')
  setShowVocab(true)
}

const handleVocabLeave = () => {
  setShowVocab(false)
}
```

### 边界检测和位置调整
```javascript
const getAdjustedPosition = () => {
  const cardWidth = 320 // 估计的卡片宽度
  const cardHeight = 120 // 估计的卡片高度
  const margin = 16 // 边距
  
  let adjustedX = position.x
  let adjustedY = position.y
  let showAbove = false // 是否显示在词汇上方
  
  // 检查左边界
  if (position.x - cardWidth / 2 < margin) {
    adjustedX = cardWidth / 2 + margin
  }
  
  // 检查右边界
  if (position.x + cardWidth / 2 > window.innerWidth - margin) {
    adjustedX = window.innerWidth - cardWidth / 2 - margin
  }
  
  // 检查下边界（确保卡片完全显示，包括偏移量）
  if (position.y + cardHeight + verticalOffset > window.innerHeight - margin) {
    adjustedY = position.y - cardHeight - 20
    showAbove = true
  }
  
  return { x: adjustedX, y: adjustedY, showAbove }
}
```

### 显示位置调整
```javascript
// 垂直偏移量
const verticalOffset = 40 // 确保不遮挡词汇本身

// 变换样式
transform: adjustedPosition.showAbove 
  ? 'translate(-50%, -100%) translateY(-8px)' // 显示在上方
  : 'translate(-50%, 0) translateY(40px)' // 显示在下方，40px偏移
```
```

### 条件渲染
```javascript
const isImportantWord = importantWords.has(token)

// 样式条件
className={`
  ${isSelected 
    ? 'bg-blue-500 text-white hover:bg-blue-600' 
    : isImportantWord
      ? 'bg-yellow-50 text-gray-800 hover:bg-yellow-100 font-bold'
      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
  }
`}

// 事件条件
onMouseEnter={isImportantWord ? (e) => handleVocabHover(e, token) : undefined}
onMouseLeave={isImportantWord ? handleVocabLeave : undefined}
```

## 📊 统计功能

### 显示信息
- **总选中数**: 所有选中的词汇数量
- **重点词汇选中数**: 选中的重点词汇数量
- **重点词汇总数**: 文章中的重点词汇总数
- **使用提示**: "加粗显示，hover查看解释"

### 计算逻辑
```javascript
// 选中的重点词汇数量
Array.from(selectedTokens).filter(token => importantWords.has(token)).length

// 重点词汇总数
importantWords.size
```

## 🎯 交互流程

### 完整流程
1. **页面加载**: 重点词汇自动加粗显示
2. **Hover重点词汇**: 显示Vocab Explanation（优先显示在下方）
3. **边界检测**: 自动调整位置避免被屏幕边缘切掉
4. **查看解释**: 显示词汇的详细定义
5. **移开鼠标**: 解释自动消失
6. **选择词汇**: 可以正常选择重点词汇
7. **统计更新**: 实时更新选中统计信息

### 状态优先级
```
选中状态 > 重点词汇状态 > 普通词汇状态
```

## 🔮 未来扩展

1. **动态词汇**: 根据文章内容动态识别重点词汇
2. **用户自定义**: 允许用户添加/删除重点词汇
3. **学习进度**: 根据用户掌握程度调整词汇难度
4. **多语言支持**: 支持不同语言的重点词汇
5. **词汇分类**: 按主题、难度等分类重点词汇
6. **学习记录**: 记录用户查看过的词汇解释

## 📁 文件结构

```
src/modules/article/components/
└── ArticleViewer.jsx          # 集成了重点词汇功能的文章查看器

src/modules/shared/components/
└── VocabExplanation.jsx       # 词汇解释组件
```

## 🎉 使用效果

当用户在Article View中浏览文章时：
1. 重点词汇以加粗样式突出显示
2. Hover时获得即时的词汇解释
3. 提供专业的学习辅助
4. 增强阅读体验和理解
5. 支持正常的词汇选择功能

## 💡 设计亮点

- **视觉突出**: 加粗和颜色区分重点词汇
- **即时解释**: Hover即可查看详细定义
- **状态管理**: 精确控制显示和隐藏
- **统计信息**: 实时显示选中和总数
- **用户体验**: 流畅的交互和动画效果
- **扩展性**: 易于添加新的重点词汇
