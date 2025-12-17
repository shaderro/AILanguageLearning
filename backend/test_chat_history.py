"""
测试聊天历史功能
用于验证数据库写入和 API 读取是否正常工作
"""
import sqlite3
import json
from datetime import datetime

# 数据库路径
DB_PATH = "database_system/data_storage/data/language_learning.db"

def test_db_read():
    """测试从数据库读取聊天记录"""
    print("=" * 70)
    print("📊 测试：从数据库读取聊天记录")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='chat_messages'
        """)
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ 表 chat_messages 不存在！")
            print("   请先运行一次聊天功能，让系统创建表。")
            return
        
        print("✅ 表 chat_messages 存在")
        
        # 统计总记录数
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        total_count = cursor.fetchone()[0]
        print(f"📈 总记录数: {total_count}")
        
        if total_count == 0:
            print("⚠️  数据库中没有聊天记录")
            print("   请先发送几条消息，然后再运行此测试。")
            return
        
        # 按文章分组统计
        cursor.execute("""
            SELECT text_id, COUNT(*) as count 
            FROM chat_messages 
            GROUP BY text_id 
            ORDER BY count DESC
        """)
        by_text = cursor.fetchall()
        print("\n📚 按文章分组统计:")
        for text_id, count in by_text:
            print(f"   文章 ID {text_id}: {count} 条消息")
        
        # 获取最近10条消息
        cursor.execute("""
            SELECT id, user_id, text_id, sentence_id, is_user, 
                   content, quote_text, created_at
            FROM chat_messages 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent = cursor.fetchall()
        
        print("\n📝 最近10条消息:")
        for msg in recent:
            msg_id, user_id, text_id, sentence_id, is_user, content, quote, created_at = msg
            msg_type = "👤 用户" if is_user else "🤖 AI"
            content_preview = content[:50] + "..." if len(content) > 50 else content
            print(f"   [{msg_id}] {msg_type} | 文章{text_id} 句子{sentence_id}")
            print(f"       内容: {content_preview}")
            print(f"       时间: {created_at}")
            if quote:
                print(f"       引用: {quote[:30]}...")
            print()
        
        conn.close()
        print("✅ 数据库读取测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_api_format():
    """测试 API 返回格式（模拟）"""
    print("\n" + "=" * 70)
    print("📡 测试：API 返回格式（模拟）")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 模拟 API 查询：获取某个文章的所有消息
        cursor.execute("""
            SELECT DISTINCT text_id FROM chat_messages LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            print("⚠️  没有可用的文章 ID")
            return
        
        test_text_id = result[0]
        print(f"📚 测试文章 ID: {test_text_id}")
        
        cursor.execute("""
            SELECT id, user_id, text_id, sentence_id, is_user, 
                   content, quote_text, selected_token_json, created_at
            FROM chat_messages 
            WHERE text_id = ?
            ORDER BY created_at ASC
            LIMIT 20
        """, (test_text_id,))
        
        messages = cursor.fetchall()
        print(f"📊 找到 {len(messages)} 条消息")
        
        # 转换为 API 格式
        api_response = {
            "success": True,
            "data": {
                "items": []
            }
        }
        
        for msg in messages:
            msg_id, user_id, text_id, sentence_id, is_user, content, quote, selected_token_json, created_at = msg
            api_response["data"]["items"].append({
                "id": msg_id,
                "user_id": user_id,
                "text_id": text_id,
                "sentence_id": sentence_id,
                "is_user": bool(is_user),
                "text": content,
                "quote_text": quote,
                "selected_token": json.loads(selected_token_json) if selected_token_json else None,
                "created_at": created_at
            })
        
        print("\n📤 API 响应格式（前3条）:")
        for i, item in enumerate(api_response["data"]["items"][:3]):
            print(f"\n   消息 {i+1}:")
            print(f"      ID: {item['id']}")
            print(f"      类型: {'用户' if item['is_user'] else 'AI'}")
            print(f"      内容: {item['text'][:50]}...")
            print(f"      时间: {item['created_at']}")
        
        conn.close()
        print("\n✅ API 格式测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🧪 聊天历史功能测试工具\n")
    test_db_read()
    test_api_format()
    print("\n" + "=" * 70)
    print("💡 提示:")
    print("   1. 如果数据库中没有记录，请先发送几条消息")
    print("   2. 清除浏览器 localStorage 后刷新页面测试跨设备功能")
    print("   3. 检查浏览器 Network 面板中的 /api/chat/history 请求")
    print("=" * 70)

