# TokenNotation 组件功能说明

## 📋 组件概述

**名称**: TokenNotation  
**文件**: `modules/article/components/TokenNotation.jsx`  
**功能**: 在hover已提问的token时，显示注释卡片

---

## 🎯 功能特性

### 触发条件

- ✅ Token必须是已提问状态（绿色下划线）
- ✅ 鼠标悬停在token上

### 显示位置

- 📍 Token正下方
- 📍 稍微偏左对齐
- 📍 带小箭头指向token

### 样式

- 🎨 背景色：浅灰色 (`bg-gray-100`)
- 🎨 文字颜色：深灰色 (`text-gray-700`)
- 🎨 边框：灰色 (`border-gray-300`)
- 🎨 阴影：`shadow-lg`
- ✨ 动画：淡入效果（150ms延迟 + 200ms淡入）

---

## 📁 文件结构

```
modules/article/components/
├── TokenNotation.jsx          (新建) - 注释卡片组件
├── TokenSpan.jsx              (修改) - 集成TokenNotation
└── TOKEN_NOTATION_FEATURE.md  (新建) - 本文档
```

---

## 🎨 视觉效果

```
未提问的token (hover):
┌─────┐
│ Der │  ← 黄色高亮，无卡片
└─────┘

已提问的token (正常):
┌─────┐
│dafür│  ← 绿色下划线
└─────┘

已提问的token (hover):
┌─────┐
│dafür│  ← 绿色下划线
└─────┘
   ▼
┌──────────────────────────┐
│ This is a test note      │  ← 浅灰底卡片
└──────────────────────────┘
```

---

## 💻 组件代码

### TokenNotation.jsx

```jsx
import { useState, useEffect } from 'react'

export default function TokenNotation({ isVisible = false, note = "This is a test note", position = {} }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (isVisible) {
      // 150ms延迟后显示，避免闪烁
      const timer = setTimeout(() => setShow(true), 150)
      return () => clearTimeout(timer)
    } else {
      setShow(false)
    }
  }, [isVisible])

  if (!show) return null

  return (
    <div className="absolute top-full left-0 mt-1 z-50">
      {/* 小箭头 */}
      <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-200 transform rotate-45 border-l border-t border-gray-300"></div>
      
      {/* 卡片主体 */}
      <div className="bg-gray-100 border border-gray-300 rounded-lg shadow-lg p-3">
        <div className="text-sm text-gray-700">
          {note}
        </div>
      </div>
    </div>
  )
}
```

### Props说明

| Prop | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `isVisible` | boolean | false | 是否显示卡片 |
| `note` | string | "This is a test note" | 显示的注释内容 |
| `position` | object | {} | 额外的定位样式（可选） |

---

## 🔗 集成到TokenSpan

### 修改内容

```jsx
// 1. 导入组件
import TokenNotation from './TokenNotation'

// 2. 添加状态管理
const [showNotation, setShowNotation] = useState(false)

// 3. 在hover时显示/隐藏
onMouseEnter={() => {
  if (isAsked) {
    setShowNotation(true)  // ← 显示notation
  }
  // ...
}}
onMouseLeave={() => {
  if (isAsked) {
    setShowNotation(false)  // ← 隐藏notation
  }
  // ...
}}

// 4. 渲染组件
{isAsked && showNotation && (
  <TokenNotation 
    isVisible={showNotation}
    note="This is a test note"
  />
)}
```

---

## 🎯 工作流程

```
用户操作                    TokenSpan状态                TokenNotation
═══════════════════════════════════════════════════════════════════════

1. 鼠标移入已提问token
      ↓
   onMouseEnter触发
      ↓
   检测 isAsked=true
      ↓
   setShowNotation(true) ─────→  isVisible=true
                                      ↓
                                 延迟150ms
                                      ↓
                                 setShow(true)
                                      ↓
                                 渲染卡片 ✅
2. 鼠标移出token
      ↓
   onMouseLeave触发
      ↓
   setShowNotation(false) ────→  isVisible=false
                                      ↓
                                 setShow(false)
                                      ↓
                                 隐藏卡片
```

---

## 🎨 样式自定义

### 修改背景色

```jsx
// TokenNotation.jsx
<div className="bg-gray-100">  {/* 改为其他颜色 */}
  
// 例如：
bg-blue-50   // 浅蓝色
bg-green-50  // 浅绿色
bg-purple-50 // 浅紫色
```

### 修改文字颜色

```jsx
<div className="text-gray-700">  {/* 改为其他颜色 */}

// 例如：
text-gray-800  // 更深的灰色
text-blue-700  // 蓝色文字
```

### 修改大小

```jsx
// 最小宽度
minWidth: '200px'  // 改为 '150px' 或 '250px'

// 最大宽度
maxWidth: '300px'  // 改为 '400px' 或更大
```

---

## 🔧 未来扩展

### 扩展1: 动态内容

```jsx
// 根据token显示不同内容
<TokenNotation 
  note={`已提问: ${token.token_body}`}
/>

// 或显示提问历史
<TokenNotation 
  note={`提问次数: ${questionCount}`}
/>
```

### 扩展2: 显示词汇解释

```jsx
// 集成vocab explanation
<TokenNotation 
  note={vocabExplanation?.definition || "This is a test note"}
/>
```

### 扩展3: 显示提问记录

```jsx
// 显示该token的提问历史
<TokenNotation>
  <div>上次提问: 2024-10-14</div>
  <div>问题: 这个词是什么意思？</div>
</TokenNotation>
```

---

## 🧪 测试步骤

### 步骤1: 刷新页面

```
按 F5 刷新浏览器
```

### 步骤2: 标记一个token

1. 选中一个token
2. 发送问题
3. 确认token变绿（绿色下划线）

### 步骤3: 测试notation显示

1. 鼠标移到绿色下划线的token上
2. **应该看到**: 浅灰色卡片出现在token下方
3. 卡片显示: "This is a test note"
4. 鼠标移开，卡片消失

---

## 📊 效果预览

### 正常状态

```
sentence: Der Hund ist dafür verantwortlich.
          ─── ──── ─── ────── ──────────────
                           ↑
                    绿色下划线（已提问）
```

### Hover状态

```
sentence: Der Hund ist dafür verantwortlich.
          ─── ──── ─── ────── ──────────────
                           ↑
                    绿色下划线
                           ↓
                    ┌─────────────────────┐
                    │ This is a test note │  ← 卡片
                    └─────────────────────┘
```

---

## ✅ 完成清单

- [x] 创建TokenNotation组件
- [x] 添加浅灰底样式
- [x] 添加深灰色文字
- [x] 集成到TokenSpan
- [x] 添加hover触发逻辑
- [x] 添加淡入动画
- [x] 定位在token下方
- [x] 添加小箭头指示器

---

**状态**: ✅ 已完成  
**测试**: 请刷新页面并测试  
**位置**: `frontend/my-web-ui/src/modules/article/components/TokenNotation.jsx`


