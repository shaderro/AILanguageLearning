#!/usr/bin/env python3
"""
测试环境数据库迁移：完整迁移（添加user_id和language字段，迁移数据）

执行步骤：
1. 备份当前数据库
2. 导出现有数据
3. 重建表结构（包含user_id和language字段）
4. 导入数据（设置user_id=1，language=德文）
5. 验证迁移结果
"""

import sys
import os
import shutil
from datetime import datetime

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.data_storage.config.config import DB_FILES
from database_system.business_logic.models import Base
from sqlalchemy import inspect, text


def backup_database(db_path):
    """备份数据库"""
    if os.path.exists(db_path):
        backup_path = db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    return None


def export_existing_data(session, table_name):
    """导出现有数据"""
    try:
        # 检查表是否存在
        inspector = inspect(session.bind)
        table_names = inspector.get_table_names()
        
        if table_name not in table_names:
            return []
        
        # 导出所有数据
        result = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        
        # 转换为字典列表
        data = []
        for row in result:
            # 尝试转换为字典
            if hasattr(row, '_mapping'):
                row_dict = dict(row._mapping)
            elif hasattr(row, '_asdict'):
                row_dict = row._asdict()
            else:
                # 如果是元组，需要知道列名
                cursor = session.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [col[1] for col in cursor.fetchall()]
                row_dict = dict(zip(columns, row))
            data.append(row_dict)
        
        return data
    except Exception as e:
        print(f"   ⚠️  导出 {table_name} 数据时出错: {e}")
        return []


