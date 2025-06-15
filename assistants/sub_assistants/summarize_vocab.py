from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import summarize_vocab_template, summarize_vocab_sys_prompt
from typing import Optional
from assistants.utility import parse_json_from_text

class SummarizeVocabAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=summarize_vocab_sys_prompt,
            max_tokens=100,
            parse_json=True
        )

    def build_prompt(
        self,
        quoted_sentence: str,
        user_question: str,
        ai_response: str,
        dialogue_context: Optional[str] = None
    ) -> str:
        context_info = (
            f"{dialogue_context}"
            if dialogue_context else "这是第一轮对话，没有上文。"
        )

        return summarize_vocab_template.format(
            context_info=context_info,
            quoted_sentence=quoted_sentence,
            user_question=user_question,
            ai_response=ai_response
        )

    def run(
        self,
        quoted_sentence: str,
        user_question: str,
        ai_response: str,
        dialogue_context: Optional[str] = None,
        verbose: bool = False
    ) -> list[dict] | str:
        return super().run(quoted_sentence, user_question, ai_response, dialogue_context, verbose=verbose)

"""" 
test_summarize_vocab = SummarizeVocabAssistant()
quoted_sentence = "This is a sample sentence for vocabulary summarization."
user_question = "What does sample mean in this context?"
ai_response = "In this context, 'sample' refers to an example or a representative part of a larger group."
summarize_vocab_response = test_summarize_vocab.run(quoted_sentence, user_question, ai_response, verbose=True)
"""