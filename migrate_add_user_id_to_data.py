"""
数据迁移：为核心表添加 user_id 字段并将现有数据归属到 user 1

执行步骤：
1. 备份当前数据库
2. 删除旧表
3. 创建新表结构（带 user_id）
4. 将数据迁移回来，设置 user_id = 1
"""
import sys
import os
import shutil
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import (
    Base, VocabExpression, GrammarRule, OriginalText, 
    Sentence, Token, VocabExpressionExample, GrammarExample
)
from sqlalchemy import inspect, text

def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None

def export_existing_data(session):
    """导出现有数据"""
    print("\n📤 导出现有数据...")
    
    data = {
        'vocabs': [],
        'grammar_rules': [],
        'texts': [],
        'sentences': [],
        'tokens': [],
        'vocab_examples': [],
        'grammar_examples': []
    }
    
    try:
        # 导出词汇
        vocabs = session.execute(text("SELECT * FROM vocab_expressions")).fetchall()
        data['vocabs'] = [dict(row._mapping) for row in vocabs]
        print(f"  - 词汇: {len(data['vocabs'])} 条")
        
        # 导出语法规则
        rules = session.execute(text("SELECT * FROM grammar_rules")).fetchall()
        data['grammar_rules'] = [dict(row._mapping) for row in rules]
        print(f"  - 语法规则: {len(data['grammar_rules'])} 条")
        
        # 导出文章
        texts = session.execute(text("SELECT * FROM original_texts")).fetchall()
        data['texts'] = [dict(row._mapping) for row in texts]
        print(f"  - 文章: {len(data['texts'])} 条")
        
        # 导出句子
        sentences = session.execute(text("SELECT * FROM sentences")).fetchall()
        data['sentences'] = [dict(row._mapping) for row in sentences]
        print(f"  - 句子: {len(data['sentences'])} 条")
        
        # 导出tokens
        tokens = session.execute(text("SELECT * FROM tokens")).fetchall()
        data['tokens'] = [dict(row._mapping) for row in tokens]
        print(f"  - Tokens: {len(data['tokens'])} 条")
        
        # 导出词汇例句
        vocab_examples = session.execute(text("SELECT * FROM vocab_expression_examples")).fetchall()
        data['vocab_examples'] = [dict(row._mapping) for row in vocab_examples]
        print(f"  - 词汇例句: {len(data['vocab_examples'])} 条")
        
        # 导出语法例句
        grammar_examples = session.execute(text("SELECT * FROM grammar_examples")).fetchall()
        data['grammar_examples'] = [dict(row._mapping) for row in grammar_examples]
        print(f"  - 语法例句: {len(data['grammar_examples'])} 条")
        
    except Exception as e:
        print(f"⚠️  导出数据时出错: {e}")
        print("   这可能是因为表结构已经更新，将直接创建新表")
    
    return data

def recreate_tables(engine):
    """重建表结构"""
    print("\n🔄 重建表结构...")
    
    # 删除所有表
    Base.metadata.drop_all(engine)
    print("  - 旧表已删除")
    
    # 创建新表
    Base.metadata.create_all(engine)
    print("  - 新表已创建")

