# SessionState 接入方案（结合当前前端交互）

本文档给出在不大改前端的前提下，将会话状态 `SessionState` 与 `DialogueHistory` 平滑接入现有后端路由与前端交互的最小改造方案。

---

## 一、目标与原则
- 目标：把“文章/句子/选词/点击AI解释/问答”等事件，映射到后端 `SessionState` 对应的 setter，并在合适时机写入 `DialogueHistory`。
- 原则：
  - 就地接入：优先在现有后端路由（如 `/api/test-token-to-vocab`）内部补齐状态写入，零前端改动即可生效。
  - 可渐进抽象：需要时再增加独立 `session` 端点，避免过度耦合业务路由。

---

## 二、触发点与设置时机

- 当前文章加载/切换句子
  - `SessionState.set_current_sentence(sentence)`：在收到/切换用户当前引用的句子后立刻设置。
  - 推荐落点：
    - 短期：在需要句子的业务路由入口（如 `/api/test-token-to-vocab`）根据请求体构造 `Sentence` 并设置。
    - 中期：前端在 `useArticle(articleId)` 成功后主动调用 `POST /api/session/set_sentence`。

- 用户选中 token
  - `SessionState.set_current_selected_token(selected_token)`：在 UI 中选中 token 成功时设置。
  - 推荐落点：
    - 短期：随同业务请求（如 `/api/test-token-to-vocab`）把选中 token 放进请求体，路由内设置。
    - 中期：提供 `POST /api/session/select_token`，前端在选中时调用。

- 用户发问（或“detail explanation”视为隐式提问）
  - `SessionState.set_current_input(user_input)`：用户提交时设置。
  - 推荐落点：
    - 问答类路由（如 `/api/answer`）入口第一步设置；若无专门问答路由，则在 `/api/test-token-to-vocab` 中将 `token_body` 或生成的提示语作为“当前输入”。

- AI 回复生成后
  - `SessionState.set_current_response(ai_response)`：模型产出后立即设置。
  - 推荐落点：
    - 业务路由内拿到结果的地方。

- 相关性判定结果
  - `SessionState.set_check_relevant_decision(grammar: bool, vocab: bool)`：判定完成后设置。

- 总结与待入库
  - `add_grammar_summary(...)` / `add_vocab_summary(...)`：SummarizeXxxAssistant 返回后追加。
  - `add_grammar_to_add(...)` / `add_vocab_to_add(...)`：根据业务规则确认需要入库时记录。

- 会话收束/文章切换
  - `SessionState.reset()`：离开文章、切换文本或页面卸载时触发。
  - 推荐落点：
    - 提供 `POST /api/session/reset`；前端在路由切换或组件卸载时调用。

---

## 三、后端改造（最小化）

- 在 `frontend/my-web-ui/backend/server.py` 中（或新建 `session_state_service.py` 并导入）持有一个模块级 `SessionState` 单例：
  - 在 `/api/test-token-to-vocab` 路由内：
    1) 根据请求体构造 `Sentence`，调用 `set_current_sentence(...)`。
    2) 若包含选中 token，`set_current_selected_token(...)`。
    3) 将“隐式问题”（如 token 文本或拼接的提示）`set_current_input(...)`。
    4) 调用 LLM；得到结果后 `set_current_response(...)`。
    5) 写 `DialogueHistory.add_message(user_input, ai_response, sentence, selected_token)`；必要时触发 `keep_in_max_turns()`。

- 可选新增端点（利于前端显式控制）：
  - `POST /api/session/set_sentence` 传 `{ text_id, sentence_id, sentence_body }`
  - `POST /api/session/select_token` 传 `{ token: {...} }`
  - `POST /api/session/reset`

> 注意：`SessionState` 支持新旧 `Sentence` 结构，后端可按需构造 `data_managers.data_classes_new.Sentence`（含 tokens）或旧结构。

---

## 四、前端触发与最小调用

- 保持“零侵入”策略：现有“detail explanation with AI”会调用 `/api/test-token-to-vocab`，该路由内部完成大部分状态写入。
- 若增加 `session` 端点，前端可在 `src/services/api.js` 增加：
  - `session.setSentence({ text_id, sentence_id, sentence_body })`
  - `session.selectToken(selectedToken)`
  - `session.reset()`
- 触发时机（与现有交互对齐）：
  - 文章/句子加载完毕：`session.setSentence(...)`
  - token 选中：`session.selectToken(...)`
  - 页面卸载/文章切换：`session.reset()`

---

## 五、推荐落地顺序（优先级）
1) 在 `/api/test-token-to-vocab` 内补齐 `set_current_sentence / set_current_selected_token / set_current_input / set_current_response` 与 `DialogueHistory.add_message(...)`（立即可做）。
2) 增加 `POST /api/session/reset`，前端在文章切换/卸载时调用。
3) 视需要再补充 `set_sentence / select_token` 端点，逐步解耦业务路由。

---

## 六、调试与观测
- 利用 `SessionState.get_learning_context()` 在后端日志中快速观测当前上下文。
- 通过 `DialogueHistory.save_to_file(path)` 定期持久化，或在切换文章时保存与清空。

---

## 七、兼容性
- `Sentence` 类型同时兼容旧结构与新结构；含 tokens 的新结构可用于更丰富的统计与标注。
- 现有前端无需修改即可获得主要状态追踪；增加 `session` 端点后可渐进增强控制粒度。 