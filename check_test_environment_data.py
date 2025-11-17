#!/usr/bin/env python3
"""
检查测试环境的详细数据
"""
import sys
import os
import sqlite3

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.data_storage.config.config import DB_FILES


def check_test_environment_data():
    """检查测试环境数据"""
    print("\n" + "="*60)
    print("📊 测试环境详细数据检查")
    print("="*60)
    
    db_path = DB_FILES['test']
    print(f"📁 数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查用户
    print("\n👤 用户表:")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if users:
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        print(f"   列名: {user_columns}")
        print(f"   记录数: {len(users)}")
        for user in users:
            print(f"   - {user}")
    else:
        print("   没有用户")
    
    # 检查词汇
    print("\n📚 词汇表 (vocab_expressions):")
    cursor.execute("SELECT * FROM vocab_expressions")
    vocabs = cursor.fetchall()
    if vocabs:
        cursor.execute("PRAGMA table_info(vocab_expressions)")
        vocab_columns = [col[1] for col in cursor.fetchall()]
        print(f"   列名: {vocab_columns}")
        print(f"   记录数: {len(vocabs)}")
        for i, vocab in enumerate(vocabs, 1):
            vocab_dict = dict(zip(vocab_columns, vocab))
            print(f"   {i}. vocab_id={vocab_dict.get('vocab_id')}, "
                  f"vocab_body='{vocab_dict.get('vocab_body')}', "
                  f"explanation='{vocab_dict.get('explanation')[:50] if vocab_dict.get('explanation') else 'N/A'}...'")
    else:
        print("   没有词汇")
    
    # 检查语法规则
    print("\n📖 语法规则表 (grammar_rules):")
    cursor.execute("SELECT * FROM grammar_rules")
    grammar_rules = cursor.fetchall()
    if grammar_rules:
        cursor.execute("PRAGMA table_info(grammar_rules)")
        grammar_columns = [col[1] for col in cursor.fetchall()]
        print(f"   列名: {grammar_columns}")
        print(f"   记录数: {len(grammar_rules)}")
        for i, rule in enumerate(grammar_rules, 1):
            rule_dict = dict(zip(grammar_columns, rule))
            print(f"   {i}. rule_id={rule_dict.get('rule_id')}, "
                  f"rule_name='{rule_dict.get('rule_name')}', "
                  f"rule_summary='{rule_dict.get('rule_summary')[:50] if rule_dict.get('rule_summary') else 'N/A'}...'")
    else:
        print("   没有语法规则")
    
    # 检查文章
    print("\n📄 文章表 (original_texts):")
    cursor.execute("SELECT * FROM original_texts")
    texts = cursor.fetchall()
    if texts:
        cursor.execute("PRAGMA table_info(original_texts)")
        text_columns = [col[1] for col in cursor.fetchall()]
        print(f"   列名: {text_columns}")
        print(f"   记录数: {len(texts)}")
        for i, text in enumerate(texts, 1):
            text_dict = dict(zip(text_columns, text))
            print(f"   {i}. text_id={text_dict.get('text_id')}, "
                  f"text_title='{text_dict.get('text_title')}'")
    else:
        print("   没有文章")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ 检查完成")
    print("="*60)


if __name__ == "__main__":
    check_test_environment_data()

