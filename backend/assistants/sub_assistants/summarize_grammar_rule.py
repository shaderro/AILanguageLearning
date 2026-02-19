from typing import Optional
from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.utility import parse_json_from_text
from backend.assistants.sub_assistants.prompt import summarize_grammar_rule_template
from backend.assistants.sub_assistants.summarize_grammar_prompt import summarize_grammar_rule_sys_prompt

class SummarizeGrammarRuleAssistant(SubAssistant):

    def __init__(self):
        super().__init__(
            sys_prompt=summarize_grammar_rule_sys_prompt,
            max_tokens=300,
            parse_json=True
        )

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
            print(f"⚠️ [SummarizeGrammar] 检测到传入 dialogue_context（长度: {len(dialogue_context)} 字符），但当前阶段已禁用，将忽略")
        context_info = "这是第一轮对话，没有上文。"

        return summarize_grammar_rule_template.format(
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
        language: Optional[str] = None,
        verbose: bool = False,
        **kwargs
    ) -> list[dict] | str:
        # 格式化 system prompt，添加语言信息
        original_sys_prompt = self.sys_prompt
        formatted_language = language or "中文"
        self.sys_prompt = summarize_grammar_rule_sys_prompt.format(
            language=formatted_language
        )
        
        try:
            result = super().run(quoted_sentence, user_question, ai_response, dialogue_context, verbose=verbose, **kwargs)
            # 只打印输出结果，不打印 prompt
            print(f"✅ [SummarizeGrammarRule] 输出结果: {result}")
        finally:
            # 恢复原始 sys_prompt，避免影响后续调用
            self.sys_prompt = original_sys_prompt
        return result

""""
summarize_grammar_rule = SummarizeGrammarRuleAssistant()
quoted_sentence = "这是一个引用的句子。"
user_question = "这个句子中的语法规则是什么？"
ai_response = "这个句子使用了被动语态。"
prompt = summarize_grammar_rule.build_prompt(quoted_sentence, user_question, ai_response)
summarize_grammar_rule_response = summarize_grammar_rule.run(quoted_sentence, user_question, ai_response, verbose=True)
print(summarize_grammar_rule_response.get("grammar_rule_name", "未找到语法规则名称"))
print(summarize_grammar_rule_response.get("grammar_rule_summary", "未找到语法规则总结"))
"""""