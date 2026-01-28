# 翻译功能接入情况总结

## 📋 功能概述

系统实现了两种翻译功能：
1. **单词翻译**（Hover 词典翻译）- 已禁用
2. **整句翻译**（自动翻译）- 已实现并启用

## 🔧 当前实现状态

### 1. 整句翻译（自动翻译）

**位置**: `frontend/my-web-ui/src/modules/article/components/SentenceContainer.jsx`

**功能**:
- 当用户开启"自动翻译"开关时，鼠标悬停在句子上会自动显示整句翻译
- 翻译目标语言根据用户 UI 语言设置自动选择

**目标语言选择逻辑**（已修复）:
```javascript
// 优先使用 UI 语言设置
if (uiLanguage === 'en') {
  // UI 语言为英语时，翻译成英语（除非源语言也是英语，则翻译成中文）
  return sourceLang === 'en' ? 'zh' : 'en'
}
// UI 语言为中文时，使用学习语言或系统语言
```

**翻译流程**:
1. 用户开启"自动翻译"开关
2. 鼠标悬停在句子上
3. 延迟 300ms 后触发翻译查询
4. 调用 `getQuickTranslation()` 进行翻译
5. 显示翻译结果在 tooltip 中

**翻译服务**: `frontend/my-web-ui/src/services/translationService.js`
- 支持多级查询：内存缓存 → localStorage缓存 → 翻译API
- 支持多个翻译API自动切换（MyMemory、LibreTranslate等）

### 2. 单词翻译（Hover 词典翻译）

**状态**: ❌ 已禁用

**原因**: 用户要求去掉 hover token 时自动翻译单词的功能，保留 hover 句子翻译整句的功能

**位置**: `frontend/my-web-ui/src/modules/article/components/TokenSpan.jsx`
- 相关代码已注释，但保留以备将来使用

## 🌐 语言设置系统

### UI 语言设置（UiLanguageContext）

**位置**: `frontend/my-web-ui/src/contexts/UiLanguageContext.jsx`

**功能**:
- 管理界面显示语言（'en' | 'zh'）
- 存储在 localStorage 中（key: `ui_language`）
- 影响所有 UI 文案的显示语言

**使用场景**:
- 控制界面文案的显示语言
- **现在也用于控制自动翻译的目标语言**（已修复）

### 学习语言设置（LanguageContext）

**位置**: `frontend/my-web-ui/src/contexts/LanguageContext.jsx`

**功能**:
- 管理用户正在学习的语言（'中文' | '英文' | '德文'）
- 用于筛选和显示特定语言的词汇/语法

**使用场景**:
- 词汇/语法列表筛选
- 学习进度统计

## 🔄 翻译服务架构

### 核心服务文件

**`translationService.js`**:
- `getSystemLanguage()`: 获取系统语言（navigator.language）
- `getQuickTranslation()`: 主翻译函数
  - 支持单词和句子翻译
  - 多级缓存机制
  - 支持多个翻译API

### 翻译查询顺序

**对于句子翻译**:
1. 内存缓存（同一会话）
2. localStorage缓存（持久化，30天有效期）
3. 外部翻译API（MyMemory、LibreTranslate等）

**对于单词翻译**（已禁用，但逻辑保留）:
1. 本地vocabulary表
2. 内存缓存
3. localStorage缓存
4. 词典API（Free Dictionary API、Wiktionary）
5. 翻译API

## ✅ 已修复的问题

### 问题：UI 语言设置不影响自动翻译目标语言

**修复前**:
- 自动翻译的目标语言基于学习语言（LanguageContext）或系统语言
- 即使用户设置 UI 语言为英语，翻译目标语言可能仍然是中文

**修复后**:
- 自动翻译的目标语言优先使用 UI 语言设置
- 当 UI 语言为英语时，自动翻译的目标语言也是英语（除非源语言也是英语）
- 当 UI 语言为中文时，使用原来的逻辑（基于学习语言或系统语言）

**修改文件**: `frontend/my-web-ui/src/modules/article/components/SentenceContainer.jsx`

## 📝 使用示例

### 用户设置 UI 语言为英语

1. 用户在设置中选择 UI 语言为"English"
2. 开启"自动翻译"开关
3. 鼠标悬停在德语句子上
4. **结果**: 句子被翻译成英语显示

### 用户设置 UI 语言为中文

1. 用户在设置中选择 UI 语言为"中文"
2. 开启"自动翻译"开关
3. 鼠标悬停在德语句子上
4. **结果**: 句子被翻译成中文显示（或根据学习语言设置）

## 🔮 未来改进建议

1. **单词翻译功能**: 如果将来需要恢复单词翻译，可以重新启用相关代码
2. **更多语言支持**: 目前主要支持 en/zh，可以扩展到更多语言
3. **翻译质量优化**: 可以集成更多翻译API，提高翻译质量
4. **缓存策略优化**: 可以根据翻译质量调整缓存策略
