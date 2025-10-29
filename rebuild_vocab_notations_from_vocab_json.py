#!/usr/bin/env python3
"""
根据 vocab.json 重建 vocab_notations/default_user.json
确保所有 text_id, sentence_id, token_id 都与 vocab.json 中的 examples 对应
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

def rebuild_vocab_notations(user_id: str = "default_user"):
    """
    根据 vocab.json 重建 vocab_notations
    
    Args:
        user_id: 用户ID
    """
    print("=" * 70)
    print(f"🔄 开始根据 vocab.json 重建 vocab_notations")
    print(f"📋 用户ID: {user_id}")
    print("=" * 70)
    
    # 读取 vocab.json
    vocab_json_path = BACKEND_DIR / "data" / "current" / "vocab.json"
    if not vocab_json_path.exists():
        print(f"❌ 错误：vocab.json 不存在：{vocab_json_path}")
        return False
    
    print(f"\n📖 读取 vocab.json：{vocab_json_path}")
    with open(vocab_json_path, "r", encoding="utf-8") as f:
        vocab_data = json.load(f)
    
    print(f"  找到 {len(vocab_data)} 个词汇")
    
    # 读取现有的 vocab_notations（用于备份信息）
    vocab_notations_path = BACKEND_DIR / "data" / "current" / "vocab_notations" / f"{user_id}.json"
    old_notations = []
    if vocab_notations_path.exists():
        print(f"\n📋 读取现有的 vocab_notations：{vocab_notations_path}")
        with open(vocab_notations_path, "r", encoding="utf-8") as f:
            old_notations = json.load(f)
        print(f"  现有记录数：{len(old_notations)}")
    
    # 收集所有需要创建的 vocab_notations
    new_notations = []
    notation_keys = set()  # 用于去重：user_id:text_id:sentence_id:token_id
    
    print(f"\n🔍 处理 vocab.json 中的 examples...")
    
    for vocab_item in vocab_data:
        vocab_id = vocab_item.get("vocab_id")
        vocab_body = vocab_item.get("vocab_body", "")
        examples = vocab_item.get("examples", [])
        
        if not examples:
            continue
        
        for example in examples:
            text_id = example.get("text_id")
            sentence_id = example.get("sentence_id")
            token_indices = example.get("token_indices", [])
            
            if not all([text_id, sentence_id is not None, token_indices]):
                print(f"  ⚠️  跳过无效的 example：vocab_id={vocab_id}, text_id={text_id}, sentence_id={sentence_id}, token_indices={token_indices}")
                continue
            
            # 为每个 token_index 创建一个 vocab_notation
            for token_id in token_indices:
                if token_id is None:
                    continue
                
                # 创建唯一键
                key = f"{user_id}:{text_id}:{sentence_id}:{token_id}"
                
                if key in notation_keys:
                    print(f"  ⚠️  跳过重复记录：vocab_id={vocab_id}, {text_id}:{sentence_id}:{token_id}")
                    continue
                
                notation_keys.add(key)
                
                # 创建 vocab_notation 记录
                notation = {
                    "user_id": user_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "token_id": token_id,
                    "vocab_id": vocab_id,
                    "created_at": datetime.now().isoformat()
                }
                new_notations.append(notation)
                
                print(f"  ✅ vocab_id={vocab_id} ({vocab_body[:20]}...), "
                      f"text_id={text_id}, sentence_id={sentence_id}, token_id={token_id}")
    
    print(f"\n📊 统计信息：")
    print(f"  - 处理了 {len(vocab_data)} 个词汇")
    print(f"  - 生成了 {len(new_notations)} 条 vocab_notation 记录")
    print(f"  - 原有记录数：{len(old_notations)}")
    
    if len(new_notations) == 0:
        print(f"\n⚠️  警告：没有生成任何记录！")
        return False
    
    # 按 text_id, sentence_id, token_id 排序
    new_notations.sort(key=lambda x: (x["text_id"], x["sentence_id"], x["token_id"]))
    
    # 备份旧文件
    if vocab_notations_path.exists():
        backup_path = vocab_notations_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        print(f"\n💾 备份旧文件到：{backup_path}")
        vocab_notations_path.rename(backup_path)
    
    # 写入新文件
    print(f"\n💾 写入新的 vocab_notations 文件：{vocab_notations_path}")
    vocab_notations_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(vocab_notations_path, "w", encoding="utf-8") as f:
        json.dump(new_notations, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功写入 {len(new_notations)} 条记录")
    
    # 验证写入的文件
    print(f"\n🔍 验证写入的文件...")
    with open(vocab_notations_path, "r", encoding="utf-8") as f:
        verify_data = json.load(f)
    
    if len(verify_data) == len(new_notations):
        print(f"✅ 验证通过：文件包含 {len(verify_data)} 条记录")
        
        # 显示前几条记录作为示例
        print(f"\n📋 前 5 条记录示例：")
        for i, notation in enumerate(verify_data[:5], 1):
            print(f"  {i}. vocab_id={notation['vocab_id']}, "
                  f"text_id={notation['text_id']}, "
                  f"sentence_id={notation['sentence_id']}, "
                  f"token_id={notation['token_id']}")
        
        return True
    else:
        print(f"❌ 验证失败：文件包含 {len(verify_data)} 条记录，期望 {len(new_notations)} 条")
        return False

if __name__ == "__main__":
    # 默认用户
    user_id = "default_user"
    
    # 如果提供了命令行参数，使用指定的用户ID
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    
    success = rebuild_vocab_notations(user_id)
    sys.exit(0 if success else 1)