def rebuild_test_environment_tables(environment, db_path):
    """重建测试环境表结构"""
    print(f"\n📋 重建 {environment} 环境数据库表结构...")
    print(f"   📁 数据库路径: {db_path}")
    
    # 1. 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"   ⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 2. 备份数据库
    backup_path = backup_database(db_path)
    
    # 3. 连接数据库
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
    except Exception as e:
        print(f"   ❌ 连接数据库失败: {e}")
        return False
    
    try:
        # 4. 导出现有数据
        print(f"\n📤 导出现有数据...")
        data = {
            'vocabs': export_existing_data(session, 'vocab_expressions'),
            'grammar_rules': export_existing_data(session, 'grammar_rules'),
            'texts': export_existing_data(session, 'original_texts'),
        }
        
        vocab_count = len(data['vocabs'])
        grammar_count = len(data['grammar_rules'])
        text_count = len(data['texts'])
        
        print(f"   📊 导出结果:")
        print(f"      - 词汇: {vocab_count} 条")
        print(f"      - 语法规则: {grammar_count} 条")
        print(f"      - 文章: {text_count} 条")
        
        if vocab_count > 0:
            print(f"   📝 示例词汇: {data['vocabs'][0] if data['vocabs'] else 'N/A'}")
        if grammar_count > 0:
            print(f"   📝 示例语法规则: {data['grammar_rules'][0] if data['grammar_rules'] else 'N/A'}")
        
        session.close()
        
        # 5. 删除旧表（按依赖顺序）
        print(f"\n🔄 删除旧表...")
        tables_to_drop = [
            'vocab_expression_examples',  # 依赖vocab_expressions
            'grammar_examples',  # 依赖grammar_rules
            'vocab_notations',  # 依赖vocab_expressions
            'grammar_notations',  # 依赖grammar_rules
            'tokens',  # 依赖original_texts
            'sentences',  # 依赖original_texts
            'asked_tokens',  # 依赖users
            'vocab_expressions',  # 依赖users
            'grammar_rules',  # 依赖users
            'original_texts',  # 依赖users
            # 注意：不要删除users表
        ]
        
        for table in tables_to_drop:
            try:
                engine.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"   ✅ 删除表: {table}")
            except Exception as e:
                print(f"   ⚠️  删除表 {table} 时出错: {e}")
        
        # 6. 创建新表结构
        print(f"\n🆕 创建新表结构...")
        from database_system.business_logic.models import (
            VocabExpression, GrammarRule, OriginalText,
            Sentence, Token, VocabExpressionExample, GrammarExample
        )
        
        # 创建表（包含user_id和language字段）
        Base.metadata.create_all(engine, tables=[
            VocabExpression.__table__,
            GrammarRule.__table__,
            OriginalText.__table__,
            Sentence.__table__,
            Token.__table__,
            VocabExpressionExample.__table__,
            GrammarExample.__table__,
        ])
        print(f"   ✅ 新表已创建")
        
        # 7. 导入数据（如果有）
        if vocab_count > 0 or grammar_count > 0 or text_count > 0:
            print(f"\n📥 导入数据到 user_id=1, language=德文...")
            session = db_manager.get_session()
            
            # 导入词汇
            if vocab_count > 0:
                print(f"   📝 导入 {vocab_count} 条词汇...")
                imported_count = 0
                for v in data['vocabs']:
                    try:
                        # 获取所有字段
                        vocab_id = v.get('vocab_id')
                        vocab_body = v.get('vocab_body')
                        explanation = v.get('explanation')
                        source = v.get('source', 'auto')
                        is_starred = v.get('is_starred', False)
                        created_at = v.get('created_at')
                        updated_at = v.get('updated_at')
                        
                        session.execute(text("""
                            INSERT INTO vocab_expressions 
                            (vocab_id, user_id, vocab_body, explanation, language, source, is_starred, created_at, updated_at)
                            VALUES (:vocab_id, 1, :vocab_body, :explanation, '德文', :source, :is_starred, :created_at, :updated_at)
                        """), {
                            'vocab_id': vocab_id,
                            'vocab_body': vocab_body,
                            'explanation': explanation,
                            'source': source,
                            'is_starred': is_starred,
                            'created_at': created_at,
                            'updated_at': updated_at,
                        })
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  导入词汇 {v.get('vocab_id')} 时出错: {e}")
                
                session.commit()
                print(f"   ✅ 成功导入 {imported_count}/{vocab_count} 条词汇")
            
            # 导入语法规则
            if grammar_count > 0:
                print(f"   📝 导入 {grammar_count} 条语法规则...")
                imported_count = 0
                for g in data['grammar_rules']:
                    try:
                        rule_id = g.get('rule_id')
                        rule_name = g.get('rule_name')
                        rule_summary = g.get('rule_summary')
                        source = g.get('source', 'auto')
                        is_starred = g.get('is_starred', False)
                        created_at = g.get('created_at')
                        updated_at = g.get('updated_at')
                        
                        session.execute(text("""
                            INSERT INTO grammar_rules 
                            (rule_id, user_id, rule_name, rule_summary, language, source, is_starred, created_at, updated_at)
                            VALUES (:rule_id, 1, :rule_name, :rule_summary, '德文', :source, :is_starred, :created_at, :updated_at)
                        """), {
                            'rule_id': rule_id,
                            'rule_name': rule_name,
                            'rule_summary': rule_summary,
                            'source': source,
                            'is_starred': is_starred,
                            'created_at': created_at,
                            'updated_at': updated_at,
                        })
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  导入语法规则 {g.get('rule_id')} 时出错: {e}")
                
                session.commit()
                print(f"   ✅ 成功导入 {imported_count}/{grammar_count} 条语法规则")
            
            # 导入文章
            if text_count > 0:
                print(f"   📝 导入 {text_count} 条文章...")
                imported_count = 0
                for t in data['texts']:
                    try:
                        text_id = t.get('text_id')
                        text_title = t.get('text_title')
                        created_at = t.get('created_at')
                        updated_at = t.get('updated_at')
                        
                        session.execute(text("""
                            INSERT INTO original_texts 
                            (text_id, user_id, text_title, language, created_at, updated_at)
                            VALUES (:text_id, 1, :text_title, '德文', :created_at, :updated_at)
                        """), {
                            'text_id': text_id,
                            'text_title': text_title,
                            'created_at': created_at,
                            'updated_at': updated_at,
                        })
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  导入文章 {t.get('text_id')} 时出错: {e}")
                
                session.commit()
                print(f"   ✅ 成功导入 {imported_count}/{text_count} 条文章")
            
            session.close()
        
        # 8. 验证表结构
        print(f"\n🔍 验证表结构...")
        session = db_manager.get_session()
        inspector = inspect(engine)
        
        tables_to_check = ['vocab_expressions', 'grammar_rules', 'original_texts']
        for table_name in tables_to_check:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            has_user_id = 'user_id' in columns
            has_language = 'language' in columns
            
            status = "✅" if has_user_id and has_language else "❌"
            print(f"   {status} {table_name}:")
            print(f"      - user_id: {'有' if has_user_id else '无'}")
            print(f"      - language: {'有' if has_language else '无'}")
            
            # 验证数据
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            count = count_result[0] if count_result else 0
            print(f"      - 记录数: {count}")
            
            if count > 0 and has_user_id:
                user_count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE user_id = 1")).fetchone()
                user_count = user_count_result[0] if user_count_result else 0
                print(f"      - user_id=1的记录数: {user_count}")
            
            if count > 0 and has_language:
                lang_count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE language = '德文'")).fetchone()
                lang_count = lang_count_result[0] if lang_count_result else 0
                print(f"      - language='德文'的记录数: {lang_count}")
        
        session.close()
        
        return True
            
    except Exception as e:
        session.rollback()
        print(f"   ❌ {environment} 环境更新失败: {e}")
        if backup_path:
            print(f"   💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("测试环境数据库迁移：完整迁移（添加user_id和language字段）")
    print("="*60)
    print("\n⚠️  注意：此脚本会重建表结构")
    print("⚠️  请确保已经备份数据库")
    print("⚠️  现有数据将迁移到 user_id=1, language=德文")
    print("\n📋 此脚本将：")
    print("  1. 备份数据库")
    print("  2. 导出现有数据（3个vocab, 2个grammar）")
    print("  3. 删除旧表")
    print("  4. 创建新表结构（包含user_id和language字段）")
    print("  5. 导入数据（设置user_id=1, language=德文）")
    print("  6. 验证迁移结果")
    
    response = input("\n❓ 是否继续？(y/n): ")
    if response.lower() != 'y':
        print("⏭️  已取消")
        return
    
    # 迁移测试环境数据库
    environment = 'testing'
    db_path = DB_FILES['test']
    
    if rebuild_test_environment_tables(environment, db_path):
        print("\n" + "="*60)
        print("✅ 迁移完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 验证数据库中的 user_id 和 language 字段")
        print("2. 测试用户隔离功能")
        print("3. 确认API正常工作")
        print("4. 确认所有数据都归属到 user_id=1, language=德文")
    else:
        print("\n" + "="*60)
        print("❌ 迁移失败")
        print("="*60)
        print("请检查错误信息并修复")


if __name__ == "__main__":
    main()

