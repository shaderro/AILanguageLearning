# Word Demo 和 Grammar Demo 页面重构方案

**创建日期**: 2025年9月15日  
**目标**: 统一Word Demo和Grammar Demo页面的视觉风格、组件和布局

##  当前组件分析

### Word Demo页面组件：
- **WordCard** - 词汇卡片
- **WordCardDetail** - 词汇详情页面  
- **ReviewCard** - 复习卡片
- **ReviewResults** - 复习结果
- **StartReviewButton** - 开始复习按钮（已在shared）
- **搜索栏** - 内联在WordDemo中

### Grammar Demo页面组件：
- **GrammarCard** - 语法卡片
- **GrammarCardDetail** - 语法详情页面
- **StartReviewButton** - 开始复习按钮（已在shared）
- **FilterBar** - 筛选栏（已在shared）
- **Modal** - 模态框（已在shared）

##  重构方案

### 目标架构：
`
shared/components/
 LearnPageLayout.jsx          # 统一页面布局
 LearnCard.jsx               # 通用学习卡片
 LearnDetailPage.jsx         # 通用详情页面
 SearchBar.jsx               # 搜索栏组件
 ReviewCard.jsx              # 通用复习卡片
 ReviewResults.jsx           # 通用复习结果
 StartReviewButton.jsx       # 开始复习按钮（已存在）
 FilterBar.jsx               # 筛选栏（已存在）
 Modal.jsx                   # 模态框（已存在）
`

##  完整实施步骤

### 第一步：创建通用组件

**指令1：创建LearnPageLayout统一布局组件**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 LearnPageLayout.jsx 文件，包含：
- 统一的页面头部（标题 + 开始复习按钮）
- 可选的筛选栏
- 可选的搜索栏
- 统一的卡片网格布局
- 支持自定义背景色和显示选项
`

**指令2：创建SearchBar搜索栏组件**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 SearchBar.jsx 文件，包含：
- 输入框和搜索按钮
- 实时搜索功能
- 可自定义占位符文本
- 统一的样式设计
`

**指令3：创建LearnCard通用卡片组件**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 LearnCard.jsx 文件，作为单词或语法知识点的预览版本，用户可点击进去查看详情。包含：
- 支持词汇和语法两种数据类型
- 统一的卡片样式和布局
- 点击事件处理
- 加载和错误状态处理
- 可自定义内容渲染
`

**指令4：创建LearnDetailPage通用详情页面**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 LearnDetailPage.jsx 文件，包含：
- 统一的详情页面布局
- 支持词汇和语法详情显示
- 返回按钮
- 加载和错误状态
- 可自定义内容渲染
`

**指令5：创建ReviewCard通用复习卡片**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 ReviewCard.jsx 文件，包含：
- 统一的复习界面
- 支持词汇和语法复习
- 进度显示
- 答案选择功能
- 下一题/完成逻辑
`

**指令6：创建ReviewResults通用复习结果**
`
在 frontend/my-web-ui/src/modules/shared/components/ 目录下创建 ReviewResults.jsx 文件，包含：
- 统一的复习结果展示
- 统计信息显示
- 返回主页面功能
- 可自定义结果渲染
`

### 第二步：重构Word Demo页面

**指令7：重构WordDemo.jsx**
`
修改 frontend/my-web-ui/src/modules/word-demo/WordDemo.jsx：
- 使用LearnPageLayout作为主布局
- 使用LearnCard替代WordCard
- 使用LearnDetailPage替代WordCardDetail
- 使用ReviewCard和ReviewResults
- 简化页面逻辑，专注于数据管理
`

### 第三步：重构Grammar Demo页面

**指令8：重构GrammarDemo.jsx**
`
修改 frontend/my-web-ui/src/modules/grammar-demo/GrammarDemo.jsx：
- 使用LearnPageLayout作为主布局
- 使用LearnCard替代GrammarCard
- 使用LearnDetailPage替代GrammarCardDetail
- 使用ReviewCard和ReviewResults
- 简化页面逻辑，专注于数据管理
`

### 第四步：清理旧组件

**指令9：删除旧的专用组件**
`
删除以下文件：
- frontend/my-web-ui/src/modules/word-demo/components/WordCard.jsx
- frontend/my-web-ui/src/modules/word-demo/components/WordCardDetail.jsx
- frontend/my-web-ui/src/modules/word-demo/components/ReviewCard.jsx
- frontend/my-web-ui/src/modules/word-demo/components/ReviewResults.jsx
- frontend/my-web-ui/src/modules/grammar-demo/components/GrammarCard.jsx
- frontend/my-web-ui/src/modules/grammar-demo/components/GrammarCardDetail.jsx
`

### 第五步：测试和优化

**指令10：测试功能完整性**
`
- 测试Word Demo页面的所有功能
- 测试Grammar Demo页面的所有功能
- 确保视觉风格统一
- 确保交互逻辑正确
- 修复任何发现的问题
`

##  设计原则

1. **统一性**：两个页面使用完全相同的布局和组件
2. **可配置性**：组件支持不同的数据类型和显示选项
3. **可维护性**：通用组件集中管理，减少重复代码
4. **扩展性**：未来添加新的学习模块时可以直接复用

##  给Cursor的具体指令模板

你可以按以下格式给Cursor指令：

`
请创建 [组件名称] 组件，位于 [路径]，包含以下功能：
1. [功能1]
2. [功能2]
3. [功能3]
...
要求：
- 使用统一的视觉风格
- 支持 [数据类型]
- 包含 [特定功能]
- 遵循现有的代码规范
`

##  预期效果

重构完成后，Word Demo和Grammar Demo页面将具有：
- 完全一致的视觉风格
- 统一的交互体验
- 可复用的组件架构
- 更易维护的代码结构
- 更好的扩展性

##  注意事项

1. 在重构过程中要保持现有功能不变
2. 每个步骤完成后都要测试功能完整性
3. 确保所有导入路径正确更新
4. 保持与现有API的兼容性
5. 遵循现有的代码风格和命名规范

---

**最后更新**: 2025年9月15日  
**状态**: 待实施
