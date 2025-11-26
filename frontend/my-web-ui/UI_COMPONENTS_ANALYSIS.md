# UI 组件分析报告

## 一、现有组件清单

### 1. 页面级组件 (Page Components)

| 组件路径 | 组件名 | 用途 |
|---------|--------|------|
| `modules/word-demo/WordDemo.jsx` | WordDemo | 单词学习页面 |
| `modules/grammar-demo/GrammarDemo.jsx` | GrammarDemo | 语法学习页面 |
| `modules/article/ArticleSelection.jsx` | ArticleSelection | 文章选择页面 |
| `modules/article/ArticleChatView.jsx` | ArticleChatView | 文章阅读与聊天页面 |
| `modules/auth/components/ProfilePage.jsx` | ProfilePage | 用户个人中心页面 |
| `modules/auth/components/ResetPasswordPage.jsx` | ResetPasswordPage | 重置密码页面 |
| `components/ApiDemo.jsx` | ApiDemo | API 演示页面 |

### 2. 功能级组件 (Feature Components)

#### 2.1 文章相关
| 组件路径 | 组件名 | 用途 |
|---------|--------|------|
| `modules/article/components/ArticleCard.jsx` | ArticleCard | 文章卡片 |
| `modules/article/components/ArticleList.jsx` | ArticleList | 文章列表 |
| `modules/article/components/ArticleViewer.jsx` | ArticleViewer | 文章阅读器 |
| `modules/article/components/UploadInterface.jsx` | UploadInterface | 文章上传界面 |
| `modules/article/components/UploadProgress.jsx` | UploadProgress | 上传进度显示 |
| `modules/article/components/ChatView.jsx` | ChatView | 聊天视图 |
| `modules/article/components/SentenceContainer.jsx` | SentenceContainer | 句子容器 |
| `modules/article/components/TokenSpan.jsx` | TokenSpan | 词汇标记 |
| `modules/article/components/VocabExplanation.jsx` | VocabExplanation | 词汇解释 |
| `modules/article/components/VocabExplanationButton.jsx` | VocabExplanationButton | 词汇解释按钮 |
| `modules/article/components/VocabTooltip.jsx` | VocabTooltip | 词汇提示框 |
| `modules/article/components/SingleVocabExplanation.jsx` | SingleVocabExplanation | 单个词汇解释 |
| `modules/article/components/GrammarNotation.jsx` | GrammarNotation | 语法注释 |
| `modules/article/components/SuggestedQuestions.jsx` | SuggestedQuestions | 建议问题 |
| `modules/article/components/ToastNotice.jsx` | ToastNotice | 提示通知 |

#### 2.2 注释卡片 (Notation Cards)
| 组件路径 | 组件名 | 用途 |
|---------|--------|------|
| `modules/article/components/notation/GrammarNotationCard.jsx` | GrammarNotationCard | 语法注释卡片 |
| `modules/article/components/notation/VocabNotationCard.jsx` | VocabNotationCard | 词汇注释卡片 |
| `modules/article/components/notation/GrammarNoteBadge.jsx` | GrammarNoteBadge | 语法注释徽章 |

#### 2.3 学习相关
| 组件路径 | 组件名 | 用途 |
|---------|--------|------|
| `modules/shared/components/LearnCard.jsx` | LearnCard | 学习卡片（词汇/语法） |
| `modules/shared/components/LearnDetailPage.jsx` | LearnDetailPage | 学习详情页 |
| `modules/shared/components/ReviewCard.jsx` | ReviewCard | 复习卡片 |
| `modules/shared/components/ReviewResults.jsx` | ReviewResults | 复习结果 |

