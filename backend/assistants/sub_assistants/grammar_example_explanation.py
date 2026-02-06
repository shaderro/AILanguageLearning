from backend.assistants.sub_assistants.sub_assistant import SubAssistant
from backend.assistants.sub_assistants.prompt import grammar_example_explanation_sys_prompt,grammar_example_explanation_template
from typing import Optional, Union
from backend.data_managers.data_classes import Sentence
from backend.data_managers.data_classes_new import Sentence as NewSentence

class GrammarExampleExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=grammar_example_explanation_sys_prompt,
            max_tokens=4000,  # 🔧 增加到 4000，避免 context_explanation 被截断（中文解释可能较长）
            parse_json=False
        )

    def build_prompt(
        self,
        grammar: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None
    ) -> str:
        return grammar_example_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            grammar_knowledge_point=grammar,
        )
    
    def run(
        self,
        grammar: str,
        sentence: Union[Sentence, NewSentence],
        language: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        执行语法例句解释。
        
        :param grammar: 语法规则名称
        :param sentence: 句子对象
        :param language: 输出语言（如"中文"、"英文"等）
        """
        # 格式化 system prompt，添加语言信息
        original_sys_prompt = self.sys_prompt
        self.sys_prompt = grammar_example_explanation_sys_prompt.format(
            language=language or "中文"
        )
        try:
            result = super().run(grammar, sentence, language=language, **kwargs)
        finally:
            # 恢复原始 sys_prompt，避免影响后续调用
            self.sys_prompt = original_sys_prompt
        return result
    