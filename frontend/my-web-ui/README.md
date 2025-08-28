# React + FastAPI 学习应用

**开发日期**: 2025.8.26  
**技术栈**: React 18 + Vite + TailwindCSS + FastAPI

一个功能丰富的学习应用，包含单词学习、语法练习和文章阅读功能。

## 🚀 快速开始

### 前端启动
```bash
npm install
npm run dev
```

### 后端启动
```bash
cd backend
source venv/bin/activate
python main.py
```

### 一键启动
```bash
./start-demo.sh
```

## 📁 项目结构

```
my-web-ui/
├── src/
│   ├── modules/                    # 模块化目录
│   │   ├── shared/                 # 共享组件和配置
│   │   │   ├── components/         # 共享组件
│   │   │   │   ├── CardBase.jsx    # 卡片基础组件
│   │   │   │   ├── Modal.jsx       # 模态框组件
│   │   │   │   ├── Navigation.jsx  # 导航栏组件
│   │   │   │   ├── ToastNotice.jsx # 通知组件
│   │   │   │   ├── FilterBar.jsx   # 筛选栏组件
│   │   │   │   ├── ArticleCard.jsx # 文章卡片组件
│   │   │   │   └── StartReviewButton.jsx # 开始复习按钮
│   │   │   └── config/
│   │   │       └── navigation.js   # 导航配置
│   │   ├── word-demo/              # 单词学习模块
│   │   │   ├── WordDemo.jsx        # 单词学习主页面
│   │   │   └── components/
│   │   │       ├── WordCard.jsx    # 单词卡片组件
│   │   │       ├── WordCardDetail.jsx # 单词详情组件
│   │   │       ├── ReviewCard.jsx  # 复习卡片组件
│   │   │       └── ReviewResults.jsx # 复习结果组件
│   │   ├── grammar-demo/           # 语法学习模块
│   │   │   ├── GrammarDemo.jsx     # 语法学习主页面
│   │   │   └── components/
│   │   │       ├── GrammarCard.jsx # 语法卡片组件
│   │   │       └── GrammarCardDetail.jsx # 语法详情组件
│   │   └── article/                # 文章阅读模块
│   │       ├── ArticleSelection.jsx # 文章选择页面
│   │       ├── ArticleChatView.jsx # 文章聊天视图
│   │       └── components/
│   │           ├── ArticleViewer.jsx # 文章阅读器
│   │           ├── ChatView.jsx     # 聊天界面
│   │           ├── VocabExplanation.jsx # 词汇解释组件
│   │           ├── SuggestedQuestions.jsx # 建议问题组件
│   │           ├── UploadInterface.jsx # 上传界面
│   │           ├── UploadProgress.jsx # 上传进度
│   │           └── ArticleList.jsx  # 文章列表
│   ├── App.jsx                     # 主应用组件
│   ├── main.jsx                    # 应用入口
│   └── index.css                   # 全局样式
├── backend/                        # FastAPI 后端
│   ├── main.py                     # 后端主程序
│   └── requirements.txt            # Python 依赖
└── 功能文档/                       # 详细功能说明
    ├── REVIEW_FEATURE.md           # 复习功能
    ├── TOAST_NOTICE_FEATURE.md     # 通知功能
    ├── VOCAB_EXPLANATION_FEATURE.md # 词汇解释
    ├── SUGGESTED_QUESTIONS_FEATURE.md # 建议问题
    ├── IMPORTANT_WORDS_FEATURE.md  # 重点词汇
    ├── UPLOAD_NEW_BUTTON_FEATURE.md # 上传按钮
    ├── UPLOAD_INTERFACE_FEATURE.md # 上传界面
    └── UPLOAD_PROGRESS_FEATURE.md  # 上传进度
```

## 🎯 核心功能

### 1. 单词学习模块 (`word-demo/`)
- **WordCard**: 单词卡片展示，支持点击查看详情
- **ReviewCard**: 交互式复习卡片，支持"模糊/认识/不认识"选择
- **ReviewResults**: 复习结果统计和回顾
- **API集成**: 从 `/api/word` 获取单词数据