#### 2.4 认证相关
| 组件路径 | 组件名 | 用途 |
|---------|--------|------|
| `modules/auth/components/LoginModal.jsx` | LoginModal | 登录模态框 |
| `modules/auth/components/RegisterModal.jsx` | RegisterModal | 注册模态框 |
| `modules/auth/components/ForgotPasswordModal.jsx` | ForgotPasswordModal | 忘记密码模态框 |
| `modules/auth/components/LoginButton.jsx` | LoginButton | 登录按钮 |
| `modules/auth/components/UserAvatar.jsx` | UserAvatar | 用户头像 |
| `modules/auth/components/UserDebugButton.jsx` | UserDebugButton | 用户调试按钮 |

### 3. 通用基础组件 (Base Components)

| 组件路径 | 组件名 | 用途 | 状态 |
|---------|--------|------|------|
| `modules/shared/components/CardBase.jsx` | CardBase | 基础卡片组件 | ✅ 已存在 |
| `modules/shared/components/Modal.jsx` | Modal | 模态框组件 | ✅ 已存在 |
| `modules/shared/components/SearchBar.jsx` | SearchBar | 搜索栏 | ✅ 已存在 |
| `modules/shared/components/FilterBar.jsx` | FilterBar | 筛选栏 | ✅ 已存在 |
| `modules/shared/components/SingleFilterOption.jsx` | SingleFilterOption | 单个筛选选项 | ✅ 已存在 |
| `modules/shared/components/StartReviewButton.jsx` | StartReviewButton | 开始复习按钮 | ✅ 已存在 |
| `modules/shared/components/LearnPageLayout.jsx` | LearnPageLayout | 学习页面布局 | ✅ 已存在 |
| `modules/shared/components/Navigation.jsx` | Navigation | 导航栏 | ✅ 已存在 |
| `components/DataMigrationModal.jsx` | DataMigrationModal | 数据迁移模态框 | ✅ 已存在 |

### 4. 重复使用的 UI Pattern

#### 4.1 卡片样式
- **基础卡片**: `bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow`
- **可点击卡片**: `cursor-pointer transform hover:scale-105`
- **卡片容器**: `bg-white rounded-lg shadow-md p-6`

#### 4.2 按钮样式
- **主要按钮**: `bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors`
- **次要按钮**: `bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors`
- **危险按钮**: `bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors`
- **图标按钮**: `p-1.5 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200`

#### 4.3 标签样式
- **状态标签**: `px-2 py-1 rounded-full text-xs font-medium shadow-sm`
- **语言标签**: `px-2 py-1 rounded-full text-xs font-medium`
- **难度标签**: `px-2 py-1 rounded-full text-xs font-medium`

#### 4.4 输入框样式
- **基础输入**: `w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500`
- **搜索输入**: `flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`

#### 4.5 模态框样式
- **背景遮罩**: `fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50`
- **模态框容器**: `bg-white rounded-lg shadow-xl max-w-md w-full`

