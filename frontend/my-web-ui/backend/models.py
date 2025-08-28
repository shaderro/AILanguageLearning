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
    examples: List[str]
    source: str
    is_starred: bool


# 统一响应模型
class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    status: Literal["success", "error"]
    data: Optional[Union[Dict[str, Any], List[Any], Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
