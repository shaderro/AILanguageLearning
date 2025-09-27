import json
import os
from typing import Dict, List, Tuple


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def load_vocab_file(vocab_file: str) -> List[Dict]:
    if os.path.exists(vocab_file):
        with open(vocab_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def assign_next_vocab_id(existing_vocabs: List[Dict]) -> int:
    existing_ids = [int(v.get('vocab_id', 0) or 0) for v in existing_vocabs]
    return (max(existing_ids) + 1) if existing_ids else 1


def upsert_vocab(existing_vocabs: List[Dict], vocab_dict: Dict) -> Tuple[List[Dict], int]:
    # 如果根据 vocab_body 已存在，则更新；否则追加新条目并分配新 ID
    target_index = None
    for idx, item in enumerate(existing_vocabs):
        if str(item.get('vocab_body', '')).strip().lower() == str(vocab_dict.get('vocab_body', '')).strip().lower():
            target_index = idx
            break

    if target_index is None:
        next_id = assign_next_vocab_id(existing_vocabs)
        vocab_dict = {**vocab_dict, 'vocab_id': next_id}
        existing_vocabs.append(vocab_dict)
        return existing_vocabs, next_id
    else:
        # 保留原 ID，覆盖其他字段
        original_id = int(existing_vocabs[target_index].get('vocab_id', 0) or 0)
        vocab_dict = {**vocab_dict, 'vocab_id': original_id}
        existing_vocabs[target_index] = vocab_dict
        return existing_vocabs, original_id


def save_vocab_to_json(vocab_file: str, vocab_dict: Dict) -> Tuple[int, int]:
    """
    将 vocab_dict 写入 vocab_file：
    - 若同名 vocab_body 已存在则更新并保留原 ID
    - 否则追加并分配新的递增 ID

    返回: (vocab_id, total_count)
    """
    # 统一日志，便于排查
    print("💾 [Backend] Attempting to save vocab to JSON file...")
    print(f"📂 [Backend] Target file: {vocab_file}")

    ensure_parent_dir(vocab_file)
    existing_vocabs = load_vocab_file(vocab_file)
    print(f"📖 [Backend] Loaded {len(existing_vocabs)} existing vocab items")

    updated_list, final_id = upsert_vocab(existing_vocabs, vocab_dict)

    # 计算本次是新增还是覆盖（通过 vocab_id 与 vocab_body 一致判断）
    is_update = any(
        int(item.get('vocab_id', 0) or 0) == final_id and
        str(item.get('vocab_body', '')).strip().lower() == str(vocab_dict.get('vocab_body', '')).strip().lower()
        for item in updated_list
    )

    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=2)

    print(f"✅ [Backend] Saved vocab to file. vocab_id: {final_id} ({'update' if is_update else 'create'})")
    print(f"📈 [Backend] Total vocab count: {len(updated_list)}")

    return final_id, len(updated_list)


