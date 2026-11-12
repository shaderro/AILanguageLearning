#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.text_processor import TextProcessor

def verify_processing():
    """验证5句话文章的处理结果"""
    
    print("🔍 验证5句话文章的处理结果")
    print("=" * 50)
    
    # 检查生成的文件
    output_dir = "data/text_001"
    files_to_check = ["original_texts.json", "sentences.json", "tokens.json"]
    
    print("📋 检查生成的文件")
    print("-" * 30)
    
    for filename in files_to_check:
        file_path = os.path.join(output_dir, filename)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {filename}: {size:,} bytes")
        else:
            print(f"❌ {filename}: 文件不存在")
    
    # 读取并分析数据
    print(f"\n📊 数据分析")
    print("-" * 30)
    
    # 读取original_texts.json
    with open(os.path.join(output_dir, "original_texts.json"), 'r', encoding='utf-8') as f:
        original_texts = json.load(f)
    
    print(f"📄 文本信息:")
    print(f"   - 文本ID: {original_texts['text_id']}")
    print(f"   - 标题: {original_texts['text_title']}")
    print(f"   - 句子数量: {len(original_texts['sentence_ids'])}")
    print(f"   - 句子ID列表: {original_texts['sentence_ids']}")
    
    # 读取sentences.json
    with open(os.path.join(output_dir, "sentences.json"), 'r', encoding='utf-8') as f:
        sentences = json.load(f)
    
    print(f"\n📝 句子分析:")
    print(f"   - 句子数量: {len(sentences)}")
    total_tokens = 0
    for i, sentence in enumerate(sentences, 1):
        token_count = len(sentence['token_ids'])
        total_tokens += token_count
        print(f"   - 句子 {i}: {token_count} 个tokens")
        print(f"     内容: {sentence['sentence_body'][:50]}...")
    
    # 读取tokens.json
    with open(os.path.join(output_dir, "tokens.json"), 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    print(f"\n🔤 Token分析:")
    print(f"   - 总Token数量: {len(tokens)}")
    print(f"   - 计算Token数量: {total_tokens}")
    
    # 验证数据一致性
    print(f"\n🔍 数据一致性验证")
    print("-" * 30)
    
    # 验证句子ID一致性
    original_sentence_ids = set(original_texts['sentence_ids'])
    sentence_ids_from_sentences = set(s['sentence_id'] for s in sentences)
    
    if original_sentence_ids == sentence_ids_from_sentences:
        print("✅ 句子ID一致性验证通过")
    else:
        print("❌ 句子ID一致性验证失败")
    
    # 验证token ID一致性
    all_token_ids_from_sentences = set()
    for sentence in sentences:
        all_token_ids_from_sentences.update(sentence['token_ids'])
    
    token_ids_from_tokens = set(t['token_id'] for t in tokens)
    
    if all_token_ids_from_sentences == token_ids_from_tokens:
        print("✅ Token ID一致性验证通过")
    else:
        print("❌ Token ID一致性验证失败")
    
    # 验证token数量一致性
    if len(tokens) == total_tokens:
        print("✅ Token数量一致性验证通过")
    else:
        print("❌ Token数量一致性验证失败")
        print(f"   Tokens文件: {len(tokens)}")
        print(f"   计算总数: {total_tokens}")
    
    # 显示一些token示例
    print(f"\n📋 Token示例")
    print("-" * 30)
    
    # 显示前10个token
    for i, token in enumerate(tokens[:10]):
        print(f"   {i+1:2d}. ID={token['token_id']:3d}, Body='{token['token_body']}', Type={token['token_type']}")
    
    # 显示不同类型的token统计
    token_types = {}
    for token in tokens:
        token_type = token['token_type']
        token_types[token_type] = token_types.get(token_type, 0) + 1
    
    print(f"\n📊 Token类型统计")
    print("-" * 30)
    for token_type, count in token_types.items():
        print(f"   {token_type}: {count} 个")
    
    print(f"\n🎉 验证完成！")

if __name__ == "__main__":
    verify_processing() 