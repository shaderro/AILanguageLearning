#!/usr/bin/env python3
"""
自动迁移测试和生产环境到新数据结构（非交互式）

执行步骤：
1. 迁移测试环境：重建表结构并迁移数据
2. 验证生产环境：确认已有user_id和language字段
3. 验证所有环境迁移结果
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
        inspector = inspect(session.bind)
        table_names = inspector.get_table_names()
        
        if table_name not in table_names:
            return []
        
        result = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
        
        data = []
        for row in result:
            if hasattr(row, '_mapping'):
                row_dict = dict(row._mapping)
            elif hasattr(row, '_asdict'):
                row_dict = row._asdict()
            else:
                cursor = session.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [col[1] for col in cursor.fetchall()]
                row_dict = dict(zip(columns, row))
            data.append(row_dict)
        
        return data
    except Exception as e:
        print(f"   ⚠️  导出 {table_name} 数据时出错: {e}")
        return []


def migrate_test_environment():
    """迁移测试环境"""
    print("\n" + "="*60)
    print("📋 迁移测试环境数据库")
    print("="*60)
    
    environment = 'testing'
    db_path = DB_FILES['test']
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = backup_database(db_path)
    
    # 连接数据库
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
        session = db_manager.get_session()
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return False
    
    try:
        # 导出现有数据
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
        
        session.close()
        
        # 重建表结构
        print(f"\n🔄 重建表结构...")
        from database_system.business_logic.models import (
            VocabExpression, GrammarRule, OriginalText,
            Sentence, Token, VocabExpressionExample, GrammarExample,
            User, VocabNotation, GrammarNotation, AskedToken
        )
        
        # 删除所有表
        print(f"   📝 删除所有旧表...")
        Base.metadata.drop_all(engine)
        print(f"   ✅ 所有旧表已删除")
        
        # 创建新表（包含所有表，包括user_id和language字段）
        print(f"   📝 创建新表结构...")
        Base.metadata.create_all(engine)
        print(f"   ✅ 新表已创建（包含user_id和language字段）")
        
        # 导入数据
        if vocab_count > 0 or grammar_count > 0 or text_count > 0:
            print(f"\n📥 导入数据到 user_id=1, language=德文...")
            session = db_manager.get_session()
            
            # 导入词汇
            if vocab_count > 0:
                print(f"   📝 导入 {vocab_count} 条词汇...")
                imported_count = 0
                for v in data['vocabs']:
                    try:
                        # 处理时间字段：如果updated_at为None，使用created_at或当前时间
                        created_at = v.get('created_at')
                        updated_at = v.get('updated_at') or created_at or datetime.now()
                        
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
                        # 处理时间字段：如果updated_at为None，使用created_at或当前时间
                        created_at = g.get('created_at')
                        updated_at = g.get('updated_at') or created_at or datetime.now()
                        
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
                            'created_at': created_at,
                            'updated_at': updated_at,
                        })
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  导入语法规则 {g.get('rule_id')} 时出错: {e}")
                
                session.commit()
                print(f"   ✅ 成功导入 {imported_count}/{grammar_count} 条语法规则")
            
            session.close()
        
        # 验证表结构
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
            
            # 验证数据
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            count = count_result[0] if count_result else 0
            print(f"      - 记录数: {count}")
        
        session.close()
        
        if all_ok:
            print(f"\n✅ 测试环境迁移完成！")
            return True
        else:
            print(f"\n❌ 测试环境迁移失败：表结构不正确")
            return False
            
    except Exception as e:
        session.rollback()
        print(f"❌ 测试环境迁移失败: {e}")
        if backup_path:
            print(f"💾 可以从备份恢复: {backup_path}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def verify_production_environment():
    """验证生产环境"""
    print("\n" + "="*60)
    print("📋 验证生产环境数据库")
    print("="*60)
    
    environment = 'production'
    db_path = DB_FILES['prod']
    
    if not os.path.exists(db_path):
        print(f"⚠️  数据库文件不存在: {db_path}")
        return False
    
    try:
        db_manager = DatabaseManager(environment)
        engine = db_manager.get_engine()
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
            
            # 验证数据
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            count = count_result[0] if count_result else 0
            print(f"      - 记录数: {count}")
        
        session.close()
        
        if all_ok:
            print(f"\n✅ 生产环境已验证：表结构正确")
            return True
        else:
            print(f"\n⚠️  生产环境需要更新：表结构不完整")
            return False
            
    except Exception as e:
        print(f"❌ 验证生产环境失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("自动迁移测试和生产环境到新数据结构")
    print("="*60)
    print("\n📋 此脚本将：")
    print("  1. 迁移测试环境（重建表结构并迁移数据）")
    print("  2. 验证生产环境（确认已有user_id和language字段）")
    print("  3. 验证所有环境迁移结果")
    print("\n⚠️  注意：")
    print("  - 测试环境的数据将迁移到 user_id=1, language=德文")
    print("  - 数据库会自动备份")
    print("  - 开发环境不会被修改")
    
    # 迁移测试环境
    test_success = migrate_test_environment()
    
    # 验证生产环境
    prod_success = verify_production_environment()
    
    # 总结
    print("\n" + "="*60)
    print("📊 迁移总结")
    print("="*60)
    print(f"  测试环境: {'✅ 成功' if test_success else '❌ 失败'}")
    print(f"  生产环境: {'✅ 已验证' if prod_success else '⚠️  需要更新'}")
    print("  开发环境: ✅ 保持不变")
    
    if test_success and prod_success:
        print("\n✅ 所有环境迁移完成！")
    else:
        print("\n⚠️  部分环境迁移失败，请检查错误信息")


if __name__ == "__main__":
    main()

