# Hover 翻译功能当前状态说明

## 📋 功能概述

当用户将鼠标悬停在**没有vocab notation的单词token**上时，系统会自动显示一个轻量级翻译tooltip。

## ✅ 预期行为

### 1. 触发条件

**会显示翻译tooltip的情况**：
- ✅ Token是文本类型（`isTextToken = true`）
- ✅ Token没有vocab notation（没有绿色下划线）
- ✅ Token是可选择的（`hoverAllowed = true`）
- ✅ 单词长度 > 0
- ✅ 鼠标悬停至少 **500ms**（延迟触发）

**不会显示翻译tooltip的情况**：
- ❌ Token有vocab notation（有绿色下划线）- 会显示vocab卡片，不显示翻译
- ❌ Token是标点符号或空格
- ❌ Token不可选择
- ❌ 鼠标快速移动（未停留500ms）

### 2. UI表现

**Tooltip显示位置**：
- 📍 显示在token的**下方**（`position="bottom"`）
- 📍 自动定位，避免超出视口

**Tooltip内容**：
- 📝 单词本身（粗体，较大字体）
- 📝 翻译结果（灰色文字，较小字体）
- 🎨 深色背景（`bg-gray-900`），白色文字
- 🎨 圆角，阴影效果

**Tooltip样式示例**：
```
┌─────────────┐
│   Haus      │  ← 单词（粗体）
│   house     │  ← 翻译（灰色）
└─────────────┘
     ↑
   token
```

### 3. 查询流程

**查询顺序**（按优先级）：
1. 💾 **内存缓存** - 同一会话中的查询结果
2. 💾 **localStorage缓存** - 持久化缓存（30天有效期）
3. 📚 **本地vocabulary表** - 如果提供了`vocabListGetter`（当前未实现）
4. 🌐 **外部API** - MyMemory翻译API（默认）

**缓存策略**：
- 第一次查询：调用API，结果缓存到内存和localStorage
- 第二次查询：直接从内存缓存读取（最快）
- 页面刷新后：从localStorage缓存读取

### 4. 语言设置

**源语言（sourceLang）**：
- 当前默认：`'de'`（德语）
- ⚠️ **注意**：这是硬编码的，后续需要从ArticleViewer传递`articleLanguage`

**目标语言（targetLang）**：
- 优先使用：全局选择的语言（`selectedLanguage`）
- 回退：系统语言（`getSystemLanguage()`）
- 支持：`'en'`（英文）或 `'zh'`（中文）
- 其他语言fallback到`'en'`

### 5. 控制台日志

**正常流程的日志**：

```
// 1. Hover触发检查
🔍 [TokenSpan] Hover翻译触发条件检查: {
  isTextToken: true,
  hasVocabVisual: false,
  hoverAllowed: true,
  word: "Haus",
  wordLength: 4,
  sourceLang: "de",
  targetLang: "en"
}

// 2. 延迟500ms后开始查询
🔍 [TokenSpan] 开始查询翻译: Haus

// 3. 调用翻译服务
🔍 [TokenSpan] 调用getQuickTranslation: {
  word: "Haus",
  sourceLang: "de",
  targetLang: "en"
}

// 4. 缓存命中或API调用
💾 [TranslationService] 从内存缓存获取翻译: Haus -> house
// 或
💾 [TranslationService] 从localStorage缓存获取翻译: Haus -> house
// 或
🌐 [TranslationService] 从外部API获取翻译: Haus -> house

// 5. 查询结果
✅ [TokenSpan] 翻译查询结果: {
  word: "Haus",
  translation: "house"
}

// 6. 状态更新
✅ [TokenSpan] 翻译tooltip状态更新: {
  translation: "house",
  showQuickTranslation: true
}
```

**不触发的情况**：

```
⚠️ [TokenSpan] Hover翻译未触发: {
  isTextToken: true,
  hasVocabVisual: true,  // 有vocab notation
  hoverAllowed: true,
  word: "Haus",
  reason: "has vocab notation"
}
```

### 6. 性能优化

**延迟机制**：
- ⏱️ 延迟500ms触发查询，避免鼠标快速移动时频繁查询
- ⏱️ 如果鼠标在500ms内离开，查询会被取消

**查询取消**：
- 当鼠标离开token时，立即取消正在进行的查询
- 避免不必要的API调用

**缓存优化**：
- 内存缓存：同一会话中立即返回
- localStorage缓存：页面刷新后仍可使用
- 自动清理过期缓存（30天）

## 🧪 测试场景

### 场景 1: 普通单词（无vocab notation）

**步骤**：
1. 找到文章中没有绿色下划线的单词
2. 将鼠标悬停在单词上
3. 保持不动至少500ms

**预期**：
- ✅ 500ms后在单词下方显示翻译tooltip
- ✅ Tooltip显示单词和翻译
- ✅ 控制台显示完整的查询日志

