from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import (
    vocab_explanation_sys_prompt,
    vocab_explanation_template,
)
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence
from typing import Optional, Union


class VocabExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_explanation_sys_prompt,
            max_tokens=4000,  # 🔧 增加到 4000，避免解释被截断（中文解释可能较长）
            parse_json=True  # 词汇解释需要 JSON 解析
        )

    def build_prompt(
        self,
        vocab: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None
    ) -> str:
        return vocab_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )

    def run(
        self,
        vocab: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None,
        **kwargs,
    ) -> dict | list[dict] | str:
        # 格式化 system prompt，添加语言信息
        original_sys_prompt = self.sys_prompt
        formatted_language = language or "中文"
        self.sys_prompt = vocab_explanation_sys_prompt.format(
            language=formatted_language
        )
        
        # 🔍 打印完整的 system prompt 用于调试
        print(f"🔍 [VocabExplanation] ========== System Prompt ==========")
        print(f"🔍 [VocabExplanation] Language: {formatted_language}")
        print(f"🔍 [VocabExplanation] Vocab: {vocab}")
        print(f"🔍 [VocabExplanation] System Prompt:\n{self.sys_prompt}")
        print(f"🔍 [VocabExplanation] ====================================")
        
        try:
            # vocab_explanation 使用关键字参数传递，确保 user_id 和 session 能正确传递
            result = super().run(vocab=vocab, sentence=sentence, language=language, **kwargs)
        finally:
            # 恢复原始 sys_prompt，避免影响后续调用
            self.sys_prompt = original_sys_prompt
        return result 