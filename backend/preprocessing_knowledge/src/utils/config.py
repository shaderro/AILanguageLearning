import os
from typing import Optional

# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

def get_openai_config() -> dict:
    """
    获取OpenAI配置
    
    Returns:
        dict: 包含OpenAI配置的字典
    """
    if not OPENAI_API_KEY:
        raise ValueError("请设置OPENAI_API_KEY环境变量")
    
    return {
        'api_key': OPENAI_API_KEY,
        'base_url': OPENAI_BASE_URL,
        'model': OPENAI_MODEL
    }

def check_openai_setup() -> bool:
    """
    检查OpenAI配置是否正确设置
    
    Returns:
        bool: 配置是否正确
    """
    try:
        get_openai_config()
        return True
    except ValueError:
        return False 