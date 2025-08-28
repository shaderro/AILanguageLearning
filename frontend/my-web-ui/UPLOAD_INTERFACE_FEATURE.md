# 📤 Upload Interface 上传界面功能文档

## 功能概述

Upload Interface 是一个完整的上传界面，当用户点击"Upload New"按钮后显示。该界面提供三种上传方式：URL上传、文件选择和拖拽上传，同时聊天功能暂时不可用。

## 🎯 主要特性

### 1. 三种上传方式
- **URL上传**: 输入文章URL进行上传
- **文件选择**: 点击按钮选择本地文件
- **拖拽上传**: 拖拽文件到指定区域

### 2. 界面设计
- **居中布局**: 所有上传选项垂直居中显示
- **分隔线**: 使用"OR"分隔不同的上传方式
- **状态反馈**: 上传成功后显示状态提示
- **文件格式**: 支持TXT、MD、PDF、DOC、DOCX格式

### 3. 交互体验
- **拖拽效果**: 拖拽时边框和背景变色
- **文件验证**: 支持多种文件格式
- **状态管理**: 实时显示上传状态
- **禁用聊天**: 上传模式下聊天功能暂时不可用

## 🚀 使用方法

### 进入上传模式
1. 在Article Selection页面点击"Upload New"按钮
2. 跳转到Article-Chat页面，显示上传界面
3. 左侧显示上传选项，右侧聊天功能暂时不可用

### 上传方式
1. **URL上传**: 输入文章URL，点击"Upload from URL"
2. **文件选择**: 点击"Choose File"选择本地文件
3. **拖拽上传**: 将文件拖拽到虚线框内

## 🎨 UI设计细节

### 布局结构
```
Upload Interface
├── 标题: "Upload New Article"
├── URL上传区域
│   ├── 标题: "Upload URL"
│   ├── URL输入框
│   └── 上传按钮
├── 分隔线: "OR"
├── 文件选择区域
│   ├── 标题: "Upload File"
│   └── 选择文件按钮
├── 分隔线: "OR"
├── 拖拽区域
│   ├── 标题: "Drop File"
│   ├── 拖拽图标
│   ├── 提示文字
│   └── 支持格式说明
└── 上传状态 (条件显示)
```

### 样式特点
- **URL输入框**: 蓝色边框，聚焦时蓝色环形
- **文件选择按钮**: 绿色背景，悬停变深
- **拖拽区域**: 虚线边框，拖拽时变蓝色
- **分隔线**: 灰色线条，中间"OR"文字

## 🔧 技术实现

### 状态管理
```javascript
const [dragActive, setDragActive] = useState(false)
const [uploadMethod, setUploadMethod] = useState(null) // 'url', 'file', 'drop'
const fileInputRef = useRef(null)
```

### 拖拽处理
```javascript
const handleDrag = (e) => {
  e.preventDefault()
  e.stopPropagation()
  if (e.type === "dragenter" || e.type === "dragover") {
    setDragActive(true)
  } else if (e.type === "dragleave") {
    setDragActive(false)
  }
}

const handleDrop = (e) => {
  e.preventDefault()
  e.stopPropagation()
  setDragActive(false)
  setUploadMethod('drop')
  
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    console.log('File dropped:', e.dataTransfer.files[0])
  }
}
```

### 文件选择
```javascript
const handleFileSelect = (e) => {
  if (e.target.files && e.target.files[0]) {
    console.log('File selected:', e.target.files[0])
    setUploadMethod('file')
  }
}

const triggerFileInput = () => {
  fileInputRef.current?.click()
}
```

### URL提交
```javascript
const handleUrlSubmit = (e) => {
  e.preventDefault()
  const url = e.target.url.value.trim()
  if (url) {
    console.log('URL submitted:', url)
    setUploadMethod('url')
  }
}
```

## 📊 聊天功能状态

### 禁用状态
- **透明度**: 聊天界面透明度降低到50%
- **标题**: 显示"聊天助手 (暂时不可用)"
- **描述**: 显示"请先上传文章内容"
- **输入框**: 禁用状态，显示"聊天暂时不可用"
- **发送按钮**: 禁用状态

### 状态切换
```javascript
// 在ArticleChatView中
<ChatView 
  quotedText={quotedText}
  onClearQuote={handleClearQuote}
  disabled={isUploadMode}
/>
```

## 🎯 交互流程

### 完整流程
1. **点击Upload New**: 从Article Selection跳转到上传界面
2. **选择上传方式**: URL、文件选择或拖拽
3. **上传文件**: 处理文件上传逻辑
4. **状态反馈**: 显示上传成功状态
5. **聊天禁用**: 聊天功能暂时不可用

### 状态变化
```
Article Selection → Upload Interface → 上传成功 → 聊天可用
                ↓
            聊天功能禁用
```

## 🔮 未来扩展

1. **文件处理**: 实现实际的文件上传和处理
2. **进度显示**: 添加上传进度条
3. **错误处理**: 显示上传错误信息
4. **文件预览**: 上传前预览文件内容
5. **批量上传**: 支持同时上传多个文件
6. **格式转换**: 自动转换不同格式的文件
7. **OCR功能**: 支持图片文字识别

## 📁 文件结构

```
src/modules/article/
├── ArticleChatView.jsx        # 主组件，支持上传模式
├── ArticleSelection.jsx       # 文章选择页面
└── components/
    ├── UploadInterface.jsx    # 上传界面组件
    └── ChatView.jsx          # 聊天组件（支持禁用状态）
```

## 🎉 使用效果

当用户进入上传模式时：
1. 页面左侧显示三种上传方式
2. 右侧聊天界面显示禁用状态
3. 支持URL、文件选择和拖拽上传
4. 上传成功后显示状态反馈
5. 提供直观的上传功能入口

## 💡 设计亮点

- **多种上传方式**: 满足不同用户的使用习惯
- **直观的界面**: 清晰的分隔和提示
- **状态反馈**: 实时显示上传状态
- **禁用聊天**: 避免在无内容时使用聊天功能
- **响应式设计**: 适配不同屏幕尺寸
- **用户体验**: 流畅的拖拽和选择交互
