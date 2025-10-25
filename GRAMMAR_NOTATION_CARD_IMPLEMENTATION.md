# 语法注释卡片功能实现总结

## 功能概述

实现了语法注释卡片组件，当用户悬停在语法注释下划线上时，会在该句子下方显示一个卡片，按顺序显示该句子的所有语法规则的详细信息。

## 实现组件

### 1. GrammarNotationCard.jsx
- **功能**: 显示语法注释卡片的主要组件
- **特性**:
  - 显示句子的所有语法规则
  - 按顺序展示规则名称、规则解释和上下文解释
  - 支持加载状态和错误处理
  - 可关闭的卡片界面
  - 响应式定位

### 2. GrammarNotation.jsx (修改)
- **新增功能**:
  - 集成GrammarNotationCard组件
  - 智能悬停检测（避免与vocab notation和asked token冲突）
  - 自动计算卡片位置
  - 延迟隐藏机制

### 3. API服务扩展
- **新增方法**: `getSentenceGrammarRules(textId, sentenceId)`
- **功能**: 直接获取指定句子的所有语法规则
- **回退机制**: 如果新API失败，自动回退到原有方法

## 核心特性

### 悬停优先级管理
```javascript
// 检查是否悬停在vocab notation或asked token上
const isVocabNotation = target.closest('.vocab-notation')
const isAskedToken = target.closest('.asked-token')

// 只有在没有悬停在vocab notation或asked token上时才显示卡片
if (!isVocabNotation && !isAskedToken) {
  // 显示语法注释卡片
}
```

### 智能定位
- 自动计算卡片位置，避免超出视窗边界
- 优先显示在元素下方，空间不足时显示在上方
- 左右边界智能对齐

### 数据获取策略
1. 优先使用新的API端点获取句子语法规则
2. 如果失败，回退到原有的标注获取方法
3. 支持多种数据格式的解析

## 使用方法

### 基本使用
```jsx
import GrammarNotation from './GrammarNotation'

<GrammarNotation
  isVisible={true}
  textId={1}
  sentenceId={1}
  grammarId={1}
  markedTokenIds={[]}
  onMouseEnter={handleMouseEnter}
  onMouseLeave={handleMouseLeave}
/>
```

### 卡片显示内容
- **规则名称**: 语法规则的名称
- **规则解释**: 语法规则的详细解释
- **上下文解释**: 在该句子中的具体应用说明

## 测试组件

创建了 `GrammarNotationTest.jsx` 用于测试功能：
- 模拟语法注释下划线
- 测试悬停交互
- 验证优先级管理
- 调试信息显示

## 技术细节

### 状态管理
- `showCard`: 控制卡片显示/隐藏
- `cardPosition`: 卡片定位信息
- `grammarRules`: 语法规则数据

### 事件处理
- `handleMouseEnter`: 智能悬停检测
- `handleMouseLeave`: 延迟隐藏机制
- `handleCloseCard`: 手动关闭卡片

### 样式设计
- 固定定位的卡片
- 阴影和边框效果
- 响应式布局
- 滚动支持

## 兼容性

- 与现有的vocab notation和asked token系统完全兼容
- 支持现有的API结构
- 保持向后兼容性

## 未来扩展

1. **动画效果**: 可以添加卡片的淡入淡出动画
2. **交互增强**: 支持卡片内的进一步交互
3. **性能优化**: 缓存语法规则数据
4. **主题支持**: 支持深色模式等主题切换

## 文件结构

```
frontend/my-web-ui/src/modules/article/components/
├── GrammarNotation.jsx          # 主组件（已修改）
├── GrammarNotationCard.jsx      # 卡片组件（新增）
└── GrammarNotationTest.jsx      # 测试组件（新增）

frontend/my-web-ui/src/services/
└── api.js                       # API服务（已扩展）
```

## 总结

成功实现了语法注释卡片功能，提供了完整的用户交互体验。该功能与现有系统完全兼容，并提供了智能的悬停检测和定位机制。用户现在可以通过悬停在语法注释下划线上来查看详细的语法规则信息。
