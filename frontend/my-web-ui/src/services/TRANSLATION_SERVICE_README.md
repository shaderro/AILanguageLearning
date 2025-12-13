# 轻量级翻译服务使用文档

## 概述

`translationService.js` 提供了一个轻量级的 hover 词典翻译功能，作为 select → ask AI 之前的轻量翻译层。该服务不调用 LLM，只提供简单的单词翻译。

## 功能特性

1. **系统语言获取**：自动检测用户系统语言（en/zh/de/ja），暂时只支持 en/zh
2. **多级查询**：本地vocabulary表 → 内存缓存 → localStorage缓存 → 外部API
3. **智能缓存**：自动缓存翻译结果，减少API调用
4. **可替换API**：支持替换不同的翻译API实现

## 核心函数

### `getSystemLanguage()`

获取并normalize用户系统语言。

```javascript
import { getSystemLanguage } from './services/translationService'

const systemLang = getSystemLanguage() // 'en' | 'zh'
```

### `getQuickTranslation(word, sourceLang, targetLang, options)`

获取快速翻译的主函数。

**参数：**
- `word` (string): 要翻译的单词
- `sourceLang` (string): 源语言代码（如 'de', 'en', 'zh'）
- `targetLang` (string, 可选): 目标语言代码，默认使用系统语言
- `options` (object, 可选):
  - `vocabListGetter` (Function): 获取本地vocabulary列表的函数
  - `apiProvider` (Function): 自定义API提供者，默认使用MyMemory

**返回值：**
- `Promise<string|null>`: 翻译结果，如果查询失败返回null

**示例：**

```javascript
import { getQuickTranslation } from './services/translationService'

// 基本使用
const translation = await getQuickTranslation('Haus', 'de', 'en')
console.log(translation) // 'house'

// 使用本地vocabulary表
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

// 使用自定义API
const customAPI = async (word, sourceLang, targetLang) => {
  // 自定义API实现
  const response = await fetch(`your-api-endpoint?word=${word}&from=${sourceLang}&to=${targetLang}`)
  const data = await response.json()
  return data.translation
}

const translation = await getQuickTranslation('Haus', 'de', 'en', {
  apiProvider: customAPI
})
```

## 缓存管理

### 缓存Key设计

缓存key格式：`quick_translation_v1_{sourceLang}_{targetLang}_{normalizedWord}`

例如：
- `quick_translation_v1_de_en_haus`
- `quick_translation_v1_zh_en_你好`

### 缓存策略

1. **内存缓存**：同一会话中的查询结果缓存在内存中，避免重复查询
2. **localStorage缓存**：持久化缓存，有效期30天
3. **自动清理**：过期缓存自动清理

### 缓存管理函数

```javascript
import { clearTranslationCache, getCacheStats } from './services/translationService'

// 清除所有缓存
clearTranslationCache()

// 获取缓存统计
const stats = getCacheStats()
console.log(stats) // { memoryCacheSize: 10, localStorageCacheSize: 50 }
```

## 在TokenSpan中使用

`TokenSpan` 组件已经集成了hover翻译功能。当用户hover在单词token上时，会自动触发翻译查询。

**特性：**
- 延迟500ms触发查询（避免鼠标快速移动时频繁查询）
- 只在没有vocab notation时显示（避免重复显示）
- 自动使用系统语言或全局选择的语言作为目标语言

## 自定义API实现

如果需要替换默认的MyMemory API，可以实现自定义API提供者：

```javascript
const customTranslationAPI = async (word, sourceLang, targetLang) => {
  try {
    // 调用你的API
    const response = await fetch(`https://your-api.com/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word, sourceLang, targetLang })
    })
    
    const data = await response.json()
    return data.translation
  } catch (error) {
    console.error('Translation API error:', error)
    return null
  }
}

// 在getQuickTranslation中使用
const translation = await getQuickTranslation('word', 'de', 'en', {
  apiProvider: customTranslationAPI
})
```

## 支持的API

### MyMemory (默认)

免费API，有请求限制。适合开发和小规模使用。

### 其他可选API

- **Google Translate API**：需要API key，有配额限制
- **DeepL API**：高质量翻译，需要API key
- **百度翻译API**：中文翻译效果好，需要API key

## 注意事项

1. **API限制**：MyMemory免费API有请求频率限制，建议在生产环境中替换为付费API
2. **缓存大小**：localStorage有大小限制（通常5-10MB），注意定期清理过期缓存
3. **语言支持**：目前系统语言只支持en/zh，其他语言fallback到en
4. **性能优化**：使用内存缓存和延迟查询，减少不必要的API调用

## 故障排查

### 翻译不显示

1. 检查浏览器控制台是否有错误
2. 确认单词不为空且长度>0
3. 检查网络连接（如果使用外部API）
4. 查看缓存是否正常（使用`getCacheStats()`）

### 翻译结果不准确

1. 检查源语言和目标语言设置是否正确
2. 尝试清除缓存后重新查询
3. 考虑替换为更准确的翻译API

### 性能问题

1. 检查是否有过多的API调用（查看网络请求）
2. 确认缓存正常工作
3. 考虑增加延迟时间或优化查询逻辑

