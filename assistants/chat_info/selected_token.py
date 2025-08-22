#!/usr/bin/env python3
"""
SelectedToken 数据结构
用于记录用户选择的特定token
"""

from dataclasses import dataclass
from typing import List, Optional, Union
from data_managers.data_classes import Sentence
from data_managers.data_classes_new import Sentence as NewSentence

# 类型别名，支持新旧两种句子类型
SentenceType = Union[Sentence, NewSentence]

@dataclass
class SelectedToken:
    """
    用户选择的token信息
    
    Attributes:
        token_indices: 相对于整句话的token索引列表
        token_text: 用户选择的token文本
        sentence_body: 完整的句子文本（用于上下文）
        sentence_id: 句子ID
        text_id: 文章ID
    """
    token_indices: List[int]  # 相对token索引
    token_text: str  # 用户选择的token文本
    sentence_body: str  # 完整句子文本
    sentence_id: int
    text_id: int
    
    def __post_init__(self):
        """验证数据"""
        if not self.token_indices:
            raise ValueError("token_indices不能为空")
        if not self.token_text:
            raise ValueError("token_text不能为空")
        if not self.sentence_body:
            raise ValueError("sentence_body不能为空")
    
    def get_selected_text(self) -> str:
        """获取用户选择的文本"""
        return self.token_text
    
    def get_full_context(self) -> str:
        """获取完整上下文（整句话）"""
        return self.sentence_body
    
    def get_token_count(self) -> int:
        """获取选择的token数量"""
        return len(self.token_indices)
    
    def is_single_token(self) -> bool:
        """是否只选择了一个token"""
        return len(self.token_indices) == 1
    
    def is_full_sentence(self) -> bool:
        """是否选择了整句话"""
        # 简单判断：如果选择的文本长度接近句子长度，认为是整句
        return len(self.token_text.strip()) >= len(self.sentence_body.strip()) * 0.8
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "token_indices": self.token_indices,
            "token_text": self.token_text,
            "sentence_body": self.sentence_body,
            "sentence_id": self.sentence_id,
            "text_id": self.text_id,
            "token_count": self.get_token_count(),
            "is_single_token": self.is_single_token(),
            "is_full_sentence": self.is_full_sentence()
        }
    
    @classmethod
    def from_sentence_and_indices(cls, sentence: SentenceType, token_indices: List[int], token_text: str) -> 'SelectedToken':
        """
        从句子对象和token索引创建SelectedToken
        
        Args:
            sentence: 句子对象（支持新旧两种类型）
            token_indices: token索引列表
            token_text: 用户选择的token文本
            
        Returns:
            SelectedToken: 创建的SelectedToken对象
        """
        return cls(
            token_indices=token_indices,
            token_text=token_text,
            sentence_body=sentence.sentence_body,
            sentence_id=sentence.sentence_id,
            text_id=sentence.text_id
        )
    
    @classmethod
    def from_full_sentence(cls, sentence: SentenceType) -> 'SelectedToken':
        """
        从完整句子创建SelectedToken（用户选择整句话）
        
        Args:
            sentence: 句子对象
            
        Returns:
            SelectedToken: 表示整句话选择的SelectedToken对象
        """
        # 对于整句话选择，我们使用所有token的索引
        # 这里简化处理，使用一个特殊值表示整句选择
        return cls(
            token_indices=[-1],  # -1表示整句选择
            token_text=sentence.sentence_body,
            sentence_body=sentence.sentence_body,
            sentence_id=sentence.sentence_id,
            text_id=sentence.text_id
        )

def create_selected_token_from_text(sentence: SentenceType, selected_text: str) -> SelectedToken:
    """
    从用户选择的文本创建SelectedToken
    
    Args:
        sentence: 句子对象
        selected_text: 用户选择的文本
        
    Returns:
        SelectedToken: 创建的SelectedToken对象
    """
    # 如果选择的文本是整句话，创建整句选择
    if selected_text.strip() == sentence.sentence_body.strip():
        return SelectedToken.from_full_sentence(sentence)
    
    # 否则，需要找到对应的token索引
    # 这里简化处理，实际应用中可能需要更复杂的token匹配逻辑
    words = sentence.sentence_body.split()
    selected_words = selected_text.split()
    
    # 找到选择的词在句子中的位置
    token_indices = []
    for i, word in enumerate(words):
        if word in selected_words:
            token_indices.append(i)
    
    return SelectedToken(
        token_indices=token_indices,
        token_text=selected_text,
        sentence_body=sentence.sentence_body,
        sentence_id=sentence.sentence_id,
        text_id=sentence.text_id
    ) 