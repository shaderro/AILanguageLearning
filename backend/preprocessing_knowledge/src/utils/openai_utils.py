from openai import OpenAI
from typing import List, Dict, Any, Optional
from . import config

class OpenAIHelper:
    """OpenAI助手类，提供常用的OpenAI操作"""
    
    def __init__(self):
        """初始化OpenAI客户端"""
        try:
            config_dict = config.get_openai_config()
            self.client = OpenAI(
                api_key=config_dict['api_key'],
                base_url=config_dict['base_url']
            )
            self.model = config_dict['model']
        except ValueError as e:
            raise e
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: Optional[int] = None) -> str:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大token数
            
        Returns:
            str: AI的回复内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {e}")
    
    def analyze_text(self, text: str, analysis_type: str = "general") -> str:
        """
        分析文本
        
        Args:
            text: 要分析的文本
            analysis_type: 分析类型 ("general", "sentiment", "grammar", "difficulty")
            
        Returns:
            str: 分析结果
        """
        analysis_prompts = {
            "general": "请分析以下文本，提供简要的总结和见解：",
            "sentiment": "请分析以下文本的情感倾向（积极、消极或中性）：",
            "grammar": "请检查以下文本的语法，指出错误并提供建议：",
            "difficulty": "请评估以下文本的难度级别（简单、中等、困难）："
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        
        messages = [
            {"role": "system", "content": "你是一个专业的文本分析助手。"},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ]
        
        return self.chat_completion(messages)
    
    def get_token_difficulty(self, token: str, context: str = "") -> Dict[str, Any]:
        """
        获取token的难度信息
        
        Args:
            token: 要分析的token
            context: 可选的上下文
            
        Returns:
            Dict[str, Any]: 包含难度信息的字典
        """
        prompt = f"""
        请分析以下单词的难度级别：
        单词: {token}
        上下文: {context if context else "无"}
        
        请以JSON格式返回以下信息：
        {{
            "difficulty_level": "easy/medium/hard",
            "explanation": "难度解释",
            "is_grammar_marker": true/false,
            "suggestions": "学习建议"
        }}
        """
        
        messages = [
            {"role": "system", "content": "你是一个英语教学专家，专门分析单词难度。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.chat_completion(messages, temperature=0.3)
            # 这里可以添加JSON解析逻辑
            return {"raw_response": response}
        except Exception as e:
            return {"error": str(e)}

def test_openai_connection():
    """测试OpenAI连接"""
    try:
        helper = OpenAIHelper()
        response = helper.chat_completion([
            {"role": "user", "content": "Hello, please respond with 'OpenAI connection successful!'"}
        ])
        print("✅ OpenAI连接成功!")
        print(f"回复: {response}")
        return True
    except Exception as e:
        print(f"❌ OpenAI连接失败: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection() 