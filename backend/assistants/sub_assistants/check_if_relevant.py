from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import check_if_relevant_template,check_if_relevant_sys_prompt
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
        # 🔧 当前阶段禁用历史消息，避免 prompt 过长
        # 即使传入了 context_info，也忽略它
        if context_info and context_info != "这是第一轮对话，没有上文。":
            print(f"⚠️ [CheckIfRelevant] 检测到传入 context_info（长度: {len(context_info)} 字符），但当前阶段已禁用，将忽略")
        context_info = "这是第一轮对话，没有上文。"
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