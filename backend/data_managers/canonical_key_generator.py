#!/usr/bin/env python3
"""
Canonical Key 生成器

用于生成语法规则的规范化键值，格式：language::category::subtype
规则：
- 所有值转换为 lowercase
- 使用 snake_case 格式
- 拼接格式：language::category::subtype
- 任何非法值直接 reject
"""
import re
from typing import Optional


def _normalize_language_name(language: str) -> str:
    """
    将语言名称转换为英文代码
    
    支持的语言映射：
    - 中文/Chinese -> chinese
    - 英文/English -> english
    - 德文/German/Deutsch -> german
    - 日文/Japanese -> japanese
    - 法文/French -> french
    - 西班牙文/Spanish -> spanish
    
    Args:
        language: 语言名称（中文或英文）
    
    Returns:
        英文语言代码（小写）
    """
    if not language:
        return ""
    
    language_lower = language.lower().strip()
    
    # 语言名称映射表
    language_map = {
        # 中文名称
        "中文": "chinese",
        "英文": "english",
        "德文": "german",
        "日文": "japanese",
        "法文": "french",
        "西班牙文": "spanish",
        "西班牙语": "spanish",
        # 英文名称
        "chinese": "chinese",
        "english": "english",
        "german": "german",
        "deutsch": "german",
        "japanese": "japanese",
        "french": "french",
        "spanish": "spanish",
    }
    
    # 先尝试直接匹配
    if language_lower in language_map:
        return language_map[language_lower]
    
    # 如果不在映射表中，尝试转换为 snake_case（仅英文）
    return _to_snake_case_english_only(language)


def _to_snake_case_english_only(value: str) -> str:
    """
    将字符串转换为 snake_case 格式（仅英文字母、数字、下划线）
    
    规则：
    - 转换为小写
    - 将空格、连字符、点等替换为下划线
    - 移除所有非英文字母、数字、下划线的字符
    - 移除连续的下划线
    - 移除首尾下划线
    
    注意：不允许中文字符，只保留英文字母、数字和下划线
    """
    if not value:
        return ""
    
    # 去除首尾空白
    value = value.strip()
    
    if not value:
        return ""
    
    # 转换为小写
    value = value.lower()
    
    # 将空格、连字符、点、逗号等分隔符替换为下划线
    value = re.sub(r'[\s\-.,;:!?()\[\]{}]+', '_', value)
    
    # 只保留英文字母、数字、下划线，移除其他所有字符（包括中文）
    value = re.sub(r'[^a-z0-9_]', '', value)
    
    # 移除连续的下划线
    value = re.sub(r'_+', '_', value)
    
    # 移除首尾下划线
    value = value.strip('_')
    
    return value


def _to_snake_case(value: str) -> str:
    """
    将字符串转换为 snake_case 格式（用于 category 和 subtype，允许英文）
    
    规则：
    - 转换为小写
    - 将空格、连字符、点等替换为下划线
    - 只保留英文字母、数字、下划线
    - 移除连续的下划线
    - 移除首尾下划线
    """
    return _to_snake_case_english_only(value)


def _validate_value(value: Optional[str], field_name: str, is_language: bool = False) -> str:
    """
    验证并清理输入值
    
    Args:
        value: 输入值
        field_name: 字段名称（用于错误信息）
        is_language: 是否为语言字段（如果是，会进行语言名称转换）
    
    Returns:
        清理后的值（snake_case, lowercase，仅英文字母、数字、下划线）
    
    Raises:
        ValueError: 如果值为非法
    """
    if value is None:
        raise ValueError(f"{field_name} 不能为 None")
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name} 必须是字符串类型，当前类型: {type(value).__name__}")
    
    # 去除首尾空白
    value = value.strip()
    
    if not value:
        raise ValueError(f"{field_name} 不能为空字符串")
    
    # 如果是语言字段，先进行语言名称转换
    if is_language:
        value = _normalize_language_name(value)
        if not value:
            raise ValueError(f"{field_name} 语言名称无法识别或转换")
    else:
        # 转换为 snake_case（仅英文）
        value = _to_snake_case(value)
    
    if not value:
        raise ValueError(f"{field_name} 转换后为空（可能只包含非法字符）")
    
    # 验证只包含英文字母、数字、下划线（不允许中文）
    if not re.match(r'^[a-z0-9_]+$', value):
        raise ValueError(f"{field_name} 包含非法字符（只允许英文字母、数字、下划线）")
    
    return value


def generate_canonical_key(
    language: Optional[str],
    category: Optional[str],
    subtype: Optional[str]
) -> str:
    """
    生成 canonical_key
    
    格式：language::category::subtype
    
    规则：
    - 所有值转换为 lowercase
    - 使用 snake_case 格式
    - 只允许英文字母、数字、下划线（不允许中文字符）
    - 语言名称会自动转换为英文代码（如"英文" -> "english"）
    - 任何非法值直接 reject（抛出 ValueError）
    
    Args:
        language: 语言（如 "德文", "英文", "中文", "English", "German"）
        category: 类别（如 "clause", "phrase"）
        subtype: 子类型（如 "relative_clause", "noun_phrase"）
    
    Returns:
        canonical_key 字符串，格式：language::category::subtype（全部英文）
    
    Raises:
        ValueError: 如果任何参数为非法值
    
    Examples:
        >>> generate_canonical_key("德文", "clause", "relative_clause")
        'german::clause::relative_clause'
        
        >>> generate_canonical_key("英文", "clause", "relative_clause")
        'english::clause::relative_clause'
        
        >>> generate_canonical_key("English", "clause", "relative_clause")
        'english::clause::relative_clause'
    """
    # 验证并转换每个参数
    # language 字段需要特殊处理（转换为英文代码）
    language_clean = _validate_value(language, "language", is_language=True)
    category_clean = _validate_value(category, "category", is_language=False)
    subtype_clean = _validate_value(subtype, "subtype", is_language=False)
    
    # 拼接为 canonical_key 格式
    canonical_key = f"{language_clean}::{category_clean}::{subtype_clean}"
    
    return canonical_key


# 便捷函数：从 GrammarRule 对象生成
def generate_canonical_key_from_rule(
    canonical_category: Optional[str],
    canonical_subtype: Optional[str],
    language: Optional[str] = None
) -> Optional[str]:
    """
    从语法规则对象生成 canonical_key（如果缺少必要字段则返回 None）
    
    Args:
        canonical_category: 规范化类别
        canonical_subtype: 规范化子类型
        language: 语言（可选，如果为 None 则返回 None）
    
    Returns:
        canonical_key 字符串，如果缺少必要字段则返回 None
    """
    if not canonical_category or not canonical_subtype or not language:
        return None
    
    try:
        return generate_canonical_key(language, canonical_category, canonical_subtype)
    except ValueError:
        # 如果验证失败，返回 None（而不是抛出异常）
        return None