def import_data_with_user_id(session, data, user_id=1):
    """导入数据并设置 user_id"""
    print(f"\n📥 导入数据到 user {user_id}...")
    
    try:
        # 1. 导入词汇
        if data['vocabs']:
            print(f"  - 导入词汇...")
            for v in data['vocabs']:
                session.execute(text("""
                    INSERT INTO vocab_expressions 
                    (vocab_id, user_id, vocab_body, explanation, source, is_starred, created_at, updated_at)
                    VALUES (:vocab_id, :user_id, :vocab_body, :explanation, :source, :is_starred, :created_at, :updated_at)
                """), {
                    'vocab_id': v['vocab_id'],
                    'user_id': user_id,
                    'vocab_body': v['vocab_body'],
                    'explanation': v['explanation'],
                    'source': v['source'],
                    'is_starred': v['is_starred'],
                    'created_at': v['created_at'],
                    'updated_at': v['updated_at']
                })
            print(f"    ✅ {len(data['vocabs'])} 条词汇")
        
        # 2. 导入语法规则
        if data['grammar_rules']:
            print(f"  - 导入语法规则...")
            for g in data['grammar_rules']:
                session.execute(text("""
                    INSERT INTO grammar_rules
                    (rule_id, user_id, rule_name, rule_summary, source, is_starred, created_at, updated_at)
                    VALUES (:rule_id, :user_id, :rule_name, :rule_summary, :source, :is_starred, :created_at, :updated_at)
                """), {
                    'rule_id': g['rule_id'],
                    'user_id': user_id,
                    'rule_name': g['rule_name'],
                    'rule_summary': g['rule_summary'],
                    'source': g['source'],
                    'is_starred': g['is_starred'],
                    'created_at': g['created_at'],
                    'updated_at': g['updated_at']
                })
            print(f"    ✅ {len(data['grammar_rules'])} 条语法规则")
        
        # 3. 导入文章
        if data['texts']:
            print(f"  - 导入文章...")
            for t in data['texts']:
                session.execute(text("""
                    INSERT INTO original_texts
                    (text_id, user_id, text_title, created_at, updated_at)
                    VALUES (:text_id, :user_id, :text_title, :created_at, :updated_at)
                """), {
                    'text_id': t['text_id'],
                    'user_id': user_id,
                    'text_title': t['text_title'],
                    'created_at': t['created_at'],
                    'updated_at': t['updated_at']
                })
            print(f"    ✅ {len(data['texts'])} 篇文章")
        
        # 4. 导入句子
        if data['sentences']:
            print(f"  - 导入句子...")
            for s in data['sentences']:
                session.execute(text("""
                    INSERT INTO sentences
                    (id, sentence_id, text_id, sentence_body, sentence_difficulty_level, 
                     grammar_annotations, vocab_annotations, created_at)
                    VALUES (:id, :sentence_id, :text_id, :sentence_body, :sentence_difficulty_level,
                            :grammar_annotations, :vocab_annotations, :created_at)
                """), s)
            print(f"    ✅ {len(data['sentences'])} 条句子")
        
        # 5. 导入tokens
        if data['tokens']:
            print(f"  - 导入tokens...")
            for tok in data['tokens']:
                session.execute(text("""
                    INSERT INTO tokens
                    (token_id, text_id, sentence_id, token_body, token_type, difficulty_level,
                     global_token_id, sentence_token_id, pos_tag, lemma, is_grammar_marker, 
                     linked_vocab_id, created_at)
                    VALUES (:token_id, :text_id, :sentence_id, :token_body, :token_type, :difficulty_level,
                            :global_token_id, :sentence_token_id, :pos_tag, :lemma, :is_grammar_marker,
                            :linked_vocab_id, :created_at)
                """), tok)
            print(f"    ✅ {len(data['tokens'])} 个tokens")
        
        # 6. 导入词汇例句
        if data['vocab_examples']:
            print(f"  - 导入词汇例句...")
            for ex in data['vocab_examples']:
                session.execute(text("""
                    INSERT INTO vocab_expression_examples
                    (example_id, vocab_id, text_id, sentence_id, context_explanation, token_indices, created_at)
                    VALUES (:example_id, :vocab_id, :text_id, :sentence_id, :context_explanation, :token_indices, :created_at)
                """), ex)
            print(f"    ✅ {len(data['vocab_examples'])} 条词汇例句")
        
        # 7. 导入语法例句
        if data['grammar_examples']:
            print(f"  - 导入语法例句...")
            for ex in data['grammar_examples']:
                session.execute(text("""
                    INSERT INTO grammar_examples
                    (example_id, rule_id, text_id, sentence_id, explanation_context, created_at)
                    VALUES (:example_id, :rule_id, :text_id, :sentence_id, :explanation_context, :created_at)
                """), ex)
            print(f"    ✅ {len(data['grammar_examples'])} 条语法例句")
        
        session.commit()
        print("\n✅ 所有数据导入完成")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 导入数据时出错: {e}")
        raise

def main():
    print("\n" + "="*60)
    print("数据迁移：添加 user_id 到核心表")
    print("="*60)
    
    # 数据库路径
    db_path = "database_system/data_storage/data/language_learning.db"
    
    # 1. 备份数据库
    backup_path = backup_database(db_path)
    
    # 2. 连接数据库
    db_manager = DatabaseManager('development')
    engine = db_manager.get_engine()
    session = db_manager.get_session()
    
    try:
        # 3. 导出现有数据
        data = export_existing_data(session)
        session.close()
        
        # 4. 重建表结构
        recreate_tables(engine)
        
        # 5. 重新获取 session
        session = db_manager.get_session()
        
        # 6. 导入数据（设置 user_id = 1）
        import_data_with_user_id(session, data, user_id=1)
        
        print("\n" + "="*60)
        print("✅ 迁移完成！")
        print("="*60)
        print(f"\n所有现有数据已归属到 User 1")
        print(f"备份文件: {backup_path}")
        print("\n下一步：")
        print("1. 重启后端服务器")
        print("2. 使用 User 1 登录测试")
        print("3. 创建 User 2 并测试数据隔离")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        if backup_path:
            print(f"\n可以从备份恢复: {backup_path}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()

