# 新文章显示空白问题修复

## 问题诊断

### 步骤1：创建文章 ✅
- 用户上传新文章
- 后端成功创建 `OriginalText` 记录
- 文章ID生成成功

### 步骤2：获取文章列表 ✅
- API: `GET /api/v2/texts/?language=德文`
- 返回状态：200
- 文章出现在列表中

### 步骤3：获取文章详情 ❌
- API: `GET /api/v2/texts/{id}?include_sentences=true`
- 返回状态：200
- **问题**：`sentences` 数组为空

### 步骤4：前端渲染 ❌
- ArticleViewer 收到空的 `sentences` 数组
- 显示空白

## 根本原因

**后端代码错误**：`backend/api/text_routes.py` 第345行
- 访问了 `text.sentences`，但 `TextDTO` 的字段是 `text_by_sentence`
- 导致取不到句子数据，返回空数组

## 修复内容

### 修改文件
- `backend/api/text_routes.py` 第344-346行

### 修复前
```python
text_by_sentence = text.sentences if hasattr(text, 'sentences') and text.sentences else []
```

### 修复后
```python
# 注意：TextDTO 的字段是 text_by_sentence，不是 sentences
text_by_sentence = getattr(text, 'text_by_sentence', None) or getattr(text, 'sentences', None) or []
```

## 测试步骤

1. **启动后端**（如果未运行）
   ```powershell
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **启动前端**（如果未运行）
   ```powershell
   cd frontend/my-web-ui
   npm run dev
   ```

3. **测试流程**：
   - 登录/注册用户
   - 上传一篇新文章（德文）
   - 等待处理完成
   - 点击文章打开
   - **预期**：应该能看到文章内容（句子列表）

4. **检查后端日志**：
   - 应该看到：`[API] Found text {id}: {title}, sentences: {count}`
   - 如果 `count > 0`，说明修复成功

5. **检查前端控制台**：
   - 应该看到：`🔍 [DEBUG] Found single text with sentences`
   - 应该看到：`sentences` 数组不为空

## 验证要点

- ✅ 文章列表显示正常
- ✅ 文章详情API返回 `sentences` 数组不为空
- ✅ ArticleViewer 能正确渲染句子
- ✅ 句子可以点击和交互
