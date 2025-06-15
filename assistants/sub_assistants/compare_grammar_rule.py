from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import compare_grammar_rule_sys_prompt, compare_grammar_rule_template
from typing import Optional
from assistants.utility import parse_json_from_text

class CompareGrammarRuleAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=compare_grammar_rule_sys_prompt,
            max_tokens=100,
            parse_json=True
        )

    def build_prompt(
        self,
        grammar_rule_1: str,
        grammar_rule_2: str
    ) -> str:

        return compare_grammar_rule_template.format(
           grammar_rule_1 = grammar_rule_1,
           grammar_rule_2 = grammar_rule_2
        )

    def run(
        self,
        grammar_rule_1: str,
        grammar_rule_2: str,
        verbose: bool = False
    ) -> list[dict] | str:
        return super().run(grammar_rule_1, grammar_rule_2, verbose=verbose)
    
#test_compare_grammar_rule = CompareGrammarRuleAssistant()
#rule1 = "被动语态"
#rule2 = "主动语态"
#test_compare_grammar_rule_response = test_compare_grammar_rule.run(rule1, rule2, verbose=True)