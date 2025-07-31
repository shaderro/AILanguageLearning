#!/usr/bin/env python3
"""
测试数据绑定服务的数据加载功能
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.services.language_learning_binding_service import LanguageLearningBindingService

def test_data_binding_service():
    """测试数据绑定服务"""
    print("🧪 测试数据绑定服务...")
    
    # 创建数据绑定服务
    binding_service = LanguageLearningBindingService()
    
    # 检查数据是否正确加载
    print("\n📊 检查加载的数据:")
    
    # 检查语法数据
    grammar_bundles = binding_service.get_data("grammar_bundles")
    total_grammar_rules = binding_service.get_data("total_grammar_rules")
    grammar_loading = binding_service.get_data("grammar_loading")
    grammar_error = binding_service.get_data("grammar_error")
    
    print(f"   Grammar Bundles: {type(grammar_bundles)}")
    print(f"   Total Grammar Rules: {total_grammar_rules}")
    print(f"   Grammar Loading: {grammar_loading}")
    print(f"   Grammar Error: {grammar_error}")
    
    if grammar_bundles:
        print(f"   Grammar Bundles Count: {len(grammar_bundles)}")
        print("   Grammar Rules:")
        for rule_id, bundle in list(grammar_bundles.items())[:3]:  # 显示前3个
            print(f"     - ID {rule_id}: {bundle.rule.name}")
    else:
        print("   ❌ 没有加载到语法数据")
    
    # 检查词汇数据
    vocab_bundles = binding_service.get_data("vocab_bundles")
    total_vocab_expressions = binding_service.get_data("total_vocab_expressions")
    vocab_loading = binding_service.get_data("vocab_loading")
    vocab_error = binding_service.get_data("vocab_error")
    
    print(f"\n   Vocab Bundles: {type(vocab_bundles)}")
    print(f"   Total Vocab Expressions: {total_vocab_expressions}")
    print(f"   Vocab Loading: {vocab_loading}")
    print(f"   Vocab Error: {vocab_error}")
    
    if vocab_bundles:
        print(f"   Vocab Bundles Count: {len(vocab_bundles)}")
        print("   Vocab Expressions:")
        for vocab_id, bundle in list(vocab_bundles.items())[:3]:  # 显示前3个
            print(f"     - ID {vocab_id}: {bundle.vocab.vocab_body}")
    else:
        print("   ❌ 没有加载到词汇数据")
    
    # 测试数据更新
    print("\n🔄 测试数据更新:")
    binding_service.update_data("test_key", "test_value")
    test_value = binding_service.get_data("test_key")
    print(f"   Test Key: {test_value}")
    
    print("\n✅ 数据绑定服务测试完成")

if __name__ == "__main__":
    test_data_binding_service() 