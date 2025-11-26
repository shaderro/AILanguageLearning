import time
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError
import httpx
#, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from assistants.utility import parse_json_from_text

class SubAssistant:
    def __init__(self, sys_prompt, max_tokens, parse_json):
        self.client = OpenAI(api_key="sk-4035e2a8e00b48c2a335b8cadbd98979", base_url="https://api.deepseek.com")
        self.sys_prompt = sys_prompt
        self.max_tokens = max_tokens
        self.parse_json = parse_json
        self.model = "deepseek-chat"
        self.max_retries = 3
        self.retry_backoff_seconds = 2

    def run(self, *args, verbose=False, **kwargs) -> dict |list[dict] | str:
        user_prompt = self.build_prompt(*args, **kwargs)
        if verbose:
            print("🧾 Prompt:\n", user_prompt)
    
        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
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
            except (APIConnectionError, APITimeoutError, httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as error:
                last_error = error
                if attempt < self.max_retries:
                    wait = self.retry_backoff_seconds * attempt
                    print(f"⚠️ OpenAI连接失败（第{attempt}次），{wait}s 后重试... 错误: {error}")
                    time.sleep(wait)
                else:
                    print(f"❌ OpenAI连接多次失败，已重试 {self.max_retries} 次。")
                    raise
        # 如果循环结束仍未返回，抛出最后的错误
        raise last_error if last_error else RuntimeError("未知错误：OpenAI调用重试后仍失败")

    def build_prompt(self, *args, **kwargs) -> str:
        """
        子类必须重写此方法构建 prompt。
        """
        raise NotImplementedError("请在子类中实现 build_prompt 方法")

        
    