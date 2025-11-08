"""
给 User 1 和 User 2 添加测试语法规则
"""
import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import GrammarRule, SourceType

def main():
    print("\n" + "="*60)
    print("添加测试语法规则")
    print("="*60)
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    try:
        # User 2 的测试语法规则
        print("\n📝 User 2 的语法规则：")
        user2_rules = [
            {
                "rule_name": "现在进行时",
                "rule_summary": "表示正在进行的动作，结构：be + doing",
                "user_id": 2
            },
            {
                "rule_name": "被动语态",
                "rule_summary": "表示动作的承受者，结构：be + done",
                "user_id": 2
            },
            {
                "rule_name": "定语从句",
                "rule_summary": "修饰名词的从句，使用关系代词连接",
                "user_id": 2
            },
        ]
        
        for r in user2_rules:
            # 检查是否已存在
            existing = session.query(GrammarRule).filter(
                GrammarRule.rule_name == r["rule_name"],
                GrammarRule.user_id == r["user_id"]
            ).first()
            
            if existing:
                print(f"  ⏭️  '{r['rule_name']}' 已存在，跳过")
                continue
            
            rule = GrammarRule(
                user_id=r["user_id"],
                rule_name=r["rule_name"],
                rule_summary=r["rule_summary"],
                source=SourceType.MANUAL,
                is_starred=False
            )
            session.add(rule)
            print(f"  ✅ 添加: {r['rule_name']}")
        
        session.commit()
        
        print("\n" + "="*60)
        print("✅ 测试语法规则添加完成！")
        print("="*60)
        
        # 统计
        user1_count = session.query(GrammarRule).filter(
            GrammarRule.user_id == 1
        ).count()
        
        user2_count = session.query(GrammarRule).filter(
            GrammarRule.user_id == 2
        ).count()
        
        print(f"\n📊 统计：")
        print(f"  User 1: {user1_count} 条语法规则")
        print(f"  User 2: {user2_count} 条语法规则")
        
        print(f"\n🧪 测试步骤：")
        print(f"1. 重启后端服务器")
        print(f"2. 登录 User 1 查看 Grammar 列表")
        print(f"   - 应该看到 {user1_count} 条规则")
        print(f"3. 登录 User 2 查看 Grammar 列表")
        print(f"   - 应该看到 {user2_count} 条规则")
        print(f"   - 包含：现在进行时、被动语态、定语从句")
        print(f"4. ✅ Grammar 数据隔离成功！")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()

