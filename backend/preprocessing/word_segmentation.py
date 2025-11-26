#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Word segmentation orchestrator.

目前仅支持中文，会在未来扩展到其他非空格语言。
"""

from typing import Any, Dict, List, Optional, Tuple

from .non_space_segmentation import (
    Chinese_sentence_segmentation,
    convert_segments_to_word_tokens,
)


def word_segmentation(
    language_code: Optional[str],
    sentence_text: str,
    sentence_tokens: List[Dict[str, Any]],
    next_word_token_id: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[int, int], int]:
    """
    根据语言执行 word segmentation。

    Args:
        language_code: 语言代码（如 "zh"）
        sentence_text: 当前句子文本
        sentence_tokens: 已生成的字符级 token（含 sentence_token_id）
        next_word_token_id: 可用的全局 word_token_id

    Returns:
        Tuple:
            - word_tokens: 当前句子的 word token 列表
            - token_word_mapping: {sentence_token_id: word_token_id}
            - next_word_token_id: 更新后的全局 word_token_id
    """
    if language_code != "zh":
        return [], {}, next_word_token_id

    segments = Chinese_sentence_segmentation(sentence_text)
    if not segments:
        return [], {}, next_word_token_id

    word_tokens, token_word_mapping, updated_counter = convert_segments_to_word_tokens(
        sentence_tokens,
        segments,
        starting_word_token_id=next_word_token_id,
    )
    return word_tokens, token_word_mapping, updated_counter

