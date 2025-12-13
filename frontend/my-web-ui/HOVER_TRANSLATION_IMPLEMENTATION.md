# Hover 词典翻译功能实现总结

## 实现概述

已成功实现轻量级 hover 词典翻译功能，作为 select → ask AI 之前的轻量翻译层。该功能不调用 LLM，只提供简单的单词翻译。

## 已实现的功能

### 1. 系统语言获取 ✅

- **文件**: `frontend/my-web-ui/src/services/translationService.js`
- **函数**: `getSystemLanguage()`
- **功能**: 
  - 使用 `navigator.language` 获取用户系统语言
  - Normalize 成 `en` / `zh` / `de` / `ja`
  - 暂时只支持 `en` / `zh`，其他 fallback 到 `en`

### 2. Hover Token 翻译逻辑 ✅

- **查询顺序**:
  1. 本地 vocabulary 表（通过 `vocabListGetter` 可选）
  2. 内存缓存（同一会话中）
  3. localStorage 缓存（持久化，30天有效期）
  4. 词典/翻译 API（MyMemory，可替换）

- **缓存策略**:
  - 内存缓存：避免同一会话中重复查询
  - localStorage缓存：持久化，自动过期清理
  - 缓存key格式：`quick_translation_v1_{sourceLang}_{targetLang}_{normalizedWord}`

### 3. UI 表现 ✅

- **组件**: `frontend/my-web-ui/src/components/QuickTranslationTooltip.jsx`
- **特性**:
  - 使用 tooltip/popover 显示
  - 内容只包含：单词 + 简短翻译
  - 不包含例句、不调用 AI
  - 自动定位，避免超出视口

### 4. API 封装 ✅

- **主函数**: `getQuickTranslation(word, sourceLang, targetLang, options)`
- **特性**:
  - 可替换 API 实现（通过 `apiProvider` 选项）
  - 默认使用 MyMemory API
  - 支持自定义 API 提供者

## 文件结构

```
frontend/my-web-ui/
├── src/
│   ├── services/
│   │   ├── translationService.js          # 翻译服务核心逻辑
│   │   └── TRANSLATION_SERVICE_README.md  # 详细使用文档
│   ├── components/
│   │   └── QuickTranslationTooltip.jsx    # 翻译tooltip组件
│   └── modules/
│       └── article/
│           └── components/
│               └── TokenSpan.jsx          # 已集成hover翻译功能
└── HOVER_TRANSLATION_IMPLEMENTATION.md    # 本文档
```

## 关键代码示例

### 1. 基本使用

```javascript
import { getQuickTranslation } from './services/translationService'

// 基本翻译查询
const translation = await getQuickTranslation('Haus', 'de', 'en')
console.log(translation) // 'house'
```

### 2. 使用本地vocabulary表

```javascript
const vocabListGetter = () => {
  // 返回词汇列表数组
  return [
    { vocab_body: 'Haus', translation: '房子', language: 'de' },
    // ...
  ]
}

const translation = await getQuickTranslation('Haus', 'de', 'zh', {
  vocabListGetter
})
```

### 3. 自定义API

```javascript
const customAPI = async (word, sourceLang, targetLang) => {
  const response = await fetch(`your-api-endpoint?word=${word}`)
  const data = await response.json()
  return data.translation
}

const translation = await getQuickTranslation('Haus', 'de', 'en', {
  apiProvider: customAPI
})
```

### 4. Hover事件处理（已在TokenSpan中实现）

```javascript
// 在TokenSpan组件中
onMouseEnter={() => {
  // 延迟500ms触发翻译查询
  hoverTranslationTimerRef.current = setTimeout(() => {
    queryQuickTranslation(displayText)
  }, 500)
}}

onMouseLeave={() => {
  // 清除翻译状态
  clearTranslation()
}}
```

## 本地缓存Key设计

### 格式

```
quick_translation_{version}_{sourceLang}_{targetLang}_{normalizedWord}
```

### 示例

- `quick_translation_v1_de_en_haus`
- `quick_translation_v1_zh_en_你好`
- `quick_translation_v1_en_zh_hello`

### 存储结构

```json
{
  "translation": "house",
  "cachedAt": 1234567890123
}
```

## 集成说明

### TokenSpan组件集成

`TokenSpan` 组件已自动集成hover翻译功能：

1. **自动触发**：当用户hover在单词token上时，延迟500ms后自动触发翻译查询
2. **智能显示**：只在没有vocab notation时显示（避免重复显示）
3. **语言检测**：自动使用系统语言或全局选择的语言作为目标语言
4. **源语言**：目前默认使用'de'（德语），后续可以通过props传递articleLanguage

### 使用条件

- 只在 `isTextToken` 为 true 时触发
- 只在 `hoverAllowed` 为 true 时触发
- 只在没有 `vocabVisual`（vocab notation）时显示
- 单词长度必须 > 0

## 配置选项

### 延迟时间

在 `TokenSpan.jsx` 中，hover延迟时间设置为500ms：

```javascript
hoverTranslationTimerRef.current = setTimeout(() => {
  queryQuickTranslation(displayText)
}, 500) // 可调整延迟时间
```

### 缓存有效期

在 `translationService.js` 中，缓存有效期设置为30天：

```javascript
const CACHE_EXPIRY_DAYS = 30 // 可调整
```

## 性能优化

1. **内存缓存**：同一会话中的查询结果缓存在内存中
2. **延迟查询**：hover延迟500ms触发，避免鼠标快速移动时频繁查询
3. **查询取消**：当鼠标离开时，取消正在进行的查询
4. **自动清理**：过期缓存自动清理

## 后续优化建议

1. **源语言传递**：从 `ArticleViewer` 传递 `articleLanguage` 到 `TokenSpan`，确保源语言正确
2. **本地vocabulary查询**：集成 `useVocabList` hook，实现本地vocabulary表查询
3. **API替换**：在生产环境中替换MyMemory为更稳定的付费API（如Google Translate、DeepL）
4. **错误处理**：增强错误处理和重试机制
5. **性能监控**：添加性能监控，跟踪查询时间和缓存命中率

## 测试建议

1. **基本功能测试**：
   - Hover在单词上，检查是否显示翻译
   - 检查翻译结果是否正确
   - 检查tooltip位置是否正确

2. **缓存测试**：
   - 第一次hover应该调用API
   - 第二次hover应该使用缓存
   - 清除缓存后应该重新调用API

3. **性能测试**：
   - 快速移动鼠标，检查是否避免频繁查询
   - 检查内存使用情况
   - 检查localStorage使用情况

4. **边界情况测试**：
   - 空单词
   - 特殊字符
   - 网络错误
   - API超时

## 已知限制

1. **API限制**：MyMemory免费API有请求频率限制
2. **语言支持**：系统语言暂时只支持en/zh
3. **源语言**：目前默认使用'de'，需要从ArticleViewer传递
4. **本地vocabulary**：暂未集成本地vocabulary表查询（可通过vocabListGetter实现）

## 相关文档

- [翻译服务详细文档](./src/services/TRANSLATION_SERVICE_README.md)
- [TokenSpan组件文档](./src/modules/article/components/TokenSpan.jsx)

