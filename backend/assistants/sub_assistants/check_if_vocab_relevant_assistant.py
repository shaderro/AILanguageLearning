from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import check_if_vocab_relevant_sys_prompt, check_if_vocab_relevant_template

class CheckIfVocabRelevantAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=check_if_vocab_relevant_sys_prompt,
            max_tokens=100,
            parse_json=True
        )
    
    def run(self, quoted_sentence: str, user_question: str, ai_response: str, verbose=False, **kwargs) -> dict | str:
        return super().run(quoted_sentence, user_question, ai_response, verbose=verbose, **kwargs)

    
    def build_prompt(self, quoted_sentence: str, user_question: str, ai_response: str) -> str:
        return check_if_vocab_relevant_template.format(
            quoted_sentence=quoted_sentence,
            user_question=user_question,
            ai_response=ai_response
        )