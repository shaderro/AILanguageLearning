#!/usr/bin/env python3
"""
重建数据库脚本
⚠️ 警告：此操作会删除所有现有数据！
"""

print("\n" + "="*60)
print("⚠️  警告：即将重建数据库")
print("="*60)
print("此操作将：")
print("  1. 删除所有现有数据")
print("  2. 删除所有表")
print("  3. 重新创建所有表（包含新的 User 模型）")
print("="*60)

# 询问确认
response = input("\n确定要继续吗？(输入 yes 继续): ")

if response.lower() != 'yes':
    print("❌ 操作已取消")
    exit(0)

print("\n开始重建数据库...\n")

try:
    from database_system.database_manager import DatabaseManager
    from database_system.business_logic.models import Base
    
    db_manager = DatabaseManager('development')
    engine = db_manager.get_engine()  # ✅ 使用 get_engine() 方法
    
    print("📋 步骤 1: 删除所有表...")
    Base.metadata.drop_all(engine)
    print("   ✅ 所有表已删除")
    
    print("\n📋 步骤 2: 创建所有表...")
    Base.metadata.create_all(engine)
    print("   ✅ 所有表已创建")
    
    print("\n" + "="*60)
    print("✅ 数据库重建完成！")
    print("="*60)
    print("\n新的数据库结构包含：")
    print("  - User 表 (user_id: Integer, password_hash)")
    print("  - AskedToken 表 (user_id: Integer)")
    print("  - VocabNotation 表 (user_id: Integer)")
    print("  - GrammarNotation 表 (user_id: Integer)")
    print("  - 以及其他所有表...")
    print("\n现在可以启动服务器并测试认证功能了！")
    print("  python frontend/my-web-ui/backend/main.py")
    print("\n")
    
except Exception as e:
    print(f"\n❌ 错误：数据库重建失败")
    print(f"   原因：{e}")
    import traceback
    traceback.print_exc()
    exit(1)

