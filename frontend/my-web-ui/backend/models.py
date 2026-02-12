from pydantic import BaseModel
from typing import List, Optional, Literal, Union, Dict, Any


# 业务模型
class VocabExample(BaseModel):
    """词汇例句模型"""
    vocab_id: int
    text_id: int
    sentence_id: int
    context_explanation: str
    token_indices: List[int]


class GrammarExample(BaseModel):
    """语法例句模型"""
    rule_id: int
    text_id: int
    sentence_id: int
    explanation_context: str


class Vocab(BaseModel):
    """词汇模型"""
    vocab_id: int
    vocab_body: str
    explanation: str
    examples: List[VocabExample]
    source: str
    is_starred: bool


class GrammarRule(BaseModel):
    """语法规则模型"""
    rule_id: int
    rule_name: str
    rule_summary: str
    # 展示用名称（可选，兼容旧字段 rule_name）
    display_name: Optional[str] = None
    # 规范化语法分类信息（可选）
    canonical_category: Optional[str] = None
    canonical_subtype: Optional[str] = None
    canonical_function: Optional[str] = None
    canonical_key: Optional[str] = None
    examples: List[GrammarExample]  # 修复：应该是对象列表，不是字符串列表
    source: str
    is_starred: bool


# 统一响应模型
class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    status: Literal["success", "error"]
    data: Optional[Union[Dict[str, Any], List[Any], Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
