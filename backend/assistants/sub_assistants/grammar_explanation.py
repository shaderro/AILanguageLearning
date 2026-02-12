from typing import Optional
from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import grammar_explanation_sys_prompt, grammar_explanation_template


class GrammarExplanationAssistant(SubAssistant):
    """
    语法规则解释助手
    
    职责：根据 summarize_grammar_rule 的输出结果，生成语法规则本身的解释
    注意：只解释语法规则本身，不涉及原句，原句仅供参考
    """
    
    def __init__(self):
        super().__init__(
            sys_prompt=grammar_explanation_sys_prompt,
            max_tokens=2000,
            parse_json=True
        )
    
    def build_prompt(
        self,
        quoted_sentence: str,
        grammar_summary: dict,
    ) -> str:
        """
        构建 prompt
        
        参数:
            quoted_sentence: 用户引用的原句（仅供参考）
            grammar_summary: summarize_grammar_rule 的输出结果
                {
                    "display_name": "...",
                    "canonical": {
                        "category": "...",
                        "subtype": "...",
                        "function": "..."
                    }
                }
        """
        return grammar_explanation_template.format(
            quoted_sentence=quoted_sentence,
            display_name=grammar_summary.get("display_name", ""),
            canonical_category=grammar_summary.get("canonical", {}).get("category", ""),
            canonical_subtype=grammar_summary.get("canonical", {}).get("subtype", ""),
            canonical_function=grammar_summary.get("canonical", {}).get("function", "")
        )
    
    def run(
        self,
        quoted_sentence: str,
        grammar_summary: dict,
        language: Optional[str] = None,
        learning_language: Optional[str] = None,
        verbose: bool = False,
        **kwargs
    ) -> dict | str:
        """
        执行语法规则解释
        
        参数:
            quoted_sentence: 用户引用的原句（仅供参考）
            grammar_summary: summarize_grammar_rule 的输出结果
            language: 输出语言（如"中文"、"英文"等），默认"中文"
            learning_language: 用户正在学习的语言（如"德文"、"英文"等），默认与 language 相同
        
        返回:
            dict: {"grammar_explanation": "..."} 或原始字符串
        """
        # 格式化 system prompt，添加语言信息
        original_sys_prompt = self.sys_prompt
        output_language = language or "中文"
        learning_lang = learning_language or output_language
        self.sys_prompt = grammar_explanation_sys_prompt.format(
            learning_language=learning_lang,
            output_language=output_language
        )
        
        try:
            result = super().run(quoted_sentence, grammar_summary, verbose=verbose, **kwargs)
        finally:
            # 恢复原始 sys_prompt，避免影响后续调用
            self.sys_prompt = original_sys_prompt
        return result

