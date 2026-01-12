#!/usr/bin/env python3
"""
从备份恢复数据库
⚠️ 警告：此操作会覆盖当前数据库文件！
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_current_database(db_path):
    """备份当前数据库文件"""
    if not os.path.exists(db_path):
        print(f"⚠️  当前数据库文件不存在: {db_path}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.replace('.db', f'_backup_before_restore_{timestamp}.db')
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已备份当前数据库: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def restore_from_backup(backup_path, db_path):
    """从备份文件恢复数据库"""
    if not os.path.exists(backup_path):
        print(f"❌ 备份文件不存在: {backup_path}")
        return False
    
    try:
        # 1. 备份当前数据库
        current_backup = backup_current_database(db_path)
        
        # 2. 从备份恢复
        shutil.copy2(backup_path, db_path)
        print(f"✅ 已从备份恢复数据库: {backup_path} -> {db_path}")
        
        # 3. 验证恢复结果
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"✅ 恢复成功！数据库文件大小: {file_size / 1024 / 1024:.2f} MB")
            
            # 检查数据库内容
            try:
                from database_system.database_manager import DatabaseManager
                from database_system.business_logic.models import User, OriginalText
                
                db_manager = DatabaseManager('development')
                session = db_manager.get_session()
                
                user_count = session.query(User).count()
                text_count = session.query(OriginalText).count()
                
                session.close()
                
                print(f"✅ 数据库内容验证:")
                print(f"   - 用户数: {user_count}")
                print(f"   - 文章数: {text_count}")
                
                return True
            except Exception as e:
                print(f"⚠️  数据库验证失败: {e}")
                print(f"   但文件已恢复，请手动验证")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_available_backups():
    """列出可用的备份文件"""
    data_dir = Path("database_system/data_storage/data")
    
    if not data_dir.exists():
        print(f"❌ 数据目录不存在: {data_dir}")
        return []
    
    backup_files = sorted(
        data_dir.glob("dev_backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return backup_files

def main():
    print("\n" + "="*60)
    print("🔄 从备份恢复数据库")
    print("="*60)
    
    # 列出可用备份
    backups = list_available_backups()
    
    if not backups:
        print("❌ 没有找到备份文件")
        return
    
    print(f"\n📋 找到 {len(backups)} 个备份文件:")
    print("-" * 60)
    
    for i, backup in enumerate(backups[:10], 1):  # 只显示前10个
        file_size = backup.stat().st_size / 1024 / 1024
        mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f"{i}. {backup.name}")
        print(f"   大小: {file_size:.2f} MB")
        print(f"   时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    if len(backups) > 10:
        print(f"   ... 还有 {len(backups) - 10} 个备份文件")
    
    # 选择备份文件
    print("-" * 60)
    print("请选择要恢复的备份文件（输入序号，或按 Enter 选择最新的）:")
    
    choice = input("> ").strip()
    
    if not choice:
        selected_backup = backups[0]
    else:
        try:
            index = int(choice) - 1
            if 0 <= index < len(backups):
                selected_backup = backups[index]
            else:
                print("❌ 无效的序号")
                return
        except ValueError:
            print("❌ 无效的输入")
            return
    
    print(f"\n✅ 已选择备份文件: {selected_backup.name}")
    
    # 确认
    print("\n" + "="*60)
    print("⚠️  警告：此操作会覆盖当前数据库文件！")
    print("="*60)
    print("当前数据库将被备份，然后从以下备份恢复:")
    print(f"  {selected_backup.name}")
    print("="*60)
    
    response = input("\n确定要继续吗？(输入 yes 继续): ")
    
    if response.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    # 恢复数据库
    db_path = "database_system/data_storage/data/dev.db"
    
    print("\n开始恢复数据库...")
    success = restore_from_backup(str(selected_backup), db_path)
    
    if success:
        print("\n" + "="*60)
        print("✅ 数据库恢复成功！")
        print("="*60)
        print("\n下一步：")
        print("1. 重启后端服务器")
        print("2. 验证数据是否正确")
        print("3. 测试登录和文章访问")
    else:
        print("\n" + "="*60)
        print("❌ 数据库恢复失败")
        print("="*60)

if __name__ == "__main__":
    main()

