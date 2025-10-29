#!/usr/bin/env python3
"""
迁移脚本：将 AskedToken JSON 数据迁移到 VocabNotation JSON 文档
只迁移 type: "token" 且有 vocab_id 的记录
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# 切换到 backend 目录并添加到路径（用于相对导入）
os.chdir(str(BACKEND_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 导入管理器（使用相对导入）
from data_managers.unified_notation_manager import get_unified_notation_manager

def migrate_asked_tokens_to_vocab_notations(user_id: str = "default_user"):
    """
    迁移 AskedToken 数据到 VocabNotation
    
    Args:
        user_id: 要迁移的用户ID
    """
    print("=" * 60)
    print(f"🚀 开始迁移 AskedToken 到 VocabNotation")
    print(f"📋 用户ID: {user_id}")
    print("=" * 60)
    
    try:
        # 使用 JSON 文件模式，启用向后兼容
        manager = get_unified_notation_manager(
            use_database=False,
            use_legacy_compatibility=True
        )
        
        # 执行迁移（但迁移方法会迁移所有类型）
        # 我们先看一下会迁移哪些记录
        print("\n📊 准备迁移以下 VocabNotation 记录：")
        
        # 读取 asked_tokens 数据来预览
        import json
        # 使用相对于 backend 目录的路径
        current_dir = Path.cwd()
        asked_tokens_path = current_dir / "data" / "current" / "asked_tokens" / f"{user_id}.json"
        if asked_tokens_path.exists():
            with open(asked_tokens_path, "r", encoding="utf-8") as f:
                asked_tokens = json.load(f)
            
            vocab_tokens = [
                token for token in asked_tokens
                if token.get("type") == "token" 
                and token.get("sentence_token_id") is not None
                and token.get("vocab_id") is not None
            ]
            
            print(f"  找到 {len(vocab_tokens)} 条需要迁移的 VocabNotation 记录：")
            for token in vocab_tokens:
                print(f"    - text_id={token['text_id']}, "
                      f"sentence_id={token['sentence_id']}, "
                      f"token_id={token['sentence_token_id']}, "
                      f"vocab_id={token['vocab_id']}")
            
            grammar_tokens = [
                token for token in asked_tokens
                if token.get("type") == "sentence" 
                and token.get("grammar_id") is not None
            ]
            
            if grammar_tokens:
                print(f"\n⚠️  注意：还有 {len(grammar_tokens)} 条 GrammarNotation 记录")
                print("  （迁移方法也会迁移这些，但本次只关注 VocabNotation）")
        
        print("\n" + "=" * 60)
        print("🔄 开始执行迁移...")
        print("=" * 60 + "\n")
        
        # 执行迁移
        success = manager.migrate_legacy_asked_tokens(user_id=user_id)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 迁移完成！")
            print("=" * 60)
            
            # 验证迁移结果
            current_dir = Path.cwd()
            vocab_notations_path = current_dir / "data" / "current" / "vocab_notations" / f"{user_id}.json"
            if vocab_notations_path.exists():
                with open(vocab_notations_path, "r", encoding="utf-8") as f:
                    vocab_notations = json.load(f)
                
                print(f"\n📊 验证迁移结果：")
                print(f"  VocabNotation 记录数: {len(vocab_notations)}")
                
                if vocab_notations:
                    print(f"\n  迁移的 VocabNotation 记录：")
                    for notation in vocab_notations:
                        print(f"    - text_id={notation.get('text_id')}, "
                              f"sentence_id={notation.get('sentence_id')}, "
                              f"token_id={notation.get('token_id')}, "
                              f"vocab_id={notation.get('vocab_id')}")
            else:
                print(f"\n⚠️  警告：VocabNotation 文件不存在！")
            
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ 迁移失败！")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ 迁移过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 默认迁移 default_user
    user_id = "default_user"
    
    # 如果提供了命令行参数，使用指定的用户ID
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    
    success = migrate_asked_tokens_to_vocab_notations(user_id)
    sys.exit(0 if success else 1)
