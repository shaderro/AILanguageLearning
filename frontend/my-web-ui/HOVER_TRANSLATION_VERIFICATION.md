# Hover 翻译功能验证指南

## 验证步骤

### 1. 准备工作

1. **打开浏览器开发者工具**
   - 按 `F12` 或右键选择"检查"
   - 切换到 `Console` 标签页

2. **打开一篇文章**
   - 确保文章中有德语单词（或其他非中文/英文的单词）
   - 确保这些单词**没有**vocab notation（没有绿色下划线）

### 2. 基本验证

#### 步骤 1: 找到没有vocab notation的token
- 在文章中找到一个**普通单词**（没有绿色下划线的）
- 例如：德语文章中的 "Haus", "und", "der" 等

#### 步骤 2: Hover测试
1. **将鼠标悬停在单词上**
   - 保持不动至少 **500ms**（延迟触发时间）
   - 观察是否出现翻译tooltip

2. **预期效果**：
   - ✅ Tooltip出现在单词**下方**
   - ✅ 显示单词本身
   - ✅ 显示翻译结果
   - ✅ Tooltip样式为深色背景（gray-900）

#### 步骤 3: 检查控制台日志
在控制台中应该看到以下日志：

```
🔍 [TokenSpan] Hover翻译触发条件检查: { isTextToken: true, hasVocabVisual: false, ... }
🔍 [TokenSpan] 开始查询翻译: Haus
🔍 [TokenSpan] 调用getQuickTranslation: { word: "Haus", sourceLang: "de", targetLang: "en" }
💾 [TranslationService] 从localStorage缓存获取翻译: Haus -> house
✅ [TokenSpan] 翻译查询结果: { word: "Haus", translation: "house" }
✅ [TokenSpan] 翻译tooltip状态更新: { translation: "house", showQuickTranslation: true, ... }
```

### 3. 验证场景

#### 场景 1: 有vocab notation的token（不应显示翻译）
1. 找到一个**有绿色下划线**的单词（有vocab notation）
2. Hover在单词上
3. **预期**：只显示vocab notation卡片，**不显示**快速翻译tooltip
4. 控制台应该显示：
   ```
   ⚠️ [TokenSpan] Hover翻译未触发: { hasVocabVisual: true, reason: "has vocab notation" }
   ```

#### 场景 2: 非文本token（不应显示翻译）
1. Hover在标点符号或空格上
2. **预期**：不显示翻译tooltip
3. 控制台应该显示：
   ```
   ⚠️ [TokenSpan] Hover翻译未触发: { isTextToken: false, reason: "not text token" }
   ```

#### 场景 3: 缓存测试
1. **第一次hover**：应该调用API或查询缓存
   - 控制台可能显示：`🌐 [TranslationService] 从外部API获取翻译: ...`
   - 或：`💾 [TranslationService] 从localStorage缓存获取翻译: ...`

2. **第二次hover同一个单词**：应该使用缓存
   - 控制台应该显示：`💾 [TranslationService] 从内存缓存获取翻译: ...`
   - 响应应该更快

#### 场景 4: 鼠标快速移动（不应频繁查询）
1. 快速移动鼠标经过多个单词
2. **预期**：不会为每个单词都触发查询（因为有500ms延迟）
3. 只有停留超过500ms的单词才会查询

#### 场景 5: 鼠标离开（应清除翻译）
1. Hover在单词上，等待翻译显示
2. 移动鼠标离开单词
3. **预期**：翻译tooltip立即消失

### 4. 故障排查

#### 问题 1: Tooltip不显示

**检查清单**：
- [ ] 控制台是否有错误信息？
- [ ] 单词是否有vocab notation？（有的话不会显示）
- [ ] 是否hover了至少500ms？
- [ ] 控制台是否显示"Hover翻译触发条件检查"？
- [ ] 翻译查询是否成功？（查看"翻译查询结果"日志）

**可能原因**：
1. **网络问题**：API调用失败
   - 检查网络连接
   - 查看控制台是否有网络错误

2. **语言设置问题**：源语言或目标语言不正确
   - 检查 `sourceLang` 和 `targetLang` 的值
   - 默认源语言是 'de'（德语）

3. **API限制**：MyMemory API可能有请求限制
   - 查看控制台是否有API错误
   - 考虑替换为其他API

#### 问题 2: Tooltip位置不对

**检查**：
- Tooltip应该在单词**下方**显示
- 如果位置不对，检查 `QuickTranslationTooltip` 组件的 `position` prop

#### 问题 3: 翻译结果不准确

**可能原因**：
1. 源语言设置错误
2. API翻译质量问题
3. 缓存了错误的翻译结果

**解决方案**：
```javascript
// 清除缓存后重新测试
import { clearTranslationCache } from './services/translationService'
clearTranslationCache()
```

### 5. 调试技巧

#### 启用详细日志
所有关键步骤都有日志输出，查看控制台即可：

1. **Hover触发检查**：`🔍 [TokenSpan] Hover翻译触发条件检查`
2. **翻译查询开始**：`🔍 [TokenSpan] 开始查询翻译`
3. **翻译服务调用**：`🔍 [TokenSpan] 调用getQuickTranslation`
4. **缓存命中**：`💾 [TranslationService] 从...缓存获取翻译`
5. **API调用**：`🌐 [TranslationService] 从外部API获取翻译`
6. **结果更新**：`✅ [TokenSpan] 翻译查询结果`

#### 检查缓存状态
```javascript
import { getCacheStats } from './services/translationService'

const stats = getCacheStats()
console.log('缓存统计:', stats)
// { memoryCacheSize: 10, localStorageCacheSize: 50 }
```

#### 手动测试翻译服务
```javascript
import { getQuickTranslation } from './services/translationService'

// 在浏览器控制台中测试
getQuickTranslation('Haus', 'de', 'en').then(translation => {
  console.log('翻译结果:', translation)
})
```

### 6. 预期行为总结

| 场景 | 预期行为 |
|------|---------|
| Hover普通单词（无vocab notation） | ✅ 显示翻译tooltip在下方 |
| Hover有vocab notation的单词 | ❌ 不显示翻译tooltip（显示vocab卡片） |
| Hover标点符号/空格 | ❌ 不显示翻译tooltip |
| 鼠标快速移动 | ❌ 不触发查询（延迟保护） |
| 鼠标离开单词 | ✅ Tooltip立即消失 |
| 第二次hover同一单词 | ✅ 使用缓存，响应更快 |

### 7. 成功标准

✅ **功能正常**的标志：
1. Hover普通单词时，500ms后在下方显示翻译tooltip
2. Tooltip显示单词和翻译
3. 有vocab notation的单词不显示翻译tooltip
4. 控制台日志清晰，无错误
5. 缓存正常工作（第二次查询更快）

如果以上都满足，说明功能正常工作！

