#!/usr/bin/env python3
"""
为测试环境创建测试数据

根据之前的检查结果，测试环境应该有3个vocab和2个grammar
"""

import sys
import os
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from sqlalchemy import text


def create_test_data():
    """创建测试数据"""
    print("\n" + "="*60)
    print("为测试环境创建测试数据")
    print("="*60)
    
    db_manager = DatabaseManager('testing')
    session = db_manager.get_session()
    
    try:
        # 创建测试数据
        print(f"\n📝 创建测试数据...")
        
        # 创建词汇
        vocabs = [
            {
                'vocab_id': 1,
                'vocab_body': 'test',
                'explanation': '这是一个测试词汇',
                'source': 'manual',
                'is_starred': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            },
            {
                'vocab_id': 2,
                'vocab_body': 'challenging',
                'explanation': '形容词，表示具有挑战性的、困难的',
                'source': 'auto',
                'is_starred': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            },
            {
                'vocab_id': 3,
                'vocab_body': 'component',
                'explanation': '名词，表示组成部分、要素、组件',
                'source': 'auto',
                'is_starred': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            },
        ]
        
        print(f"   📚 创建 {len(vocabs)} 条词汇...")
        imported_count = 0
        for v in vocabs:
            try:
                session.execute(text("""
                    INSERT INTO vocab_expressions 
                    (vocab_id, user_id, vocab_body, explanation, language, source, is_starred, created_at, updated_at)
                    VALUES (:vocab_id, 1, :vocab_body, :explanation, '德文', :source, :is_starred, :created_at, :updated_at)
                """), {
                    'vocab_id': v['vocab_id'],
                    'vocab_body': v['vocab_body'],
                    'explanation': v['explanation'],
                    'source': v['source'],
                    'is_starred': v['is_starred'],
                    'created_at': v['created_at'],
                    'updated_at': v['updated_at'],
                })
                imported_count += 1
            except Exception as e:
                print(f"   ⚠️  创建词汇 {v['vocab_id']} 时出错: {e}")
        
        session.commit()
        print(f"   ✅ 成功创建 {imported_count}/{len(vocabs)} 条词汇")
        
        # 创建语法规则
        grammar_rules = [
            {
                'rule_id': 1,
                'rule_name': '德语定冠词变化',
                'rule_summary': '德语定冠词根据名词的性、数、格发生变化',
                'source': 'manual',
                'is_starred': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            },
            {
                'rule_id': 2,
                'rule_name': '德语形容词词尾变化',
                'rule_summary': '德语形容词在名词前需要根据名词的性、数、格变化词尾',
                'source': 'manual',
                'is_starred': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            },
        ]
        
        print(f"   📖 创建 {len(grammar_rules)} 条语法规则...")
        imported_count = 0
        for g in grammar_rules:
            try:
                session.execute(text("""
                    INSERT INTO grammar_rules 
                    (rule_id, user_id, rule_name, rule_summary, language, source, is_starred, created_at, updated_at)
                    VALUES (:rule_id, 1, :rule_name, :rule_summary, '德文', :source, :is_starred, :created_at, :updated_at)
                """), {
                    'rule_id': g['rule_id'],
                    'rule_name': g['rule_name'],
                    'rule_summary': g['rule_summary'],
                    'source': g['source'],
                    'is_starred': g['is_starred'],
                    'created_at': g['created_at'],
                    'updated_at': g['updated_at'],
                })
                imported_count += 1
            except Exception as e:
                print(f"   ⚠️  创建语法规则 {g['rule_id']} 时出错: {e}")
        
        session.commit()
        print(f"   ✅ 成功创建 {imported_count}/{len(grammar_rules)} 条语法规则")
        
        session.close()
        
        # 验证数据
        print(f"\n🔍 验证数据...")
        session = db_manager.get_session()
        
        vocab_count_result = session.execute(text("SELECT COUNT(*) FROM vocab_expressions")).fetchone()
        vocab_count = vocab_count_result[0] if vocab_count_result else 0
        
        grammar_count_result = session.execute(text("SELECT COUNT(*) FROM grammar_rules")).fetchone()
        grammar_count = grammar_count_result[0] if grammar_count_result else 0
        
        print(f"   📊 词汇: {vocab_count} 条")
        print(f"   📊 语法规则: {grammar_count} 条")
        
        # 检查user_id和language
        vocab_user_count_result = session.execute(text("SELECT COUNT(*) FROM vocab_expressions WHERE user_id = 1 AND language = '德文'")).fetchone()
        vocab_user_count = vocab_user_count_result[0] if vocab_user_count_result else 0
        
        grammar_user_count_result = session.execute(text("SELECT COUNT(*) FROM grammar_rules WHERE user_id = 1 AND language = '德文'")).fetchone()
        grammar_user_count = grammar_user_count_result[0] if grammar_user_count_result else 0
        
        print(f"   📊 user_id=1, language=德文的词汇: {vocab_user_count} 条")
        print(f"   📊 user_id=1, language=德文的语法规则: {grammar_user_count} 条")
        
        session.close()
        
        if vocab_count == 3 and grammar_count == 2:
            print(f"\n✅ 测试数据创建成功！")
            return True
        else:
            print(f"\n⚠️  测试数据创建不完整")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"❌ 创建测试数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    print("\n" + "="*60)
    print("为测试环境创建测试数据")
    print("="*60)
    print("\n📋 此脚本将：")
    print("  1. 创建3个词汇（user_id=1, language=德文）")
    print("  2. 创建2个语法规则（user_id=1, language=德文）")
    print("  3. 验证数据创建结果")
    
    if create_test_data():
        print("\n✅ 测试数据创建成功！")
    else:
        print("\n❌ 测试数据创建失败")


if __name__ == "__main__":
    main()

