"""
手动创建 chat_messages 表（如果初始化脚本失败时使用）
"""
import os
import sqlite3
import sys

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(current_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# 数据库路径
DB_PATH = os.path.join(
    repo_root, 
    "backend", 
    "database_system", 
    "data_storage", 
    "data", 
    "language_learning.db"
)

def create_table():
    """手动创建 chat_messages 表"""
    print("=" * 70)
    print("🔧 手动创建 chat_messages 表")
    print("=" * 70)
    print(f"📁 数据库路径: {DB_PATH}")
    
    # 确保目录存在
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        print(f"📁 创建目录: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='chat_messages'
        """)
        if cursor.fetchone():
            print("✅ 表 chat_messages 已存在，跳过创建")
            conn.close()
            return True
        
        # 创建表
        print("📝 创建表 chat_messages...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                text_id INTEGER,
                sentence_id INTEGER,
                is_user INTEGER NOT NULL,
                content TEXT NOT NULL,
                quote_sentence_id INTEGER,
                quote_text TEXT,
                selected_token_json TEXT,
                created_at TEXT NOT NULL
            );
        """)
        
        conn.commit()
        print("✅ 表创建成功！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(chat_messages)")
        columns = cursor.fetchall()
        print(f"\n📋 表结构 ({len(columns)} 个字段):")
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            pk_str = " (主键)" if pk else ""
            not_null_str = " NOT NULL" if not_null else ""
            print(f"   - {name}: {col_type}{not_null_str}{pk_str}")
        
        conn.close()
        print("\n✅ 完成！现在可以运行测试脚本了")
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_table()
    if success:
        print("\n" + "=" * 70)
        print("🎉 下一步:")
        print("   1. 运行 python backend\\test_chat_history.py 验证表")
        print("   2. 启动后端服务器")
        print("   3. 在前端发送几条聊天消息")
        print("=" * 70)

