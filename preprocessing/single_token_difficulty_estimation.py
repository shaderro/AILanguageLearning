from assistants.sub_assistants.sub_assistant import SubAssistant
from assistants.sub_assistants.prompt import difficulty_estimation_system_template_specific_standard, difficulty_estimation_system_template_default, assessment_user_template

class SingleTokenDifficultyEstimator(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=difficulty_estimation_system_template_default.format(language="English"),
            max_tokens=400,
            parse_json=True
        )

    def build_prompt(self, word: str) -> str:
        return assessment_user_template.format(word=word)

    def run(self, word: str, verbose=False) -> str:
        return super().run(word, verbose=verbose)