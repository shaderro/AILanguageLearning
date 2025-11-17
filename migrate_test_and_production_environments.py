#!/usr/bin/env python3
"""
批量迁移测试环境和生产环境到新数据结构

执行步骤：
1. 迁移测试环境（有数据，完整迁移）
2. 迁移生产环境（没有数据，添加字段）
3. 验证迁移结果
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


def migrate_test_environment():
    """迁移测试环境（完整迁移：重建表结构 + 迁移数据）"""
    print("\n" + "="*60)
    print("📋 迁移测试环境（完整迁移）")
    print("="*60)
    
    environment = 'testing'
    db_path = DB_FILES['test']
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        # 1. 导出现有数据
        print(f"\n📤 导出现有数据...")
        
        def export_data(table_name):
            try:
                inspector = inspect(session.bind)
                if table_name not in inspector.get_table_names():
                    return []
                result = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                if not result:
                    return []
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                data = []
                for row in result:
                    if hasattr(row, '_mapping'):
                        data.append(dict(row._mapping))
                    else:
                        data.append(dict(zip(columns, row)))
                return data
            except Exception as e:
                print(f"   ⚠️  导出 {table_name} 数据时出错: {e}")
                return []
        
        data = {
            'vocabs': export_data('vocab_expressions'),
            'grammar_rules': export_data('grammar_rules'),
            'texts': export_data('original_texts'),
        }
        
        vocab_count = len(data['vocabs'])
        grammar_count = len(data['grammar_rules'])
        text_count = len(data['texts'])
        
        print(f"   📊 导出结果:")
        print(f"      - 词汇: {vocab_count} 条")
        print(f"      - 语法规则: {grammar_count} 条")
        print(f"      - 文章: {text_count} 条")
        
        session.close()
        
        # 2. 删除旧表
        print(f"\n🔄 删除旧表...")
        tables_to_drop = [
            'vocab_expression_examples',
            'grammar_examples',
            'vocab_notations',
            'grammar_notations',
            'tokens',
            'sentences',
            'asked_tokens',
            'vocab_expressions',
            'grammar_rules',
            'original_texts',
        ]
        
        for table in tables_to_drop:
            try:
                engine.execute(text(f"DROP TABLE IF EXISTS {table}"))
                print(f"   ✅ 删除表: {table}")
            except Exception as e:
                print(f"   ⚠️  删除表 {table} 时出错: {e}")
        
        # 3. 创建新表结构
        print(f"\n🆕 创建新表结构...")
        from database_system.business_logic.models import (
            VocabExpression, GrammarRule, OriginalText,
            Sentence, Token, VocabExpressionExample, GrammarExample
        )
        
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
        
        # 4. 导入数据（如果有）
        if vocab_count > 0 or grammar_count > 0 or text_count > 0:
            print(f"\n📥 导入数据到 user_id=1, language=德文...")
            session = db_manager.get_session()
            
            # 导入词汇
            if vocab_count > 0:
                print(f"   📝 导入 {vocab_count} 条词汇...")
                imported_count = 0
                for v in data['vocabs']:
                    try:
                        session.execute(text("""
                            INSERT INTO vocab_expressions 
                            (vocab_id, user_id, vocab_body, explanation, language, source, is_starred, created_at, updated_at)
                            VALUES (:vocab_id, 1, :vocab_body, :explanation, '德文', :source, :is_starred, :created_at, :updated_at)
                        """), {
                            'vocab_id': v.get('vocab_id'),
                            'vocab_body': v.get('vocab_body'),
                            'explanation': v.get('explanation'),
                            'source': v.get('source', 'auto'),
                            'is_starred': v.get('is_starred', False),
                            'created_at': v.get('created_at'),
                            'updated_at': v.get('updated_at'),
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
                        session.execute(text("""
                            INSERT INTO grammar_rules 
                            (rule_id, user_id, rule_name, rule_summary, language, source, is_starred, created_at, updated_at)
                            VALUES (:rule_id, 1, :rule_name, :rule_summary, '德文', :source, :is_starred, :created_at, :updated_at)
                        """), {
                            'rule_id': g.get('rule_id'),
                            'rule_name': g.get('rule_name'),
                            'rule_summary': g.get('rule_summary'),
                            'source': g.get('source', 'auto'),
                            'is_starred': g.get('is_starred', False),
                            'created_at': g.get('created_at'),
                            'updated_at': g.get('updated_at'),
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
                        session.execute(text("""
                            INSERT INTO original_texts 
                            (text_id, user_id, text_title, language, created_at, updated_at)
                            VALUES (:text_id, 1, :text_title, '德文', :created_at, :updated_at)
                        """), {
                            'text_id': t.get('text_id'),
                            'text_title': t.get('text_title'),
                            'created_at': t.get('created_at'),
                            'updated_at': t.get('updated_at'),
                        })
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  导入文章 {t.get('text_id')} 时出错: {e}")
                
                session.commit()
                print(f"   ✅ 成功导入 {imported_count}/{text_count} 条文章")
            
            session.close()
        
        # 5. 验证表结构
        print(f"\n🔍 验证表结构...")
        session = db_manager.get_session()
        inspector = inspect(engine)
        
        tables_to_check = ['vocab_expressions', 'grammar_rules', 'original_texts']
        all_ok = True
        for table_name in tables_to_check:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            has_user_id = 'user_id' in columns
            has_language = 'language' in columns
            
            status = "✅" if has_user_id and has_language else "❌"
            print(f"   {status} {table_name}:")
            print(f"      - user_id: {'有' if has_user_id else '无'}")
            print(f"      - language: {'有' if has_language else '无'}")
            
            if not (has_user_id and has_language):
                all_ok = False
        
        session.close()
        
        if all_ok:
            print(f"\n✅ 测试环境迁移完成！")
            return True
        else:
            print(f"\n❌ 测试环境迁移失败：表结构不完整")
            return False
            
    except Exception as e:
        print(f"❌ 测试环境迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_production_environment():
    """迁移生产环境（添加user_id字段）"""
    print("\n" + "="*60)
    print("📋 迁移生产环境（添加user_id字段）")
    print("="*60)
    
    environment = 'production'
    db_path = DB_FILES['prod']
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
        
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        tables = [
            ('vocab_expressions', 'INTEGER'),
            ('grammar_rules', 'INTEGER'),
            ('original_texts', 'INTEGER'),
        ]
        
        success_count = 0
        for table_name, user_id_type in tables:
            print(f"\n📋 处理表: {table_name}")
            
            if table_name not in table_names:
                print(f"   ⚠️  {table_name} 表不存在，跳过")
                continue
            
            # 检查user_id字段是否存在
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if 'user_id' in columns:
                print(f"   ℹ️  {table_name} 表的 user_id 字段已存在，跳过")
                success_count += 1
                continue
            
            # 检查是否有数据
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            record_count = count_result[0] if count_result else 0
            print(f"   📊 当前记录数: {record_count}")
            
            # 添加user_id字段
            print(f"   📝 添加 user_id 字段...")
            try:
                session.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN user_id {user_id_type}
                """))
                session.commit()
                print(f"   ✅ 成功添加 user_id 字段")
                
                # 如果有数据，设置默认user_id=1
                if record_count > 0:
                    print(f"   📝 设置现有记录的 user_id = 1...")
                    session.execute(text(f"""
                        UPDATE {table_name} 
                        SET user_id = 1 
                        WHERE user_id IS NULL
                    """))
                    session.commit()
                    print(f"   ✅ 成功设置 {record_count} 条记录的 user_id = 1")
                
                success_count += 1
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ℹ️  {table_name} 表的 user_id 字段已存在")
                    success_count += 1
                else:
                    raise
        
        session.close()
        
        # 验证表结构
        print(f"\n🔍 验证表结构...")
        session = db_manager.get_session()
        inspector = inspect(engine)
        
        all_ok = True
        for table_name, _ in tables:
            if table_name in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                has_user_id = 'user_id' in columns
                has_language = 'language' in columns
                
                status = "✅" if has_user_id and has_language else "⚠️"
                print(f"   {status} {table_name}:")
                print(f"      - user_id: {'有' if has_user_id else '无'}")
                print(f"      - language: {'有' if has_language else '无'}")
                
                if not has_user_id:
                    all_ok = False
        
        session.close()
        
        if success_count == len(tables) and all_ok:
            print(f"\n✅ 生产环境迁移完成！")
            return True
        else:
            print(f"\n⚠️  生产环境部分迁移完成 ({success_count}/{len(tables)})")
            return success_count == len(tables)
            
    except Exception as e:
        print(f"❌ 生产环境迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("批量迁移测试环境和生产环境到新数据结构")
    print("="*60)
    print("\n📋 迁移计划：")
    print("  1. 迁移测试环境（完整迁移：重建表结构 + 迁移数据）")
    print("  2. 迁移生产环境（添加user_id字段）")
    print("  3. 验证迁移结果")
    print("\n⚠️  注意：")
    print("  - 测试环境：会重建表结构，现有数据将迁移到 user_id=1, language=德文")
    print("  - 生产环境：会添加user_id字段（表是空的，安全）")
    print("  - 两个环境都会自动备份数据库")
    print("  - 开发环境保持不变")
    
    # 自动执行（不需要确认）
    print("\n🚀 开始自动迁移...")
    print("   - 测试环境：完整迁移（重建表结构 + 迁移数据）")
    print("   - 生产环境：添加user_id字段")
    print("   - 开发环境：保持不变\n")
    
    # 1. 迁移测试环境
    test_success = migrate_test_environment()
    
    # 2. 迁移生产环境
    prod_success = migrate_production_environment()
    
    # 3. 总结
    print("\n" + "="*60)
    print("📊 迁移结果总结")
    print("="*60)
    print(f"  测试环境: {'✅ 成功' if test_success else '❌ 失败'}")
    print(f"  生产环境: {'✅ 成功' if prod_success else '❌ 失败'}")
    print("  开发环境: ✅ 保持不变（已有新数据结构）")
    print("="*60)
    
    if test_success and prod_success:
        print("\n✅ 所有环境迁移完成！")
        print("\n下一步：")
        print("1. 验证测试环境和生产环境的表结构")
        print("2. 确认测试环境的数据已正确迁移")
        print("3. 确认生产环境的user_id字段已添加")
        print("4. 测试环境切换功能（如果需要）")
    else:
        print("\n⚠️  部分迁移完成，请检查错误信息")


if __name__ == "__main__":
    main()

