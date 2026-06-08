from dataclasses import dataclass, field
from typing import Union, Optional

from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import (
    vocab_example_explanation_sys_prompt,
    vocab_example_explanation_template,
)
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence


@dataclass
class VocabExampleTarget:
    """vocab example explanation 的输入：lemma + 句中词形 + token 位置。"""
    lemma: str
    word_form: str
    token_indices: list[int] = field(default_factory=list)


class VocabExampleExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_example_explanation_sys_prompt,
            max_tokens=4000,  # 🔧 增加到 4000，避免 context_explanation 被截断（中文解释可能较长）
            parse_json=False  # 按现有使用场景返回原始字符串（JSON 文本）
        )

    def build_prompt(
        self,
        vocab: str = "",
        sentence: Union[Sentence, NewSentence, None] = None,
        language: Optional[str] = None,
        *,
        lemma: Optional[str] = None,
        word_form: Optional[str] = None,
        token_indices: Optional[list[int]] = None,
        **kwargs,
    ) -> str:
        effective_lemma = (lemma or vocab or "").strip()
        effective_word_form = (word_form or vocab or effective_lemma).strip()
        indices = list(token_indices or [])
        if indices:
            token_index_label = ", ".join(str(i) for i in indices)
        else:
            token_index_label = "（未指定）"
        return vocab_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body if sentence else "",
            lemma=effective_lemma,
            word_form=effective_word_form,
            token_index_label=token_index_label,
        )

    def run(
        self,
        vocab: str = "",
        sentence: Union[Sentence, NewSentence, None] = None,
        language: Optional[str] = None,
        *,
        lemma: Optional[str] = None,
        word_form: Optional[str] = None,
        token_indices: Optional[list[int]] = None,
        **kwargs,
    ) -> str:
        effective_lemma = (lemma or vocab or "").strip()
        effective_word_form = (word_form or vocab or effective_lemma).strip()
        indices = list(token_indices or [])

        original_sys_prompt = self.sys_prompt
        formatted_language = language or "中文"
        self.sys_prompt = vocab_example_explanation_sys_prompt.format(
            output_language=formatted_language
        )

        _sp_len = len(self.sys_prompt) if self.sys_prompt else 0
        print(
            f"🔍 [VocabExampleExplanation] language={formatted_language} "
            f"lemma={effective_lemma!r} word_form={effective_word_form!r} "
            f"token_indices={indices} sys_prompt_chars={_sp_len}"
        )

        try:
            result = super().run(
                vocab=vocab,
                sentence=sentence,
                language=language,
                lemma=effective_lemma,
                word_form=effective_word_form,
                token_indices=indices,
                **kwargs,
            )
        finally:
            self.sys_prompt = original_sys_prompt
        return result
