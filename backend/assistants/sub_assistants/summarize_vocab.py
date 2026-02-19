from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import (
    summarize_vocab_template, 
    summarize_vocab_sys_prompt,
    summarize_non_space_vocab_sys_prompt
)
from typing import Optional
from backend.assistants.utility import parse_json_from_text

class SummarizeVocabAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=summarize_vocab_sys_prompt,  # 默认使用空格语言的 prompt
            max_tokens=200,
            parse_json=True
        )
        # 保存原始的 sys_prompt，以便在需要时切换
        self.default_sys_prompt = summarize_vocab_sys_prompt
        self.non_space_sys_prompt = summarize_non_space_vocab_sys_prompt

    def build_prompt(
        self,
        quoted_sentence: str,
        user_question: str,
        ai_response: str,
        dialogue_context: Optional[str] = None
    ) -> str:
        # 🔧 当前阶段禁用历史消息，避免 prompt 过长
        # 即使传入了 dialogue_context，也忽略它
        if dialogue_context and dialogue_context != "这是第一轮对话，没有上文。":
            print(f"⚠️ [SummarizeVocab] 检测到传入 dialogue_context（长度: {len(dialogue_context)} 字符），但当前阶段已禁用，将忽略")
        context_info = "这是第一轮对话，没有上文。"

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
        is_non_whitespace: bool = False,
        verbose: bool = False,
        **kwargs
    ) -> list[dict] | str:
        # 根据语言类型动态设置 sys_prompt
        if is_non_whitespace:
            self.sys_prompt = self.non_space_sys_prompt
            print("🌐 [SummarizeVocab] 使用非空格语言 prompt（中文/日文等）")
        else:
            self.sys_prompt = self.default_sys_prompt
            print("🌐 [SummarizeVocab] 使用空格语言 prompt（英文/德文等）")
        
        # 调用父类的 run 方法，不传递 is_non_whitespace（因为 build_prompt 不需要它）
        return super().run(quoted_sentence, user_question, ai_response, dialogue_context, verbose=verbose, **kwargs)

"""" 
test_summarize_vocab = SummarizeVocabAssistant()
quoted_sentence = "This is a sample sentence for vocabulary summarization."
user_question = "What does sample mean in this context?"
ai_response = "In this context, 'sample' refers to an example or a representative part of a larger group."
summarize_vocab_response = test_summarize_vocab.run(quoted_sentence, user_question, ai_response, verbose=True)
"""