#### 4.6 布局样式
- **页面容器**: `bg-gray-100 p-8 min-h-[calc(100vh-64px)]`
- **内容区域**: `max-w-6xl mx-auto`
- **网格布局**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4`

## 二、重复实现分析

### 2.1 按钮重复实现

**问题**: 多个组件中重复实现相似的按钮样式

| 组件 | 按钮类型 | 样式 |
|------|---------|------|
| `StartReviewButton.jsx` | 主要按钮 | `px-6 py-3 bg-blue-600 text-white rounded-lg` |
| `ArticleCard.jsx` | 主要按钮 | `w-full py-2 px-4 rounded-md bg-blue-500 text-white` |
| `SearchBar.jsx` | 搜索按钮 | `px-6 py-2 bg-blue-500 text-white rounded-lg` |
| `LearnDetailPage.jsx` | 返回按钮 | `px-4 py-2 bg-gray-500 text-white rounded-lg` |

**建议**: 创建 `BaseButton` 组件，支持 variant (primary, secondary, danger, ghost) 和 size (sm, md, lg)

### 2.2 卡片重复实现

**问题**: `ArticleCard` 和 `LearnCard` 有相似的卡片结构，但实现不同

| 组件 | 特点 |
|------|------|
| `ArticleCard.jsx` | 自定义实现，包含语言标签、操作按钮、统计信息 |
| `LearnCard.jsx` | 使用 `CardBase`，但仍有自定义样式 |
| `CardBase.jsx` | 基础卡片，但功能有限 |

**建议**: 统一使用增强的 `BaseCard` 组件，支持 header、body、footer、actions 等插槽

### 2.3 模态框重复实现

**问题**: 多个模态框组件有相似的实现

| 组件 | 特点 |
|------|------|
| `Modal.jsx` | 基础模态框，支持 ESC 关闭 |
| `LoginModal.jsx` | 自定义实现，包含表单 |
| `RegisterModal.jsx` | 自定义实现，包含表单 |
| `ForgotPasswordModal.jsx` | 自定义实现，包含表单 |

**建议**: 所有模态框统一使用 `BaseModal`，表单内容作为 children

### 2.4 标签重复实现

**问题**: 语言标签、状态标签、难度标签等有相似样式但分散实现

| 组件 | 标签类型 |
|------|---------|
| `ArticleCard.jsx` | 语言标签、难度标签、分类标签 |
| `LearnCard.jsx` | 状态标签 |
| `FilterBar.jsx` | 筛选标签 |

**建议**: 创建 `BaseBadge` 组件，支持 variant (default, primary, success, warning, danger, info)

## 三、应该抽象成全局组件的建议

### 3.1 基础组件 (Base Components)

#### 优先级：高
1. **BaseButton** - 统一按钮组件
   - Variants: primary, secondary, danger, ghost, link
   - Sizes: sm, md, lg
   - States: default, hover, active, disabled, loading

2. **BaseCard** - 统一卡片组件
   - 支持 header、body、footer 插槽
   - 支持 hover、clickable 状态
   - 支持 shadow 级别

3. **BaseModal** - 统一模态框组件
   - 支持标题、关闭按钮
   - 支持不同尺寸 (sm, md, lg, xl)
   - 支持 ESC 关闭、背景点击关闭

4. **BaseBadge** - 统一标签组件
   - Variants: default, primary, success, warning, danger, info
   - Sizes: sm, md
   - 支持图标

5. **BaseInput** - 统一输入框组件
   - 支持 label、error、helper text
   - 支持不同尺寸
   - 支持前缀/后缀图标

#### 优先级：中
6. **BaseSelect** - 统一下拉选择组件
7. **BaseCheckbox** - 统一复选框组件
8. **BaseRadio** - 统一单选框组件
9. **BaseTextarea** - 统一文本域组件
10. **BaseSpinner** - 统一加载动画组件
11. **BaseAlert** - 统一提示组件
12. **BaseTooltip** - 统一提示框组件

### 3.2 布局组件 (Layout Components)

1. **Container** - 页面容器
2. **Grid** - 网格布局
3. **Stack** - 堆叠布局
4. **Divider** - 分割线

### 3.3 功能组件 (Feature Components)

1. **ConfirmDialog** - 确认对话框
2. **LoadingOverlay** - 加载遮罩
3. **EmptyState** - 空状态
4. **ErrorBoundary** - 错误边界

## 四、UI 风格一致性分析

### 4.1 颜色使用

#### 主要颜色
- **Primary (蓝色)**: `bg-blue-500`, `bg-blue-600`, `text-blue-600`
- **Success (绿色)**: `bg-green-500`, `text-green-600`
- **Warning (黄色)**: `bg-yellow-100`, `text-yellow-800`
- **Danger (红色)**: `bg-red-500`, `bg-red-100`, `text-red-600`, `text-red-800`
- **Gray (灰色)**: `bg-gray-100`, `bg-gray-200`, `text-gray-500`, `text-gray-600`, `text-gray-700`, `text-gray-800`, `text-gray-900`

#### 不一致之处
1. **蓝色变体不统一**:
   - `bg-blue-500` (SearchBar, ArticleCard)
   - `bg-blue-600` (StartReviewButton, FilterBar)
   - `text-blue-600` (LearnCard, ArticleCard)

2. **灰色变体过多**:
   - 使用了 gray-100 到 gray-900 的多个变体，缺乏统一规范

3. **状态颜色不统一**:
   - 成功状态: `green-500`, `green-600`
   - 警告状态: `yellow-100`, `yellow-800`
   - 错误状态: `red-500`, `red-600`, `red-800`

### 4.2 间距使用

#### 常用间距
- **Padding**: `p-2`, `p-4`, `p-6`, `px-2`, `px-3`, `px-4`, `px-6`, `py-2`, `py-3`, `py-4`
- **Margin**: `mb-2`, `mb-4`, `mb-6`, `mt-2`, `mt-4`, `gap-2`, `gap-4`, `space-x-2`, `space-x-3`, `space-x-4`, `space-y-1`, `space-y-2`, `space-y-4`

#### 不一致之处
1. **卡片内边距不统一**:
   - `p-4` (LearnCard, CardBase)
   - `p-6` (ArticleCard, Modal)

2. **按钮内边距不统一**:
   - `px-4 py-2` (ArticleCard)
   - `px-6 py-2` (SearchBar)
   - `px-6 py-3` (StartReviewButton)

### 4.3 圆角使用

#### 常用圆角
- **小圆角**: `rounded-md` (输入框、按钮)
- **中圆角**: `rounded-lg` (卡片、模态框)
- **大圆角**: `rounded-full` (标签、圆形按钮)

#### 不一致之处
1. **按钮圆角不统一**:
   - `rounded-md` (ArticleCard)
   - `rounded-lg` (SearchBar, StartReviewButton)

### 4.4 阴影使用

#### 常用阴影
- **基础阴影**: `shadow-md` (卡片)
- **悬停阴影**: `shadow-lg` (卡片悬停)
- **模态框阴影**: `shadow-xl` (模态框)

#### 不一致之处
1. **卡片阴影基本一致**，但有些组件使用 `shadow-sm`

### 4.5 字体大小

#### 常用字体大小
- **标题**: `text-xl`, `text-2xl`, `text-3xl`
- **正文**: `text-sm`, `text-base`
- **小字**: `text-xs`

#### 不一致之处
1. **标题大小不统一**:
   - `text-xl` (ArticleCard, Modal)
   - `text-2xl` (LearnDetailPage, LoginModal)
   - `text-3xl` (LearnPageLayout)

## 五、建议的组件结构树

```
src/
├── components/
│   ├── base/                    # 基础组件（原子级）
│   │   ├── Button/
│   │   │   ├── BaseButton.jsx
│   │   │   ├── Button.stories.jsx
│   │   │   └── index.js
│   │   ├── Card/
│   │   │   ├── BaseCard.jsx
│   │   │   └── index.js
│   │   ├── Modal/
│   │   │   ├── BaseModal.jsx
│   │   │   └── index.js
│   │   ├── Badge/
│   │   │   ├── BaseBadge.jsx
│   │   │   └── index.js
│   │   ├── Input/
│   │   │   ├── BaseInput.jsx
│   │   │   └── index.js
│   │   ├── Select/
│   │   │   ├── BaseSelect.jsx
│   │   │   └── index.js
│   │   ├── Spinner/
│   │   │   ├── BaseSpinner.jsx
│   │   │   └── index.js
│   │   └── Alert/
│   │       ├── BaseAlert.jsx
│   │       └── index.js
│   │
│   ├── ui/                      # UI 组件（分子级）
│   │   ├── SearchBar/
│   │   │   ├── SearchBar.jsx
│   │   │   └── index.js
│   │   ├── FilterBar/
│   │   │   ├── FilterBar.jsx
│   │   │   └── index.js
│   │   ├── ConfirmDialog/
│   │   │   ├── ConfirmDialog.jsx
│   │   │   └── index.js
│   │   ├── LoadingOverlay/
│   │   │   ├── LoadingOverlay.jsx
│   │   │   └── index.js
│   │   └── EmptyState/
│   │       ├── EmptyState.jsx
│   │       └── index.js
│   │
│   ├── layout/                  # 布局组件
│   │   ├── Container/
│   │   │   ├── Container.jsx
│   │   │   └── index.js
│   │   ├── Grid/
│   │   │   ├── Grid.jsx
│   │   │   └── index.js
│   │   ├── Stack/
│   │   │   ├── Stack.jsx
│   │   │   └── index.js
│   │   └── PageLayout/
│   │       ├── PageLayout.jsx
│   │       └── index.js
│   │
│   ├── features/                # 功能组件（业务相关）
│   │   ├── article/
│   │   │   ├── ArticleCard/
│   │   │   ├── ArticleList/
│   │   │   ├── ArticleViewer/
│   │   │   └── UploadInterface/
│   │   ├── learning/
│   │   │   ├── LearnCard/
│   │   │   ├── LearnDetailPage/
│   │   │   └── ReviewCard/
│   │   ├── notation/
│   │   │   ├── GrammarNotationCard/
│   │   │   └── VocabNotationCard/
│   │   └── auth/
│   │       ├── LoginModal/
│   │       ├── RegisterModal/
│   │       └── UserAvatar/
│   │
│   └── pages/                   # 页面组件
│       ├── WordDemo/
│       ├── GrammarDemo/
│       ├── ArticleSelection/
│       └── ArticleChatView/
│
├── design-tokens/               # 设计令牌
│   ├── colors.js
│   ├── spacing.js
│   ├── typography.js
│   ├── shadows.js
│   ├── radius.js
│   └── index.js
│
└── styles/                      # 全局样式
    ├── base.css
    ├── utilities.css
    └── components.css
