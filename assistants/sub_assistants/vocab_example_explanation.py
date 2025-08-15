from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import (
    vocab_example_explanation_sys_prompt,
    vocab_example_explanation_template,
)
from data_managers.data_classes import Sentence


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
        sentence: Sentence,
    ) -> str:
        return vocab_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )

    def run(
        self,
        vocab: str,
        sentence: Sentence,
        **kwargs,
    ) -> str:
        return super().run(vocab=vocab, sentence=sentence, **kwargs) 