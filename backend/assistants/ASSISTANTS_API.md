# Assistants 参数说明

本文件汇总 `backend/assistants/sub_assistants` 目录下各 Assistant 的入参与返回类型，便于在代码中正确调用。

- 统一行为：所有 Assistant 继承自 `SubAssistant`，核心方法为 `run(...)`，内部会调用 LLM（DeepSeek）。若 `parse_json=True`，将尝试把模型输出解析为 JSON。
- 通用可选参数：`verbose: bool=False`（打印 prompt 与原始响应）

## 词汇与示例类

- VocabExplanationAssistant
  - run(vocab: str, sentence: Sentence|NewSentence, **kwargs) -> dict|list[dict]|str
  - 说明：根据词汇与句子生成“词汇解释”，要求返回 JSON（字段：explanation）。

- VocabExampleExplanationAssistant
  - run(vocab: str, sentence: Sentence|NewSentence, **kwargs) -> str
  - 说明：生成词汇在当前句子的上下文解释（自由文本/JSON字符串）。

## 语法相关

- GrammarExampleExplanationAssistant
  - run(grammar: str, sentence: Sentence|NewSentence) -> str
  - 说明：对句中某语法点给出示例解释/说明（自由文本）。

- SummarizeGrammarRuleAssistant
  - run(quoted_sentence: str, user_question: str, ai_response: str, dialogue_context: str|None=None, verbose: bool=False) -> list[dict]|str
  - 说明：将一次对话中的语法要点进行结构化总结（parse_json=True）。

- CompareGrammarRuleAssistant
  - run(grammar_rule_1: str, grammar_rule_2: str, verbose: bool=False) -> list[dict]|str
  - 说明：对两条语法规则进行对比与要点提炼（parse_json=True）。

## 相关性判断与总结

- CheckIfRelevant
  - run(quoted_sentence: str, input_message: str, context_info: str|None=None, verbose: bool=False) -> dict|str
  - 说明：判断用户输入是否与学习相关（parse_json=True，返回 {"is_relevant": bool}）。

- CheckIfVocabRelevantAssistant
  - run(quoted_sentence: str, user_question: str, ai_response: str, verbose: bool=False) -> dict|str
  - 说明：判断是否为词汇相关问题（parse_json=True，返回 {"is_vocab_relevant": bool}）。

- CheckIfGrammarRelevantAssistant
  - run(quoted_sentence: str, user_question: str, ai_response: str, verbose: bool=False) -> dict|str
  - 说明：判断是否为语法相关问题（parse_json=True，返回 {"is_grammar_relevant": bool}）。

- SummarizeDialogueHistoryAssistant
  - run(dialogue_history: str, sentence: Sentence|NewSentence, verbose: bool=False) -> str
  - 说明：对对话历史进行简要总结（自由文本）。

- SummarizeVocabAssistant
  - run(quoted_sentence: str, user_question: str, ai_response: str, dialogue_context: str|None=None, verbose: bool=False) -> list[dict]|str
  - 说明：对词汇类对话进行结构化总结（parse_json=True）。

## 通用问答

- AnswerQuestionAssistant
  - run(full_sentence: str, user_question: str, quoted_part: str|None=None, context_info: str|None=None) -> dict|str
  - 说明：面向通用问答，建议提供整句、用户问题、可选引用与上下文（parse_json=True）。

## 会话状态（Session State）与对话历史（Dialogue History）

- SessionState（`assistants/chat_info/session_state.py`）
  - 关键字段（写入时机 → 用途）：
    - `set_current_sentence(sentence: Sentence|NewSentence)`：在收到/切换用户当前引用的句子后立刻设置；供后续各 Assistant 构建 prompt 使用。
    - `set_current_selected_token(selected_token: SelectedToken)`：当用户在 UI 中选中 token 时设置；用于词汇解释、难度统计等。
    - `set_current_input(user_input: str)`：每次用户提问时设置当前输入；用于记录与总结。
    - `set_current_response(ai_response: str)`：每次生成 AI 回复后设置；与 `current_input` 一同进入历史。
    - `set_check_relevant_decision(grammar: bool, vocab: bool)`：完成相关性判定后记录结果；供后续总结/入库逻辑参考。
    - `add_grammar_summary(name: str, summary: str)` / `add_vocab_summary(vocab: str)`：在完成 summarizer 调用后追加结构化摘要。
    - `add_grammar_to_add(rule_name: str, rule_explanation: str)` / `add_vocab_to_add(vocab: str)`：在总结后确认需要入库时记录待新增项。
    - `reset()`：在一次完整交互（或离开当前文章/句子）结束时重置临时状态。
  - 常用读取：
    - `get_learning_context()`：聚合当前句子、输入/输出与统计，用于诊断与可视化。

- DialogueHistory（`assistants/chat_info/dialogue_history.py`）
  - 关键方法与参数：
    - `add_message(user_input: str, ai_response: str, quoted_sentence: Sentence|NewSentence, selected_token: SelectedToken|None=None)`：
      - 调用时机：每轮问答生成 AI 回复后立即调用；将一轮对话写入历史。
      - 作用：维护 `messages_history` 并保留所用句子与（可选）选中 token。
    - `keep_in_max_turns()` / 内部 `_summarize_and_clear()`：当 `messages_history` 超过 `max_turns` 时自动触发对话总结并清空历史（摘要保留在 `summary`）。
    - `summarize_dialogue_history()`：显式触发总结；内部调用 `SummarizeDialogueHistoryAssistant.run(dialogue_history: str, sentence: Sentence|NewSentence)`，其中 `sentence` 通常传入最近一条的引用句。
    - `save_to_file(path: str)` / `load_from_file(path: str)`：持久化与恢复历史（兼容新旧句子结构），可在用户切换文章或会话结束时调用保存。
  - 推荐调用顺序（一轮交互）：
    1) `SessionState.set_current_sentence(...)`（若句子变化）；必要时 `set_current_selected_token(...)`。
    2) `SessionState.set_current_input(user_input)`。
    3) 调用相关 Assistant（问答/解释/判断/总结）。
    4) `SessionState.set_current_response(ai_response)`。
    5) `DialogueHistory.add_message(user_input, ai_response, sentence, selected_token)`。
    6) 视场景调用 `Summarize*`，将结果写入 `SessionState.add_*_summary(...)`，并按需 `add_*_to_add(...)`。
    7) 如需控量：`DialogueHistory.keep_in_max_turns()` 或在达到阈值时自动总结。

## 备注
- Sentence 类型兼容旧结构 `data_managers.data_classes.Sentence` 与新结构 `data_managers.data_classes_new.Sentence`。
- DeepSeek 模型与 API Key 在 `SubAssistant` 中配置；如需切换模型或密钥，请修改该基类。 