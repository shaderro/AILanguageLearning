"""
检查数据库中的用户数据
"""
import sys
import os

# 添加路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from database_system.business_logic.models import User

def main():
    print("\n" + "="*60)
    print("数据库用户检查")
    print("="*60)
    
    # 连接数据库
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    
    try:
        # 查询所有用户
        users = session.query(User).all()
        
        print(f"\n✅ 找到 {len(users)} 个用户：\n")
        
        if len(users) == 0:
            print("❌ 数据库中没有用户！")
            print("\n这就是为什么登录失败的原因。")
            print("\n解决方案：")
            print("1. 使用前端的'注册'功能创建新用户")
            print("2. 或者运行 create_test_users.py 脚本创建测试用户")
        else:
            print("| User ID | 密码哈希 (前20字符) | 创建时间 |")
            print("|---------|---------------------|----------|")
            for user in users:
                hash_preview = user.password_hash[:20] + "..." if len(user.password_hash) > 20 else user.password_hash
                created_at = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "Unknown"
                print(f"| {user.user_id:7} | {hash_preview:19} | {created_at} |")
            
            print("\n⚠️ 注意：USER_CREDENTIALS.md 中的密码是明文，但数据库中只存储加密后的哈希值。")
            print("如果用户是通过注册创建的，密码会被加密存储。")
            print("如果登录失败，说明数据库中的密码哈希与你输入的密码不匹配。")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()

