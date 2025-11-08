"""
给 User 1 和 User 2 添加测试词汇，验证数据隔离
"""
import sys
import os

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import VocabExpression, SourceType

def main():
    print("\n" + "="*60)
    print("添加测试词汇")
    print("="*60)
    
    # 连接数据库
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    try:
        # User 1 的测试词汇
        print("\n📝 User 1 的词汇：")
        user1_vocabs = [
            {"vocab_body": "hello", "explanation": "你好，问候语", "user_id": 1},
            {"vocab_body": "world", "explanation": "世界", "user_id": 1},
            {"vocab_body": "apple", "explanation": "苹果（水果）", "user_id": 1},
        ]
        
        for v in user1_vocabs:
            # 检查是否已存在
            existing = session.query(VocabExpression).filter(
                VocabExpression.vocab_body == v["vocab_body"],
                VocabExpression.user_id == v["user_id"]
            ).first()
            
            if existing:
                print(f"  ⏭️  '{v['vocab_body']}' 已存在，跳过")
                continue
            
            vocab = VocabExpression(
                user_id=v["user_id"],
                vocab_body=v["vocab_body"],
                explanation=v["explanation"],
                source=SourceType.MANUAL,
                is_starred=False
            )
            session.add(vocab)
            print(f"  ✅ 添加: {v['vocab_body']} - {v['explanation']}")
        
        # User 2 的测试词汇（与User 1有重复，测试隔离）
        print("\n📝 User 2 的词汇：")
        user2_vocabs = [
            {"vocab_body": "hello", "explanation": "你好（正式场合）", "user_id": 2},
            {"vocab_body": "goodbye", "explanation": "再见", "user_id": 2},
            {"vocab_body": "apple", "explanation": "苹果公司", "user_id": 2},
        ]
        
        for v in user2_vocabs:
            # 检查是否已存在
            existing = session.query(VocabExpression).filter(
                VocabExpression.vocab_body == v["vocab_body"],
                VocabExpression.user_id == v["user_id"]
            ).first()
            
            if existing:
                print(f"  ⏭️  '{v['vocab_body']}' 已存在，跳过")
                continue
            
            vocab = VocabExpression(
                user_id=v["user_id"],
                vocab_body=v["vocab_body"],
                explanation=v["explanation"],
                source=SourceType.MANUAL,
                is_starred=False
            )
            session.add(vocab)
            print(f"  ✅ 添加: {v['vocab_body']} - {v['explanation']}")
        
        session.commit()
        
        print("\n" + "="*60)
        print("✅ 测试词汇添加完成！")
        print("="*60)
        
        # 统计
        user1_count = session.query(VocabExpression).filter(
            VocabExpression.user_id == 1
        ).count()
        
        user2_count = session.query(VocabExpression).filter(
            VocabExpression.user_id == 2
        ).count()
        
        print(f"\n📊 统计：")
        print(f"  User 1: {user1_count} 条词汇")
        print(f"  User 2: {user2_count} 条词汇")
        
        print(f"\n🧪 测试步骤：")
        print(f"1. 登录 User 1 (test123456)")
        print(f"   - 应该看到包含 'hello', 'world', 'apple' 的词汇")
        print(f"   - 'hello' 的解释应该是：你好，问候语")
        print(f"   - 'apple' 的解释应该是：苹果（水果）")
        print(f"")
        print(f"2. 登录 User 2 (mypassword123)")
        print(f"   - 应该看到 'hello', 'goodbye', 'apple'")
        print(f"   - 'hello' 的解释应该是：你好（正式场合）← 不同于User 1")
        print(f"   - 'apple' 的解释应该是：苹果公司 ← 不同于User 1")
        print(f"   - 看不到 'world' ← User 1 独有")
        print(f"")
        print(f"3. 数据隔离成功标志：")
        print(f"   ✅ 两个用户都有 'hello' 和 'apple'")
        print(f"   ✅ 但解释不同（说明是独立的数据）")
        print(f"   ✅ 用户只能看到自己的数据")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()

