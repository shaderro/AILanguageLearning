"""
检查脚本：确认 vocab 和 grammar 数据库中是否已添加 learn_status 字段

使用方法：
    python check_learn_status_fields.py
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database_system.database_manager import DatabaseManager
from sqlalchemy import inspect, text

def check_learn_status_fields():
    """检查 learn_status 字段是否存在"""
    
    print("=" * 80)
    print("🔍 检查数据库中的 learn_status 字段")
    print("=" * 80)
    
    # 连接到开发数据库
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    engine = db_manager.get_engine()
    
    try:
        inspector = inspect(engine)
        
        # 检查 vocab_expressions 表
        print("\n📚 检查 vocab_expressions 表...")
        if 'vocab_expressions' in inspector.get_table_names():
            vocab_columns = [col['name'] for col in inspector.get_columns('vocab_expressions')]
            if 'learn_status' in vocab_columns:
                print("  ✅ learn_status 字段已存在")
                # 检查字段类型和默认值
                for col in inspector.get_columns('vocab_expressions'):
                    if col['name'] == 'learn_status':
                        print(f"     - 类型: {col['type']}")
                        print(f"     - 可空: {col['nullable']}")
                        print(f"     - 默认值: {col.get('default', 'None')}")
                
                # 统计 learn_status 的值分布
                result = session.execute(text("""
                    SELECT learn_status, COUNT(*) as count 
                    FROM vocab_expressions 
                    GROUP BY learn_status
                """))
                print("     - 值分布:")
                for row in result:
                    print(f"       * {row[0]}: {row[1]} 个")
            else:
                print("  ❌ learn_status 字段不存在")
        else:
            print("  ⚠️  vocab_expressions 表不存在")
        
        # 检查 grammar_rules 表
        print("\n📖 检查 grammar_rules 表...")
        if 'grammar_rules' in inspector.get_table_names():
            grammar_columns = [col['name'] for col in inspector.get_columns('grammar_rules')]
            if 'learn_status' in grammar_columns:
                print("  ✅ learn_status 字段已存在")
                # 检查字段类型和默认值
                for col in inspector.get_columns('grammar_rules'):
                    if col['name'] == 'learn_status':
                        print(f"     - 类型: {col['type']}")
                        print(f"     - 可空: {col['nullable']}")
                        print(f"     - 默认值: {col.get('default', 'None')}")
                
                # 统计 learn_status 的值分布
                result = session.execute(text("""
                    SELECT learn_status, COUNT(*) as count 
                    FROM grammar_rules 
                    GROUP BY learn_status
                """))
                print("     - 值分布:")
                for row in result:
                    print(f"       * {row[0]}: {row[1]} 个")
            else:
                print("  ❌ learn_status 字段不存在")
        else:
            print("  ⚠️  grammar_rules 表不存在")
        
        print("\n" + "=" * 80)
        print("✅ 检查完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    check_learn_status_fields()