### 2. 语法学习模块 (`grammar-demo/`)
- **GrammarCard**: 语法规则卡片展示
- **GrammarCardDetail**: 语法规则详细说明
- **API集成**: 从 `/api/grammar` 获取语法数据
- **支持规则**: present-perfect, past-continuous, future-simple, conditional

### 3. 文章阅读模块 (`article/`)
- **ArticleViewer**: 文章阅读器，支持token选择和重点词汇高亮
- **ChatView**: AI聊天助手，支持文章相关问答
- **VocabExplanation**: 词汇解释弹窗，hover显示
- **SuggestedQuestions**: 智能建议问题
- **UploadInterface**: 文件上传界面，支持URL/文件/拖拽
- **UploadProgress**: 上传进度显示，四步骤处理

### 4. 共享组件 (`shared/`)
- **CardBase**: 卡片基础组件，统一loading/error处理
- **Modal**: 可复用模态框组件
- **Navigation**: 导航栏组件
- **ToastNotice**: 通知组件，支持自动消失
- **FilterBar**: 筛选栏组件

## 🔧 技术特性

### 前端特性
- **模块化设计**: 清晰的模块分离和组件复用
- **状态管理**: React Hooks 状态管理
- **响应式设计**: TailwindCSS 响应式布局
- **动画效果**: CSS transitions 和 animations
- **组件通信**: Props 和回调函数

### 后端特性
- **FastAPI**: 现代化Python Web框架
- **CORS支持**: 跨域请求处理
- **数据模拟**: 内置单词和语法数据库
- **RESTful API**: 标准REST API设计

### 开发体验
- **热重载**: Vite 开发服务器
- **ESLint**: 代码质量检查
- **PostCSS**: CSS 后处理
- **虚拟环境**: Python 依赖隔离

## 🎨 UI/UX 设计

### 设计原则
- **一致性**: 统一的视觉风格和交互模式
- **可访问性**: 清晰的视觉层次和交互反馈
- **响应式**: 适配不同屏幕尺寸
- **动画**: 流畅的过渡和加载动画

### 交互特性
- **悬停效果**: 卡片悬停和按钮反馈
- **加载状态**: 统一的loading和error处理
- **进度反馈**: 上传进度和步骤指示
- **成功动效**: 完成操作的视觉反馈

## 📊 API 接口

### 单词接口
```
GET /api/word?text={word}
Response: { word, definition, example }
```

### 语法接口
```
GET /api/grammar?rule={rule}
Response: { rule, structure, usage, example, additionalExamples }
```

## 🚀 部署说明

### 开发环境
```bash
# 前端
npm run dev          # 开发服务器
npm run build        # 生产构建

# 后端
python main.py       # 开发服务器
```

### 生产环境
```bash
# 前端构建
npm run build
# 部署 dist/ 目录

# 后端部署
pip install -r requirements.txt
python main.py
```

## 🔮 扩展计划

### 功能扩展
- [ ] 用户认证系统
- [ ] 学习进度跟踪
- [ ] 个性化推荐
- [ ] 离线支持
- [ ] 多语言支持

### 技术扩展
- [ ] 数据库集成
- [ ] 文件上传服务
- [ ] 实时聊天
- [ ] 推送通知
- [ ] PWA支持

## 📝 开发规范

### 代码组织
- **模块化**: 按功能模块组织代码
- **组件化**: 可复用的组件设计
- **配置化**: 统一的配置管理
- **文档化**: 详细的功能文档

### 命名规范
- **文件命名**: PascalCase (组件), camelCase (工具)
- **组件命名**: PascalCase
- **函数命名**: camelCase
- **常量命名**: UPPER_SNAKE_CASE

### Git规范
- **分支管理**: feature/功能名
- **提交信息**: feat: 新功能, fix: 修复, docs: 文档
- **代码审查**: 提交前代码审查

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 项目讨论区

---

**最后更新**: 2025.8.26  
**版本**: 1.0.0  
**状态**: 开发中
