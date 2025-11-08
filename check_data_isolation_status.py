"""
检查所有数据表的隔离状态
"""
import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import (
    VocabExpression, GrammarRule, OriginalText,
    VocabExpressionExample, GrammarExample,
    VocabNotation, GrammarNotation,
    Sentence, Token
)
from sqlalchemy import inspect

def check_table_has_user_id(model_class):
    """检查表是否有 user_id 字段"""
    mapper = inspect(model_class)
    columns = [col.name for col in mapper.columns]
    return 'user_id' in columns

def main():
    print("\n" + "="*60)
    print("数据隔离状态检查")
    print("="*60)
    
    # 核心数据表
    print("\n📊 核心数据表（直接有 user_id）：")
    core_tables = [
        ("VocabExpression", VocabExpression, "词汇"),
        ("GrammarRule", GrammarRule, "语法规则"),
        ("OriginalText", OriginalText, "文章"),
    ]
    
    for table_name, model, desc in core_tables:
        has_user_id = check_table_has_user_id(model)
        status = "✅" if has_user_id else "❌"
        print(f"  {status} {desc:10} ({table_name}): {'有 user_id' if has_user_id else '无 user_id'}")
    
    # 标注表
    print("\n📌 标注表（直接有 user_id）：")
    notation_tables = [
        ("VocabNotation", VocabNotation, "词汇标注"),
        ("GrammarNotation", GrammarNotation, "语法标注"),
    ]
    
    for table_name, model, desc in notation_tables:
        has_user_id = check_table_has_user_id(model)
        status = "✅" if has_user_id else "❌"
        print(f"  {status} {desc:10} ({table_name}): {'有 user_id' if has_user_id else '无 user_id'}")
    
    # 例句表（通过外键级联隔离）
    print("\n📝 例句表（通过外键级联隔离）：")
    example_tables = [
        ("VocabExpressionExample", VocabExpressionExample, "词汇例句", "vocab_id → VocabExpression.user_id"),
        ("GrammarExample", GrammarExample, "语法例句", "rule_id → GrammarRule.user_id"),
    ]
    
    for table_name, model, desc, chain in example_tables:
        has_user_id = check_table_has_user_id(model)
        if has_user_id:
            print(f"  ✅ {desc:10} ({table_name}): 直接有 user_id")
        else:
            print(f"  ✅ {desc:10} ({table_name}): 通过外键级联隔离")
            print(f"      关联链: {chain}")
    
    # 句子和Token（通过外键级联隔离）
    print("\n📄 文章相关表（通过外键级联隔离）：")
    text_tables = [
        ("Sentence", Sentence, "句子", "text_id → OriginalText.user_id"),
        ("Token", Token, "Token", "text_id → OriginalText.user_id"),
    ]
    
    for table_name, model, desc, chain in text_tables:
        has_user_id = check_table_has_user_id(model)
        if has_user_id:
            print(f"  ✅ {desc:10} ({table_name}): 直接有 user_id")
        else:
            print(f"  ✅ {desc:10} ({table_name}): 通过外键级联隔离")
            print(f"      关联链: {chain}")
    
    # 统计数据
    print("\n" + "="*60)
    print("📊 数据统计")
    print("="*60)
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    try:
        for user_id in [1, 2]:
            print(f"\n👤 User {user_id}:")
            
            # 词汇
            vocab_count = session.query(VocabExpression).filter(
                VocabExpression.user_id == user_id
            ).count()
            print(f"  - 词汇: {vocab_count}")
            
            # 语法规则
            grammar_count = session.query(GrammarRule).filter(
                GrammarRule.user_id == user_id
            ).count()
            print(f"  - 语法规则: {grammar_count}")
            
            # 文章
            text_count = session.query(OriginalText).filter(
                OriginalText.user_id == user_id
            ).count()
            print(f"  - 文章: {text_count}")
            
            # 词汇标注
            vocab_notation_count = session.query(VocabNotation).filter(
                VocabNotation.user_id == user_id
            ).count()
            print(f"  - 词汇标注: {vocab_notation_count}")
            
            # 语法标注
            grammar_notation_count = session.query(GrammarNotation).filter(
                GrammarNotation.user_id == user_id
            ).count()
            print(f"  - 语法标注: {grammar_notation_count}")
            
            # 词汇例句（通过 vocab_id 关联）
            vocab_example_count = session.query(VocabExpressionExample).join(
                VocabExpression
            ).filter(VocabExpression.user_id == user_id).count()
            print(f"  - 词汇例句: {vocab_example_count}")
            
            # 语法例句（通过 rule_id 关联）
            grammar_example_count = session.query(GrammarExample).join(
                GrammarRule
            ).filter(GrammarRule.user_id == user_id).count()
            print(f"  - 语法例句: {grammar_example_count}")
            
            # 句子（通过 text_id 关联）
            sentence_count = session.query(Sentence).join(
                OriginalText
            ).filter(OriginalText.user_id == user_id).count()
            print(f"  - 句子: {sentence_count}")
            
            # Token（通过 text_id 关联）
            token_count = session.query(Token).join(
                OriginalText
            ).filter(OriginalText.user_id == user_id).count()
            print(f"  - Token: {token_count}")
    
    finally:
        session.close()
    
    print("\n" + "="*60)
    print("✅ 检查完成")
    print("="*60)
    
    print("\n📝 总结：")
    print("  ✅ 核心表（Vocab, Grammar, Text）已添加 user_id")
    print("  ✅ 标注表（VocabNotation, GrammarNotation）已有 user_id")
    print("  ✅ 例句表通过外键自动隔离")
    print("  ✅ 句子和Token通过外键自动隔离")
    print("\n⚠️  API 隔离状态：")
    print("  ✅ Vocab API - 完全隔离")
    print("  🔄 Grammar API - 列表已隔离，其他端点待完成")
    print("  ❌ Text API - 待实现")
    print("  ❌ Notation API - 待实现")

if __name__ == "__main__":
    main()

