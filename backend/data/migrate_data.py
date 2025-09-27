#!/usr/bin/env python3
"""
数据迁移脚本
用于将数据从旧位置迁移到新的统一数据结构
"""

import os
import shutil
import json
from pathlib import Path

def migrate_articles():
    """迁移文章数据到新的articles目录"""
    current_dir = Path(__file__).parent
    current_articles_dir = current_dir / "current" / "articles"
    old_result_dir = current_dir.parent.parent / "real_data_raw" / "result"
    
    # 确保目标目录存在
    current_articles_dir.mkdir(parents=True, exist_ok=True)
    
    if old_result_dir.exists():
        print(f"迁移文章数据从 {old_result_dir} 到 {current_articles_dir}")
        for file in old_result_dir.glob("*.json"):
            shutil.copy2(file, current_articles_dir)
            print(f"已复制: {file.name}")
    else:
        print(f"源目录不存在: {old_result_dir}")

def verify_data_structure():
    """验证数据结构完整性"""
    current_dir = Path(__file__).parent / "current"
    
    required_files = [
        "vocab.json",
        "grammar.json", 
        "dialogue_history.json",
        "dialogue_record.json"
    ]
    
    required_dirs = ["articles"]
    
    print("验证数据结构...")
    
    # 检查必需文件
    for file in required_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"✅ {file} 存在")
        else:
            print(f"❌ {file} 缺失")
    
    # 检查必需目录
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ 目录存在")
            # 列出目录内容
            files = list(dir_path.glob("*"))
            print(f"   包含 {len(files)} 个文件")
        else:
            print(f"❌ {dir_name}/ 目录缺失")

def backup_current_data():
    """备份当前数据"""
    current_dir = Path(__file__).parent / "current"
    backup_dir = Path(__file__).parent / "backup" / "current_backup"
    
    if current_dir.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(current_dir, backup_dir, dirs_exist_ok=True)
        print(f"数据已备份到: {backup_dir}")

if __name__ == "__main__":
    print("=== 数据迁移工具 ===")
    
    # 备份现有数据
    print("\n1. 备份现有数据...")
    backup_current_data()
    
    # 迁移文章数据
    print("\n2. 迁移文章数据...")
    migrate_articles()
    
    # 验证数据结构
    print("\n3. 验证数据结构...")
    verify_data_structure()
    
    print("\n✅ 数据迁移完成！")
