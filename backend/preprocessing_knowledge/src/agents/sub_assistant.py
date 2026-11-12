import os
from openai import OpenAI
#, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from ..utils.utility import parse_json_from_text

class SubAssistant:
    def __init__(self, sys_prompt, max_tokens, parse_json):
        self.client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
        self.sys_prompt = sys_prompt
        self.max_tokens = max_tokens
        self.parse_json = parse_json
        self.model = "deepseek-chat"

    def run(self, *args, verbose=False, **kwargs) -> dict |list[dict] | str:
        user_prompt = self.build_prompt(*args, **kwargs)
        if verbose:
            print("🧾 Prompt:\n", user_prompt)
    
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens
        )
        content = response.choices[0].message.content.strip()
        if verbose:
            print("📬 Raw Response:\n", content)
        if self.parse_json:
            #print("📬 Parsing JSON from response...")
            return parse_json_from_text(content)
        return content

    def build_prompt(self, *args, **kwargs) -> str:
        """
        子类必须重写此方法构建 prompt。
        """
        raise NotImplementedError("请在子类中实现 build_prompt 方法")

        
    