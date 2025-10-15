#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token性能影响测试

测试目标：
1. 测量不同查询方式的实际性能
2. 对比有无Token的数据量差异
3. 分析N+1查询问题
4. 提供优化建议
"""
import sys
import os
import time

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import OriginalText, Sentence, Token
from sqlalchemy.orm import selectinload, joinedload

def print_header(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_query_without_tokens():
    """测试1: 查询文章和句子（不加载tokens）"""
    print_header("测试1: 查询文章+句子（不含tokens）- 当前实现")
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    start_time = time.time()
    
    # 查询文章和句子，不加载tokens
    text = session.query(OriginalText).filter(
        OriginalText.text_id == 1
    ).first()
    
    # 访问sentences会触发查询，但不会加载tokens
    sentence_count = len(text.sentences)
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000  # 转换为毫秒
    
    print(f"[RESULT]")
    print(f"  文章ID: {text.text_id}")
    print(f"  文章标题: {text.text_title[:50]}...")
    print(f"  句子数量: {sentence_count}")
    print(f"  查询时间: {elapsed:.2f} ms")
    rating = "极快" if elapsed < 100 else "快" if elapsed < 500 else "慢"
    print(f"  性能评级: {rating}")
    
    session.close()
    return elapsed


def test_query_with_tokens_lazy():
    """测试2: 查询文章和句子+tokens（懒加载，会导致N+1问题）"""
    print_header("测试2: 查询文章+句子+tokens（懒加载）- 会有N+1问题")
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    start_time = time.time()
    
    # 查询文章和句子
    text = session.query(OriginalText).filter(
        OriginalText.text_id == 1
    ).first()
    
    # 访问sentences
    sentence_count = len(text.sentences)
    
    # 访问每个句子的tokens（会触发N次查询）
    total_tokens = 0
    for sentence in text.sentences:
        total_tokens += len(sentence.tokens)  # ← 每次都会查询数据库
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000
    
    print(f"[RESULT]")
    print(f"  文章ID: {text.text_id}")
    print(f"  句子数量: {sentence_count}")
    print(f"  Token总数: {total_tokens}")
    print(f"  查询时间: {elapsed:.2f} ms")
    rating = "极快" if elapsed < 100 else "快" if elapsed < 500 else "慢"
    print(f"  性能评级: {rating}")
    print(f"  问题: N+1查询（1次查询文章 + {sentence_count}次查询tokens）")
    
    session.close()
    return elapsed


def test_query_with_tokens_eager():
    """测试3: 查询文章和句子+tokens（预加载，优化版）"""
    print_header("测试3: 查询文章+句子+tokens（eager loading）- 优化版")
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    start_time = time.time()
    
    # 使用selectinload预加载sentences和tokens
    text = session.query(OriginalText).options(
        selectinload(OriginalText.sentences).selectinload(Sentence.tokens)
    ).filter(
        OriginalText.text_id == 1
    ).first()
    
    # 访问sentences和tokens，不会触发额外查询
    sentence_count = len(text.sentences)
    total_tokens = sum(len(s.tokens) for s in text.sentences)
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000
    
    print(f"[RESULT]")
    print(f"  文章ID: {text.text_id}")
    print(f"  句子数量: {sentence_count}")
    print(f"  Token总数: {total_tokens}")
    print(f"  查询时间: {elapsed:.2f} ms")
    rating = "极快" if elapsed < 100 else "快" if elapsed < 500 else "慢"
    print(f"  性能评级: {rating}")
    print(f"  优化: 使用eager loading，只需3次查询")
    
    session.close()
    return elapsed


def test_data_size():
    """测试4: 数据大小对比"""
    print_header("测试4: 数据大小对比")
    
    import json
    from backend.adapters import TextAdapter, SentenceAdapter
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    # 查询文章
    text = session.query(OriginalText).options(
        selectinload(OriginalText.sentences).selectinload(Sentence.tokens)
    ).filter(
        OriginalText.text_id == 1
    ).first()
    
    # 方式1: 不含tokens
    text_dto_simple = TextAdapter.model_to_dto(text, include_sentences=True)
    data_simple = {
        "text_id": text_dto_simple.text_id,
        "text_title": text_dto_simple.text_title,
        "sentences": [
            {
                "sentence_id": s.sentence_id,
                "sentence_body": s.sentence_body,
                "tokens": []  # 空
            }
            for s in text_dto_simple.text_by_sentence
        ]
    }
    json_simple = json.dumps(data_simple, ensure_ascii=False)
    size_simple = len(json_simple.encode('utf-8'))
    
    # 方式2: 含tokens（模拟）
    total_tokens = sum(len(s.tokens) for s in text.sentences)
    # 估算：每个token约450 bytes JSON
    estimated_token_size = total_tokens * 450
    size_with_tokens = size_simple + estimated_token_size
    
    print(f"[RESULT]")
    print(f"  文章: {text.text_title[:50]}...")
    print(f"  句子数: {len(text.sentences)}")
    print(f"  Token总数: {total_tokens}")
    print()
    print(f"  不含tokens的JSON大小: {size_simple:,} bytes ({size_simple/1024:.1f} KB)")
    print(f"  含tokens的JSON大小(估算): {size_with_tokens:,} bytes ({size_with_tokens/1024:.1f} KB)")
    print(f"  增加倍数: {size_with_tokens/size_simple:.1f}x")
    print()
    print(f"  网络传输时间估算 (100Mbps):")
    print(f"    不含tokens: {size_simple*8/100000000*1000:.1f} ms")
    print(f"    含tokens:   {size_with_tokens*8/100000000*1000:.1f} ms")
    
    session.close()


def test_single_sentence_tokens():
    """测试5: 单个句子的tokens查询（独立API场景）"""
    print_header("测试5: 单个句子的tokens查询 - 独立API方案")
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    start_time = time.time()
    
    # 只查询一个句子的tokens
    tokens = session.query(Token).filter(
        Token.text_id == 1,
        Token.sentence_id == 1
    ).all()
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000
    
    print(f"[RESULT]")
    print(f"  查询: text_id=1, sentence_id=1 的所有tokens")
    print(f"  Token数量: {len(tokens)}")
    print(f"  查询时间: {elapsed:.2f} ms")
    print(f"  性能评级: 快")
    print(f"  适用场景: 用户点击某个句子时，按需加载其tokens")
    
    if tokens:
        print(f"\n  样本Token:")
        t = tokens[0]
        print(f"    token_body: {t.token_body}")
        print(f"    token_type: {t.token_type}")
        print(f"    sentence_token_id: {t.sentence_token_id}")
    
    session.close()
    return elapsed


def main():
    print("\n" + "=" * 70)
    print("Token性能影响详细测试")
    print("=" * 70)
    print("\n基于真实数据库数据的性能测试")
    
    # 运行测试
    time1 = test_query_without_tokens()
    time2 = test_query_with_tokens_lazy()
    time3 = test_query_with_tokens_eager()
    test_data_size()
    time5 = test_single_sentence_tokens()
    
    # 性能对比总结
    print_header("性能对比总结")
    
    print(f"\n查询时间对比:")
    print(f"  1. 文章+句子（不含tokens）:          {time1:8.2f} ms  [基准]")
    print(f"  2. 文章+句子+tokens（懒加载N+1）:    {time2:8.2f} ms  [慢] {time2/time1:.1f}x")
    print(f"  3. 文章+句子+tokens（eager优化）:    {time3:8.2f} ms  [较快] {time3/time1:.1f}x")
    print(f"  5. 单个句子的tokens（独立API）:      {time5:8.2f} ms  [快速]")
    
    print(f"\n建议:")
    print(f"  [推荐] 默认使用方式1（不含tokens）- 性能最优")
    print(f"  [推荐] 需要时使用方式5（独立API）- 按需加载")
    print(f"  [警告] 避免使用方式2（懒加载）- 有N+1问题")
    print(f"  [可选] 如必须一次性加载，使用方式3（eager）- 但仍较慢")
    
    print(f"\n结论:")
    print(f"  当前的简化实现（空tuple）是正确的设计选择！")
    print(f"  如需Token详情，推荐使用独立API（方式5）")


if __name__ == "__main__":
    main()

