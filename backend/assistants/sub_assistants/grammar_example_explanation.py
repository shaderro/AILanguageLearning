from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import grammar_example_explanation_sys_prompt,grammar_example_explanation_template
from typing import Optional, Union
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence

class GrammarExampleExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=grammar_example_explanation_sys_prompt,
            max_tokens=100,
            parse_json=False
        )

    def build_prompt(
        self,
        grammar: str,
        sentence: Union[Sentence, NewSentence]
    ) -> str:
        return grammar_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            grammar_knowledge_point=grammar,
        )
    
    def run(
        self,
        grammar: str,
        sentence: Union[Sentence, NewSentence],
        **kwargs
    ) -> str:
        """
        执行对话历史总结。
        
        :param dialogue_history: 对话历史字符串
        """
        return super().run(grammar, sentence, **kwargs)
    