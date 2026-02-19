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
        # 🔧 当前阶段禁用历史消息，避免 prompt 过长
        # 即使传入了 context_info，也忽略它
        if context_info:
            print(f"⚠️ [AnswerQuestion] 检测到传入 context_info（长度: {len(context_info)} 字符），但当前阶段已禁用，将忽略")
        context_info = "这是第一轮对话，没有上文。"
        print(f"📊 [AnswerQuestion] 使用默认提示（不包含历史消息）")
        
        # 格式化 quoted_part：如果用户选择了特定文本，明确标注；否则说明是整句话
        if quoted_part:
            quoted_part_formatted = f'"{quoted_part}"'
        else:
            quoted_part_formatted = "用户引用了整句话"
        
        final_prompt = answer_question_template.format(
            quoted_part=quoted_part_formatted,
            context_info=context_info,
            full_sentence=full_sentence,
            user_question=user_question
        )
        
        # 🔧 记录最终 prompt 的长度
        prompt_length = len(final_prompt)
        print(f"📊 [AnswerQuestion] 最终 prompt 长度: {prompt_length} 字符")
        if prompt_length > 4000:
            print(f"⚠️ [AnswerQuestion] 警告：prompt 较长 ({prompt_length} 字符)，可能影响 API 响应速度")
        
        return final_prompt

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