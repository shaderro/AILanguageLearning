from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import answer_question_sys_prompt, answer_question_template
from typing import Optional

class AnswerQuestionAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=answer_question_sys_prompt,
            max_tokens=100,
            parse_json=True
        )

    def build_prompt(
        self,
        quoted_sentence: str,
        user_question: str,
        context_info: Optional[str] = None
    ) -> str:
        context_info = (
            f"这是对话的上文，用于提供背景参考：\n{context_info}"
            if context_info else "这是第一轮对话，没有上文。"
        )

        return answer_question_template.format(
            context_info=context_info,
            quoted_sentence=quoted_sentence,
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