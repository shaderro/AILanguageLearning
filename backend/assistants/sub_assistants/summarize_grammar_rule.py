from typing import Optional
from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.utility import parse_json_from_text
from backend.assistants.sub_assistants.prompt import summarize_grammar_rule_template, summarize_grammar_rule_sys_prompt

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
        context_info = (
            f"这是对话的上文，用于提供背景参考，不需要总结：\n{dialogue_context}"
            if dialogue_context else "这是第一轮对话，没有上文。"
        )

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
        
        # 🔍 打印完整的 system prompt 用于调试
        print(f"🔍 [SummarizeGrammarRule] ========== System Prompt ==========")
        print(f"🔍 [SummarizeGrammarRule] Language: {formatted_language}")
        print(f"🔍 [SummarizeGrammarRule] System Prompt:\n{self.sys_prompt}")
        print(f"🔍 [SummarizeGrammarRule] ====================================")
        
        try:
            result = super().run(quoted_sentence, user_question, ai_response, dialogue_context, verbose=verbose, **kwargs)
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