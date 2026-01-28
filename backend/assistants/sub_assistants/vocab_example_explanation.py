from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import (
    vocab_example_explanation_sys_prompt,
    vocab_example_explanation_template,
)
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence
from typing import Union, Optional


class VocabExampleExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_example_explanation_sys_prompt,
            max_tokens=100,
            parse_json=False  # 按现有使用场景返回原始字符串（JSON 文本）
        )

    def build_prompt(
        self,
        vocab: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None
    ) -> str:
        return vocab_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )

    def run(
        self,
        vocab: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None,
        **kwargs,
    ) -> str:
        # 格式化 system prompt，添加语言信息
        original_sys_prompt = self.sys_prompt
        formatted_language = language or "中文"
        self.sys_prompt = vocab_example_explanation_sys_prompt.format(
            language=formatted_language
        )
        
        # 🔍 打印完整的 system prompt 用于调试
        print(f"🔍 [VocabExampleExplanation] ========== System Prompt ==========")
        print(f"🔍 [VocabExampleExplanation] Language: {formatted_language}")
        print(f"🔍 [VocabExampleExplanation] Vocab: {vocab}")
        print(f"🔍 [VocabExampleExplanation] System Prompt:\n{self.sys_prompt}")
        print(f"🔍 [VocabExampleExplanation] ====================================")
        
        try:
            result = super().run(vocab=vocab, sentence=sentence, language=language, **kwargs)
        finally:
            # 恢复原始 sys_prompt，避免影响后续调用
            self.sys_prompt = original_sys_prompt
        return result 