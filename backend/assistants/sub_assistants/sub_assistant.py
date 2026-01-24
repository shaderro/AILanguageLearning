import time
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError
import httpx
from typing import Optional
from sqlalchemy.orm import Session
#, Sentence, GrammarRule, GrammarExample, GrammarBundle, VocabExpression, VocabExpressionExample
from backend.assistants.utility import parse_json_from_text

class SubAssistant:
    def __init__(self, sys_prompt, max_tokens, parse_json):
        # 从统一配置模块导入 API Key
        try:
            from backend.config import OPENAI_API_KEY
            api_key = OPENAI_API_KEY
        except ImportError:
            # 如果导入失败，直接从环境变量读取（向后兼容）
            import os
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("⚠️ OPENAI_API_KEY 环境变量未设置！请在 .env 文件中设置 OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.sys_prompt = sys_prompt
        self.max_tokens = max_tokens
        self.parse_json = parse_json
        self.model = "deepseek-chat"
        self.max_retries = 3
        self.retry_backoff_seconds = 2

    def run(
        self, 
        *args, 
        verbose=False, 
        user_id: Optional[int] = None,
        session: Optional[Session] = None,
        **kwargs
    ) -> dict |list[dict] | str:
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
                
                # ⚠️ 重要：在 API 调用成功后，立即记录 token 使用并扣减
                # 必须在处理响应内容之前完成，确保即使后续处理失败，token 也已正确扣减
                if user_id is not None and session is not None:
                    try:
                        # 从 response.usage 中读取真实 token 使用量
                        usage = response.usage
                        if usage:
                            total_tokens = usage.total_tokens
                            prompt_tokens = usage.prompt_tokens
                            completion_tokens = usage.completion_tokens
                            
                            # 调用 token 服务记录使用并扣减
                            from backend.services.token_service import record_token_usage
                            # 🔧 获取当前 SubAssistant 的类名（用于详细统计）
                            assistant_name = self.__class__.__name__
                            token_result = record_token_usage(
                                session=session,
                                user_id=user_id,
                                total_tokens=total_tokens,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                model_name=self.model,
                                assistant_name=assistant_name
                            )
                            
                            # 提交事务（确保 token 扣减和日志记录已保存）
                            session.commit()
                            
                            # 📊 后端日志输出（用于调试和排查成本异常）
                            print(f"💰 [Token Usage] user_id={user_id} | model={self.model} | "
                                  f"prompt_tokens={prompt_tokens} | completion_tokens={completion_tokens} | "
                                  f"total_tokens={total_tokens} | balance_after={token_result['token_balance_after']}")
                        else:
                            print(f"⚠️ [Token Usage] API 响应中未包含 usage 信息，跳过 token 扣减")
                    except Exception as token_error:
                        # Token 记录失败不应该影响 API 响应，但需要记录错误
                        print(f"❌ [Token Usage] 记录 token 使用失败: {token_error}")
                        import traceback
                        traceback.print_exc()
                        # 回滚 token 相关的事务
                        session.rollback()
                
                # 🔧 详细记录原始响应
                raw_content = response.choices[0].message.content
                print(f"🔍 [SubAssistant] 原始响应内容（strip前）: {repr(raw_content)}")
                print(f"🔍 [SubAssistant] 原始响应内容长度: {len(raw_content) if raw_content else 0}")
                
                content = raw_content.strip() if raw_content else ""
                print(f"🔍 [SubAssistant] strip后的内容: {repr(content)}")
                print(f"🔍 [SubAssistant] strip后的内容长度: {len(content)}")
                
                if verbose:
                    print("📬 Raw Response:\n", content)
                
                # 🔧 检查返回内容是否为空
                if not content:
                    print(f"⚠️ [SubAssistant] AI 返回内容为空（第{attempt}次尝试）")
                    if attempt < self.max_retries:
                        print(f"🔄 [SubAssistant] 将进行第 {attempt + 1} 次重试...")
                        continue  # 继续重试循环
                    else:
                        print(f"❌ [SubAssistant] AI 返回空内容，已重试 {self.max_retries} 次，返回空字符串")
                        return content  # 返回空字符串
                
                if self.parse_json:
                    print(f"🔍 [SubAssistant] 准备解析 JSON，内容: {repr(content[:200]) if content else '(空)'}")
                    #print("📬 Parsing JSON from response...")
                    parsed = parse_json_from_text(content)
                    print(f"🔍 [SubAssistant] JSON 解析结果: {type(parsed)}, 值: {parsed}")
                    if parsed is None:
                        # 🔧 JSON 解析失败，返回原始文本（而不是 None）
                        print(f"⚠️ [SubAssistant] JSON 解析失败，原始内容: {content[:100] if content else '(空)'}")
                        if not content:
                            # 如果是空内容且 JSON 解析失败，尝试重试
                            if attempt < self.max_retries:
                                print(f"🔄 [SubAssistant] 内容为空且JSON解析失败，将进行第 {attempt + 1} 次重试...")
                                continue
                        print(f"🔍 [SubAssistant] 返回原始内容: {repr(content)}")
                        return content
                    print(f"🔍 [SubAssistant] JSON 解析成功，返回: {type(parsed)}, 值: {parsed}")
                    return parsed
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

        
    