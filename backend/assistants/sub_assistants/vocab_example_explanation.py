from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import (
    vocab_example_explanation_sys_prompt,
    vocab_example_explanation_template,
)
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence
from typing import Union


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
    ) -> str:
        return vocab_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )

    def run(
        self,
        vocab: str,
        sentence: Union[Sentence, NewSentence],
        **kwargs,
    ) -> str:
        return super().run(vocab=vocab, sentence=sentence, **kwargs) 