**示例**：
- 德语单词 "Haus" → 显示 "house"
- 德语单词 "und" → 显示 "and"

### 场景 2: 有vocab notation的单词

**步骤**：
1. 找到文章中有绿色下划线的单词（有vocab notation）
2. 将鼠标悬停在单词上

**预期**：
- ❌ **不显示**翻译tooltip
- ✅ 显示vocab notation卡片（原有的功能）
- ✅ 控制台显示：`reason: "has vocab notation"`

### 场景 3: 缓存测试

**步骤**：
1. 第一次hover一个单词（例如 "Haus"）
2. 等待翻译显示
3. 鼠标离开
4. 再次hover同一个单词

**预期**：
- ✅ 第一次：可能调用API或从localStorage读取
- ✅ 第二次：从内存缓存读取（更快）
- ✅ 控制台显示：`💾 [TranslationService] 从内存缓存获取翻译`

### 场景 4: 快速移动鼠标

**步骤**：
1. 快速移动鼠标经过多个单词
2. 不停留在任何单词上超过500ms

**预期**：
- ❌ 不触发任何翻译查询
- ✅ 控制台不显示查询日志（或显示被取消的日志）

### 场景 5: 鼠标离开

**步骤**：
1. Hover在单词上，等待翻译显示
2. 移动鼠标离开单词

**预期**：
- ✅ Tooltip立即消失
- ✅ 正在进行的查询被取消
- ✅ 控制台可能显示：`⚠️ [TokenSpan] 翻译查询已被取消，忽略结果`

## 🔍 验证清单

### 功能验证

- [ ] Hover普通单词时，500ms后显示翻译tooltip
- [ ] Tooltip显示在单词下方
- [ ] Tooltip显示单词和翻译
- [ ] 有vocab notation的单词不显示翻译tooltip
- [ ] 鼠标离开时tooltip立即消失
- [ ] 快速移动鼠标时不触发查询

### 日志验证

- [ ] 控制台显示"Hover翻译触发条件检查"
- [ ] 控制台显示"开始查询翻译"
- [ ] 控制台显示"调用getQuickTranslation"
- [ ] 控制台显示缓存或API查询结果
- [ ] 控制台显示"翻译查询结果"
- [ ] 控制台显示"翻译tooltip状态更新"

### 性能验证

- [ ] 第二次hover同一单词时使用缓存（更快）
- [ ] 快速移动鼠标时不触发查询
- [ ] 鼠标离开时查询被取消

## ⚠️ 已知限制

1. **源语言硬编码**：
   - 当前默认使用`'de'`（德语）
   - 需要从ArticleViewer传递`articleLanguage`来动态设置

2. **本地vocabulary查询未实现**：
   - `vocabListGetter`选项已预留，但未集成
   - 当前只使用缓存和API

3. **API限制**：
   - MyMemory免费API有请求频率限制
   - 生产环境建议替换为付费API

4. **语言支持**：
   - 系统语言只支持`'en'`和`'zh'`
   - 其他语言fallback到`'en'`

## 🐛 故障排查

### 问题：Tooltip不显示

**检查**：
1. 控制台是否有错误？
2. 单词是否有vocab notation？（有的话不会显示）
3. 是否hover了至少500ms？
4. 控制台是否显示"Hover翻译触发条件检查"？
5. 翻译查询是否成功？

**可能原因**：
- 网络问题（API调用失败）
- 语言设置错误
- API限制（请求频率过高）

### 问题：翻译结果不准确

**检查**：
1. 源语言是否正确？（当前默认'de'）
2. 目标语言是否正确？
3. 缓存是否过期？

**解决方案**：
```javascript
// 清除缓存后重新测试
import { clearTranslationCache } from './services/translationService'
clearTranslationCache()
```

### 问题：Tooltip位置不对

**检查**：
- Tooltip应该在单词**下方**显示
- 如果位置不对，检查`QuickTranslationTooltip`组件的定位逻辑

## 📝 当前实现状态

✅ **已完成**：
- 翻译服务核心逻辑
- Tooltip组件
- TokenSpan集成
- 缓存机制
- 延迟触发
- 调试日志

⚠️ **待优化**：
- 源语言动态获取（从ArticleViewer传递）
- 本地vocabulary表查询集成
- API替换（生产环境）

## 🎯 测试重点

**核心功能**：
1. ✅ Hover普通单词显示翻译
2. ✅ 有vocab notation的单词不显示翻译
3. ✅ Tooltip显示在下方
4. ✅ 缓存正常工作

**边界情况**：
1. ✅ 快速移动鼠标不触发
2. ✅ 鼠标离开立即清除
3. ✅ 查询取消机制

现在可以按照以上说明进行测试了！


