from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import answer_question_sys_prompt, answer_question_template
from typing import Optional

class AnswerQuestionAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=answer_question_sys_prompt,
            max_tokens=600,
            parse_json=True
        )

    def build_prompt(
        self,
        
        full_sentence: str,
        user_question: str,
        quoted_part: Optional[str] = None,
        context_info: Optional[str] = None
    ) -> str:
        context_info = (
            f"这是对话的上文，用于提供背景参考：\n{context_info}"
            if context_info else "这是第一轮对话，没有上文。"
        )
        # 格式化 quoted_part：如果用户选择了特定文本，明确标注；否则说明是整句话
        if quoted_part:
            quoted_part_formatted = f'"{quoted_part}"'
        else:
            quoted_part_formatted = "用户引用了整句话"
        
        return answer_question_template.format(
            quoted_part=quoted_part_formatted,
            context_info=context_info,
            full_sentence=full_sentence,
            user_question=user_question
        )

"""""  
test_answer_question = AnswerQuestionAssistant()
test_sentence = "This is a test sentence."
test_question = "What does this sentence mean in Chinese?"
test_context = "没有上文信息。"
test_answer_question_response = test_answer_question.run(
    quoted_sentence=test_sentence,
    user_question=test_question,
    context_info=test_context,
    verbose=True
)
"""