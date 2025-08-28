from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import check_if_relevant_template,check_if_relevant_sys_prompt
from typing import Optional

class CheckIfRelevant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=check_if_relevant_sys_prompt,
            max_tokens=100,
            parse_json=True
        )
    
    def run(self, quoted_sentence: str, input_message: str, context_info: Optional[str] = None, verbose=False) -> dict | str:
        return super().run(quoted_sentence, input_message, context_info, verbose=verbose)
    
    def build_prompt(self, quoted_sentence: str, input_message: str, context_info: str) -> str:
        context_info = (
            f"{context_info}"
            if context_info else "这是第一轮对话，没有上文。"
        )
        return check_if_relevant_template.format(
            quoted_sentence=quoted_sentence,
            input_message=input_message,
            context_info=context_info
        )

#check_if_relevant_assistant = CheckIfRelevant()
#quoted_sentence = "This is a test sentence."
#user_question = "What is the meaning of this sentence?"
#result = check_if_relevant_assistant.run(quoted_sentence, user_question, verbose=True)
#print(result.get("is_relevant", "未找到相关性判断结果"))