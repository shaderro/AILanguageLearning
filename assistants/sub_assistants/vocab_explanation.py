from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import (
    vocab_explanation_sys_prompt,
    vocab_explanation_template,
)
from data_managers.data_classes import Sentence
from typing import Optional


class VocabExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_explanation_sys_prompt,
            max_tokens=300,
            parse_json=True  # 词汇解释需要 JSON 解析
        )

    def build_prompt(
        self,
        vocab: str,
        sentence: Sentence,
    ) -> str:
        return vocab_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )

    def run(
        self,
        vocab: str,
        sentence: Sentence,
        **kwargs,
    ) -> dict | list[dict] | str:
        return super().run(vocab=vocab, sentence=sentence, **kwargs) 