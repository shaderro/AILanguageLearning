# Vercel 上线版本文章显示空白问题修复

## 问题诊断

### 从日志分析：
1. **API 调用**：`GET /api/articles/1768453977` 返回 200 ✅
2. **响应格式**：`{status: 'success', data: {...}, message: '成功获取文章详情: Paris'}` ✅
3. **ArticleViewer 状态**：`sentencesLength: 5` 但 `hasSentence: false` ❌

### 根本原因：
**`/api/articles/{id}` 端点返回的句子数据缺少 `tokens` 字段**

- 前端 ArticleViewer 需要 `tokens` 字段来渲染句子内容
- 当前只返回了：`sentence_id`, `sentence_body`, `difficulty_level`, `grammar_annotations`, `vocab_annotations`
- 缺少：`tokens`, `word_tokens`, `language_code`, `is_non_whitespace`

## 修复内容

### 修改文件
- `frontend/my-web-ui/backend/main.py` 的 `get_article_detail` 函数

### 修复内容
1. **添加 tokens 字段**：从 `SentenceDTO` 中提取 `tokens` 和 `word_tokens`
2. **构建完整的 tokens 数据**：
   - 如果 DTO 有 tokens，使用 DTO 的 tokens
   - 否则，按空格切分 `sentence_body` 生成 fallback tokens
3. **添加语言相关字段**：`language_code`, `is_non_whitespace`
4. **添加 word_tokens 字段**：从 DTO 中提取 word_tokens 数据

### 修复后的数据格式
```python
{
    "sentence_id": s.sentence_id,
    "sentence_body": s.sentence_body,
    "difficulty_level": ...,
    "grammar_annotations": [...],
    "vocab_annotations": [...],
    "tokens": [
        {
            "token_body": "...",
            "sentence_token_id": 0,
            "token_type": "text",
            "selectable": True,
            ...
        }
    ],
    "word_tokens": [...],
    "language": "...",
    "language_code": "...",
    "is_non_whitespace": ...
}
```

## 验证步骤

1. **部署到 Vercel**（不 push main，仅本地测试）
2. **测试流程**：
   - 登录/注册用户
   - 上传一篇新文章（德文）
   - 等待处理完成
   - 点击文章打开
   - **预期**：应该能看到文章内容（句子列表，包含 tokens）

3. **检查前端控制台**：
   - 应该看到：`sentencesLength: 5` 且 `hasSentence: true`
   - 应该能看到句子内容正常渲染

## 注意事项

- 此修复针对 `/api/articles/{id}` 端点（旧API，当 `API_TARGET=mock` 时使用）
- 如果使用 `/api/v2/texts/{id}`（新API），已经有完整的 tokens 数据，不需要此修复
- 建议统一使用 `/api/v2/texts/{id}` API，以获得更好的性能和功能
