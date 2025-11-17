"""
迁移脚本：为所有 vocab 添加 learn_status 字段

功能：
1. 在 vocab_expressions 表中添加 learn_status 字段（如果不存在）
2. 将所有现有 vocab 的 learn_status 设置为 'not_mastered'（未掌握）

使用方法：
    python migrate_add_learn_status_to_vocab.py
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import VocabExpression, LearnStatus
from sqlalchemy import inspect, text

def migrate_vocab_learn_status():
    """迁移函数：添加 learn_status 字段并设置默认值"""
    
    print("=" * 80)
    print("🚀 开始迁移：为所有 vocab 添加 learn_status 字段")
    print("=" * 80)
    
    # 连接到开发数据库
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    engine = db_manager.get_engine()
    
    try:
        # 检查 learn_status 字段是否已存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('vocab_expressions')]
        
        if 'learn_status' in columns:
            print("✅ learn_status 字段已存在，跳过添加字段步骤")
        else:
            print("📝 添加 learn_status 字段到 vocab_expressions 表...")
            # 使用 SQLite 的 ALTER TABLE 添加列
            # 注意：SQLite 不支持直接添加 ENUM，我们需要先添加 TEXT 列，然后迁移数据
            session.execute(text("""
                ALTER TABLE vocab_expressions 
                ADD COLUMN learn_status TEXT DEFAULT 'not_mastered'
            """))
            session.commit()
            print("✅ learn_status 字段添加成功")
        
        # 更新所有现有 vocab 的 learn_status 为 'NOT_MASTERED'（枚举值）
        print("\n📝 更新所有现有 vocab 的 learn_status 为 'NOT_MASTERED'...")
        
        # 先使用原始 SQL 查询总数（避免枚举转换问题）
        result = session.execute(text("SELECT COUNT(*) FROM vocab_expressions"))
        total_count = result.scalar()
        
        if total_count == 0:
            print("ℹ️  没有找到任何 vocab，跳过更新")
        else:
            # 使用原始 SQL 更新所有记录为 'NOT_MASTERED'（枚举值）
            # 注意：SQLAlchemy 的 Enum 在 SQLite 中存储的是枚举的 value（小写），但读取时期望匹配枚举名
            # 我们需要更新为枚举的 value：'not_mastered'
            session.execute(text("""
                UPDATE vocab_expressions 
                SET learn_status = 'not_mastered'
                WHERE learn_status IS NULL OR learn_status != 'not_mastered'
            """))
            session.commit()
            
            # 验证更新结果
            result = session.execute(text("SELECT COUNT(*) FROM vocab_expressions WHERE learn_status = 'not_mastered'"))
            updated_count = result.scalar()
            
            print(f"✅ 成功更新 {updated_count}/{total_count} 个 vocab 的 learn_status 为 'not_mastered'")
        
        print("\n" + "=" * 80)
        print("✅ 迁移完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_vocab_learn_status()

