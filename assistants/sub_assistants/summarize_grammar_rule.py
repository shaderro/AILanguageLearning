from typing import Optional
from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.utility import parse_json_from_text
from assistants.sub_assistants.prompt import summarize_grammar_rule_template, summarize_grammar_rule_sys_prompt

class SummarizeGrammarRuleAssistant(SubAssistant):

    def __init__(self):
        super().__init__(
            sys_prompt=summarize_grammar_rule_sys_prompt,
            max_tokens=100,
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
        verbose: bool = False
    ) -> list[dict] | str:
        return super().run(quoted_sentence, user_question, ai_response, dialogue_context, verbose=verbose)

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