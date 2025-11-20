#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语言分类标准
用于区分需要不同分词策略的语言

当用户上传文章并选择语言后，系统会根据语言分类来决定使用哪种分词/分割策略。
"""

# =====================================================================
# 1. WHITESPACE LANGUAGES (默认情况)
# =====================================================================
# 这些语言使用自然空格分隔单词
#
# 对于这些语言：
# - 以空格分割作为主要分词方式
# - 根据需要应用标准化、词形还原、词性标注等
# - 不使用单字符分词
# - 使用 token = word
# - 支持多词表达式，但基本单位仍然是单词

WHITESPACE_LANGUAGES = {
    "en",  # English
    "de",  # German
    "fr",  # French
    "es",  # Spanish
    "it",  # Italian
    "pt",  # Portuguese
    "ru",  # Russian
    "uk",  # Ukrainian
    "pl",  # Polish
    "cs",  # Czech
    "sv",  # Swedish
    "no",  # Norwegian
    "da",  # Danish
    "ar",  # Arabic
    "fa",  # Persian/Farsi
    "he",  # Hebrew
    "hi",  # Hindi
    "bn",  # Bengali
    "ur",  # Urdu
    "tr",  # Turkish
    "az",  # Azerbaijani
    "uz",  # Uzbek
    "id",  # Indonesian
    "ms",  # Malay
    "vi",  # Vietnamese
    "ko",  # Korean
    "nl",  # Dutch
    "ro",  # Romanian
    "el",  # Greek
    "sw",  # Swahili
    "zu",  # Zulu
    "xh",  # Xhosa
    "af",  # Afrikaans
    "hu",  # Hungarian
    "fi",  # Finnish
    "et",  # Estonian
}

# =====================================================================
# 2. NON-WHITESPACE LANGUAGES (需要分词)
# =====================================================================
# 这些语言不使用空格来分隔单词

NON_WHITESPACE_LANGUAGES = {
    "zh",  # Chinese (中文)
    "ja",  # Japanese (日语 - 假名+汉字，需要分词)
    "th",  # Thai (泰语)
    "lo",  # Lao (老挝语)
    "km",  # Khmer / Cambodian (高棉语/柬埔寨语)
    "my",  # Burmese (缅甸语)
}

# =====================================================================
# 辅助函数
# =====================================================================

def is_whitespace_language(language_code: str) -> bool:
    """
    判断指定语言代码是否为空格分隔语言
    
    Args:
        language_code: 语言代码（ISO 639-1 格式，如 "en", "zh"）
        
    Returns:
        bool: True 如果是空格分隔语言，False 如果是非空格分隔语言
              如果语言代码不在任何分类中，默认返回 True（空格分隔）
    """
    if not language_code:
        return True  # 默认使用空格分隔
    
    language_code = language_code.lower().strip()
    
    # 检查是否为非空格分隔语言
    if language_code in NON_WHITESPACE_LANGUAGES:
        return False
    
    # 默认返回 True（空格分隔）
    return True


def is_non_whitespace_language(language_code: str) -> bool:
    """
    判断指定语言代码是否为非空格分隔语言
    
    Args:
        language_code: 语言代码（ISO 639-1 格式，如 "zh", "ja"）
        
    Returns:
        bool: True 如果是非空格分隔语言，False 如果是空格分隔语言
    """
    if not language_code:
        return False
    
    language_code = language_code.lower().strip()
    return language_code in NON_WHITESPACE_LANGUAGES


def get_language_category(language_code: str) -> str:
    """
    获取语言的分类类型
    
    Args:
        language_code: 语言代码（ISO 639-1 格式）
        
    Returns:
        str: "whitespace" 或 "non_whitespace"
    """
    if is_non_whitespace_language(language_code):
        return "non_whitespace"
    return "whitespace"


# =====================================================================
# 语言代码映射（用于将中文语言名称转换为ISO代码）
# =====================================================================

# 中文语言名称到ISO代码的映射
LANGUAGE_NAME_TO_CODE = {
    "中文": "zh",
    "英文": "en",
    "德文": "de",
    "法文": "fr",
    "西班牙文": "es",
    "意大利文": "it",
    "葡萄牙文": "pt",
    "俄文": "ru",
    "日文": "ja",
    "韩文": "ko",
    "泰文": "th",
    "越南文": "vi",
    # 可以根据需要添加更多映射
}

def get_language_code(language_name: str) -> str:
    """
    将中文语言名称转换为ISO语言代码
    
    Args:
        language_name: 语言名称（如 "中文", "英文", "德文"）
        
    Returns:
        str: ISO 639-1 语言代码（如 "zh", "en", "de"）
             如果找不到映射，返回原始字符串的小写形式
    """
    if not language_name:
        return ""
    
    # 先尝试直接查找
    code = LANGUAGE_NAME_TO_CODE.get(language_name)
    if code:
        return code
    
    # 如果找不到，返回小写形式（可能已经是代码）
    return language_name.lower().strip()

