"""
检查各个用户的数据
"""
import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import VocabExpression, GrammarRule

db_manager = DatabaseManager('development')
session = db_manager.get_session()

print("\n" + "="*60)
print("用户数据检查")
print("="*60)

for user_id in [1, 2, 3]:
    vocab_count = session.query(VocabExpression).filter(
        VocabExpression.user_id == user_id
    ).count()
    
    grammar_count = session.query(GrammarRule).filter(
        GrammarRule.user_id == user_id
    ).count()
    
    print(f"\n👤 User {user_id}:")
    print(f"  - 词汇: {vocab_count} 条")
    print(f"  - 语法: {grammar_count} 条")
    
    if vocab_count > 0:
        vocabs = session.query(VocabExpression).filter(
            VocabExpression.user_id == user_id
        ).limit(3).all()
        print(f"  - 前3个词汇:", [v.vocab_body for v in vocabs])

session.close()

print("\n" + "="*60)
print("✅ 检查完成")
print("="*60)

