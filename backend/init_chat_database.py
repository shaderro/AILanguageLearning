"""
初始化聊天记录数据库表
如果表不存在，会自动创建
"""
import os
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(current_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.data_managers.chat_message_manager_db import ChatMessageManagerDB

def init_chat_database():
    """初始化聊天记录数据库表"""
    print("=" * 70)
    print("🔧 初始化聊天记录数据库表")
    print("=" * 70)
    
    try:
        # 创建 ChatMessageManagerDB 实例，会自动创建表
        manager = ChatMessageManagerDB()
        
        # 获取数据库路径
        db_path = manager.db_path
        print(f"✅ 数据库路径: {db_path}")
        
        # 验证表是否存在
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='chat_messages'
        """)
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ 表 chat_messages 已存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(chat_messages)")
            columns = cursor.fetchall()
            print(f"\n📋 表结构 ({len(columns)} 个字段):")
            for col in columns:
                col_id, name, col_type, not_null, default_val, pk = col
                pk_str = " (主键)" if pk else ""
                not_null_str = " NOT NULL" if not_null else ""
                print(f"   - {name}: {col_type}{not_null_str}{pk_str}")
            
            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM chat_messages")
            count = cursor.fetchone()[0]
            print(f"\n📊 当前记录数: {count}")
        else:
            print("❌ 表创建失败！")
            return False
        
        conn.close()
        print("\n✅ 数据库初始化完成！")
        print("💡 现在可以发送聊天消息，系统会自动保存到数据库")
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_chat_database()
    if success:
        print("\n" + "=" * 70)
        print("🎉 下一步:")
        print("   1. 启动后端服务器")
        print("   2. 在前端发送几条聊天消息")
        print("   3. 运行 python backend\\test_chat_history.py 验证数据")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("⚠️  请检查:")
        print("   1. 数据库文件路径是否正确")
        print("   2. 是否有写入权限")
        print("   3. 查看上面的错误信息")
        print("=" * 70)

