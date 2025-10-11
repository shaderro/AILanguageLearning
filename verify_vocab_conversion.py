#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证Vocab数据转换
"""
import sys
import os
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from backend.data_managers import VocabManagerDB
from backend.adapters import VocabAdapter

def main():
    print("\n" + "="*60)
    print("Vocab 数据转换验证")
    print("="*60)
    
    # 1. 连接数据库
    print("\n[1] 连接数据库...")
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    print("    [OK] 连接成功")
    
    # 2. 创建Manager
    print("\n[2] 创建VocabManagerDB...")
    vocab_manager = VocabManagerDB(session)
    print("    [OK] Manager创建成功")
    print(f"    类型: {type(vocab_manager).__name__}")
    
    # 3. 查询词汇
    print("\n[3] 查询词汇 ID=1...")
    
    # 3.1 获取Model（内部操作）
    print("\n    [3.1] 数据库层返回VocabModel:")
    vocab_model = vocab_manager.db_manager.get_vocab(1)
    if vocab_model:
        print(f"          vocab_id: {vocab_model.vocab_id}")
        print(f"          vocab_body: {vocab_model.vocab_body}")
        print(f"          source: {vocab_model.source} (类型: {type(vocab_model.source).__name__})")
        print(f"          is_starred: {vocab_model.is_starred}")
    
        # 3.2 转换为DTO
        print("\n    [3.2] Adapter转换为VocabDTO:")
        vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=True)
        print(f"          vocab_id: {vocab_dto.vocab_id}")
        print(f"          vocab_body: {vocab_dto.vocab_body}")
        print(f"          source: '{vocab_dto.source}' (类型: {type(vocab_dto.source).__name__})")
        print(f"          is_starred: {vocab_dto.is_starred}")
        print(f"          examples: {len(vocab_dto.examples)} 个")
        
        # 3.3 对比
        print("\n    [3.3] 转换结果:")
        print(f"          Model.source: {vocab_model.source} (枚举)")
        print(f"          DTO.source:   '{vocab_dto.source}' (字符串)")
        print(f"          转换成功: {vocab_model.source.value.lower() == vocab_dto.source}")
    
    # 4. 通过Manager调用（FastAPI会这样用）
    print("\n[4] FastAPI路由会这样调用:")
    print("    vocab = vocab_manager.get_vocab_by_id(1)")
    
    vocab = vocab_manager.get_vocab_by_id(1)
    print(f"\n    返回的直接就是DTO:")
    print(f"      类型: {type(vocab).__name__}")
    print(f"      source: '{vocab.source}' (已经是字符串)")
    print(f"      FastAPI直接返回给前端，无需任何转换")
    
    # 5. 模拟FastAPI返回
    print("\n[5] FastAPI返回给前端的JSON:")
    response = {
        "success": True,
        "data": {
            "vocab_id": vocab.vocab_id,
            "vocab_body": vocab.vocab_body,
            "source": vocab.source,  # 直接用，已经是字符串
            "is_starred": vocab.is_starred
        }
    }
    
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    # 总结
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    print("""
数据转换位置:

FastAPI (vocab_routes.py)
    | 调用: vocab_manager.get_vocab_by_id(1)
    v
VocabManagerDB (vocab_manager_db.py)
    | 1. 调用: db_manager.get_vocab(1)
    | 2. 得到: VocabModel (source=SourceType.AUTO)
    | 3. 调用: VocabAdapter.model_to_dto(model)
    | 4. 得到: VocabDTO (source="auto")
    v
返回DTO给FastAPI
    | FastAPI直接返回，无需转换
    v
前端收到JSON: {"source": "auto"}

关键点:
- FastAPI不需要处理任何转换
- 转换在VocabManagerDB和Adapter内部完成
- FastAPI只需要调用方法，得到DTO，返回即可
""")
    
    session.close()
    print("[SUCCESS] 验证完成!")

if __name__ == "__main__":
    main()

