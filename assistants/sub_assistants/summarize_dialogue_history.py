from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import summarize_dialogue_history_sys_prompt, summarize_dialogue_history_template
from typing import Optional
from data_managers.data_classes import Sentence

class SummarizeDialogueHistoryAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=summarize_dialogue_history_sys_prompt,
            max_tokens=100,
            parse_json=False
        )

    def build_prompt(
        self,
        dialogue_history: str,
        sentence: Sentence
    ) -> str:

        return summarize_dialogue_history_template.format(
            quoted_sentence=sentence.sentence_body,
            dialogue_history=dialogue_history,
        )
    
    def run(
        self,
        dialogue_history: str,
        sentence: Sentence,
        verbose: bool = False
    ) -> str:
        """
        执行对话历史总结。
        
        :param dialogue_history: 对话历史字符串
        """
        return super().run(dialogue_history, sentence, verbose=verbose)
    