```

## 六、现有组件清单

### 6.1 已存在的组件

#### 基础组件
- ✅ CardBase
- ✅ Modal
- ✅ SearchBar
- ✅ FilterBar
- ✅ SingleFilterOption
- ✅ StartReviewButton
- ✅ Navigation

#### 功能组件
- ✅ ArticleCard
- ✅ ArticleList
- ✅ ArticleViewer
- ✅ UploadInterface
- ✅ UploadProgress
- ✅ ChatView
- ✅ LearnCard
- ✅ LearnDetailPage
- ✅ ReviewCard
- ✅ ReviewResults
- ✅ GrammarNotationCard
- ✅ VocabNotationCard
- ✅ LoginModal
- ✅ RegisterModal
- ✅ ForgotPasswordModal
- ✅ UserAvatar
- ✅ DataMigrationModal

### 6.2 应该新增的通用组件清单

#### 优先级：高
1. **BaseButton** - 统一按钮组件
2. **BaseCard** - 增强的卡片组件（替代 CardBase）
3. **BaseModal** - 增强的模态框组件（替代 Modal）
4. **BaseBadge** - 统一标签组件
5. **BaseInput** - 统一输入框组件
6. **BaseSpinner** - 统一加载动画组件
7. **ConfirmDialog** - 确认对话框组件
8. **LoadingOverlay** - 加载遮罩组件

#### 优先级：中
9. **BaseSelect** - 统一下拉选择组件
10. **BaseTextarea** - 统一文本域组件
11. **BaseAlert** - 统一提示组件
12. **BaseTooltip** - 统一提示框组件
13. **EmptyState** - 空状态组件
14. **ErrorBoundary** - 错误边界组件

#### 优先级：低
15. **BaseCheckbox** - 统一复选框组件
16. **BaseRadio** - 统一单选框组件
17. **Container** - 页面容器组件
18. **Grid** - 网格布局组件
19. **Stack** - 堆叠布局组件
20. **Divider** - 分割线组件

## 七、Design Token 表

```javascript
// design-tokens/index.js
export const tokens = {
  // 颜色
  colors: {
    // 主色
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',  // 主要使用
      600: '#2563eb',  // hover 状态
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    
    // 成功色
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',  // 主要使用
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    
    // 警告色
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    
    // 危险色
    danger: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',  // 主要使用
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    
    // 灰色
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',  // 背景色
      200: '#e5e7eb',  // 边框色
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',  // 次要文本
      600: '#4b5563',  // 正文
      700: '#374151',  // 标题
      800: '#1f2937',
      900: '#111827',  // 主要文本
    },
    
    // 语义化颜色
    semantic: {
      text: {
        primary: '#111827',      // gray-900
        secondary: '#6b7280',    // gray-500
        tertiary: '#9ca3af',     // gray-400
        disabled: '#d1d5db',     // gray-300
      },
      bg: {
        primary: '#ffffff',
        secondary: '#f9fafb',    // gray-50
        tertiary: '#f3f4f6',     // gray-100
      },
      border: {
        default: '#e5e7eb',      // gray-200
        hover: '#d1d5db',        // gray-300
        focus: '#3b82f6',        // primary-500
      },
    },
  },
  
  // 间距
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
  },
  
  // 圆角
  radius: {
    none: '0',
    sm: '0.25rem',   // 4px
    md: '0.375rem',  // 6px
    lg: '0.5rem',    // 8px
    xl: '0.75rem',   // 12px
    '2xl': '1rem',   // 16px
    full: '9999px',
  },
  
  // 字体大小
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  
  // 字体粗细
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  
  // 行高
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
  
  // 阴影
  shadow: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  // 过渡
  transition: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
  },
  
  // Z-index
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
  
  // 断点
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
}
```

## 八、散落在代码里的样式（需要提取）

### 8.1 内联样式
- `GrammarNotationCard.jsx` - 使用大量内联样式（应改为 className）
- `VocabNotationCard.jsx` - 使用内联样式定位

### 8.2 重复的颜色值
- `bg-blue-500` / `bg-blue-600` - 应统一为 primary 色
- `bg-gray-100` / `bg-gray-200` - 应统一为 semantic.bg
- `text-gray-500` / `text-gray-600` - 应统一为 semantic.text

### 8.3 重复的间距值
- `p-4` / `p-6` - 应统一为 spacing.md / spacing.lg
- `px-2` / `px-3` / `px-4` - 应统一为 spacing 系统
- `gap-2` / `gap-4` - 应统一为 spacing 系统

### 8.4 重复的圆角值
- `rounded-md` / `rounded-lg` - 应统一为 radius.md / radius.lg
- `rounded-full` - 应统一为 radius.full

## 九、总结与建议

### 9.1 主要问题
1. **组件重复实现**: 按钮、卡片、模态框等有多个相似实现
2. **样式不统一**: 颜色、间距、圆角等缺乏统一规范
3. **缺乏基础组件**: 没有统一的 BaseButton、BaseCard 等
4. **内联样式**: 部分组件使用内联样式，难以维护
5. **缺乏 Design Token**: 没有统一的设计令牌系统

### 9.2 改进建议
1. **立即行动**:
   - 创建 Design Token 系统
   - 实现 BaseButton、BaseCard、BaseModal 等基础组件
   - 统一颜色、间距、圆角的使用

2. **短期计划**:
   - 重构现有组件使用基础组件
   - 移除内联样式
   - 建立组件文档

3. **长期计划**:
   - 建立组件库
   - 添加 Storybook
   - 建立设计系统文档

### 9.3 迁移路径
1. 先创建 Design Token
2. 实现基础组件（BaseButton、BaseCard 等）
3. 逐步重构现有组件使用基础组件
4. 移除重复实现
5. 统一样式规范

