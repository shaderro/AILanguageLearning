from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import answer_question_sys_prompt, answer_question_template
from typing import Optional

class AnswerQuestionAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=answer_question_sys_prompt,
            max_tokens=400,
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
        quoted_part = (
            f"\n{quoted_part}"
            if quoted_part else "用户引用了整句话\n"
        )
        return answer_question_template.format(
            quoted_part=quoted_part,
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