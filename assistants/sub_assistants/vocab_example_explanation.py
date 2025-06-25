from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import vocab_example_explanation_sys_prompt,vocab_example_explanation_template
from typing import Optional
from data_managers.data_classes import Sentence

class VocabExampleExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_example_explanation_sys_prompt,
            max_tokens=100,
            parse_json=False
        )

    def build_prompt(
        self,
        vocab: str,
        sentence: Sentence
    ) -> str:
        return vocab_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab,
        )
    
    def run(
        self,
        vocab: str,
        sentence: Sentence
    ) -> str:
        """
        执行对话历史总结。
        
        :param dialogue_history: 对话历史字符串
        """
        return super().run(vocab, sentence)
    