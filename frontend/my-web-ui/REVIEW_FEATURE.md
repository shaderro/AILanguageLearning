# 📚 Review Feature Documentation

## 功能概述

Review功能是一个交互式的单词复习系统，允许用户通过选择"模糊"、"认识"或"不认识"来评估自己对单词的掌握程度。

## 🎯 主要功能

### 1. Review Card 组件
- **单词展示**: 显示当前复习的单词
- **进度条**: 显示复习进度（当前单词/总单词数）
- **三个选项按钮**:
  - 🤔 模糊 (Vague) - 黄色按钮
  - ✅ 认识 (Known) - 绿色按钮  
  - ❌ 不认识 (Unknown) - 红色按钮

### 2. 复习流程
1. 用户看到单词，选择熟悉程度
2. 显示单词释义和例句
3. 点击"Next Word"继续下一个单词
4. 完成所有单词后显示结果

### 3. Review Results 组件
- **统计信息**: 显示认识、模糊、不认识的单词数量
- **掌握程度**: 进度条显示整体掌握水平
- **详细结果**: 每个单词的选择结果列表
- **操作按钮**: 重新开始或关闭

## 🚀 使用方法

### 在Word Demo页面
1. 点击右下角的"Start Review"按钮
2. 进入复习模式，逐个评估单词
3. 完成所有单词后查看结果
4. 可以选择重新开始或关闭

### 组件结构
```
src/modules/word-demo/
├── components/
│   ├── ReviewCard.jsx          # 复习卡片组件
│   ├── ReviewResults.jsx       # 复习结果组件
│   ├── WordCard.jsx           # 单词卡片组件
│   └── WordCardDetail.jsx     # 单词详情组件
└── WordDemo.jsx               # 主页面组件
```

## 🎨 UI设计特点

### Review Card
- 清晰的进度显示
- 直观的颜色编码（绿色=认识，黄色=模糊，红色=不认识）
- 响应式设计，适配不同屏幕尺寸
- 平滑的动画过渡效果

### Review Results
- 统计卡片展示各项数据
- 进度条显示整体掌握程度
- 可滚动的详细结果列表
- 清晰的操作按钮

## 🔧 技术实现

### 状态管理
- `isReviewMode`: 控制复习模式开关
- `isReviewComplete`: 控制结果页面显示
- `reviewResults`: 存储用户选择结果
- `currentIndex`: 跟踪当前复习进度

### API集成
- 使用现有的 `/api/word` 端点获取单词数据
- 异步加载单词释义和例句
- 错误处理和加载状态

### 用户体验
- 流畅的模态框切换
- 直观的进度反馈
- 清晰的操作指引
- 完整的结果统计

## 📊 数据结构

### 用户选择结果
```javascript
{
  word: "apple",
  choice: "known" // "known" | "vague" | "unknown"
}
```

### 单词数据
```javascript
{
  word: "apple",
  definition: "A round fruit with red, yellow, or green skin and white flesh",
  example: "I eat an apple every day for breakfast."
}
```

## 🎯 未来扩展

1. **复习历史**: 保存用户的复习记录
2. **智能推荐**: 根据掌握程度推荐复习单词
3. **间隔重复**: 实现科学的复习间隔算法
4. **统计分析**: 更详细的进度分析图表
5. **自定义设置**: 允许用户自定义复习参数
