#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocab 数据库适配流程详细验证

展示完整的数据转换过程：
1. FastAPI接收请求
2. VocabManagerDB处理
3. Adapter转换Model<->DTO
4. 数据库操作
"""
import sys
import os

# 添加backend路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from backend.data_managers import VocabManagerDB
from backend.adapters import VocabAdapter
from database_system.business_logic.models import VocabExpression as VocabModel
from backend.data_managers.data_classes_new import VocabExpression as VocabDTO


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    else:
        print("-"*70)


def print_step(step_num, description):
    """打印步骤"""
    print(f"\n[步骤{step_num}] {description}")
    print_separator()


def inspect_object(obj, name="Object"):
    """检查对象详情"""
    print(f"\n{name}:")
    print(f"  类型: {type(obj).__name__}")
    print(f"  模块: {type(obj).__module__}")
    
    if hasattr(obj, '__dict__'):
        print(f"  属性:")
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):
                value_str = str(value)[:50]
                if len(str(value)) > 50:
                    value_str += "..."
                print(f"    - {key}: {value_str} (类型: {type(value).__name__})")


def test_complete_flow():
    """完整流程测试"""
    
    print_separator("Vocab 数据库适配完整流程验证")
    print("\n本测试将展示从API层到数据库层的完整数据转换过程")
    
    # ===== 步骤1: 初始化数据库连接 =====
    print_step(1, "初始化数据库连接")
    
    db_manager = DatabaseManager('development')
    session = db_manager.get_session()
    print(f"[OK] 数据库连接成功")
    print(f"     数据库URL: {db_manager.database_url}")
    print(f"     Session类型: {type(session).__name__}")
    
    # ===== 步骤2: 创建VocabManagerDB =====
    print_step(2, "创建VocabManagerDB实例 (模拟FastAPI路由中的操作)")
    
    vocab_manager = VocabManagerDB(session)
    print(f"[OK] VocabManagerDB创建成功")
    print(f"     Manager类型: {type(vocab_manager).__name__}")
    print(f"     Manager内部db_manager: {type(vocab_manager.db_manager).__name__}")
    
    # ===== 步骤3: 查询词汇（展示完整转换） =====
    print_step(3, "查询词汇 - 展示Model->DTO转换")
    
    print("\n>>> vocab_manager.get_vocab_by_id(1)")
    print("     这是FastAPI路由会调用的方法")
    print_separator()
    
    # 3.1 从数据库获取Model
    print("\n[3.1] 内部操作: 从数据库获取VocabModel")
    vocab_model = vocab_manager.db_manager.get_vocab(1)
    
    if vocab_model:
        print(f"[OK] 获取到VocabModel")
        inspect_object(vocab_model, "VocabModel (数据库ORM对象)")
        print(f"\n关键字段:")
        print(f"  vocab_id: {vocab_model.vocab_id}")
        print(f"  vocab_body: {vocab_model.vocab_body}")
        print(f"  source: {vocab_model.source} (类型: {type(vocab_model.source).__name__})")
        print(f"  source.value: {vocab_model.source.value}")
        print(f"  is_starred: {vocab_model.is_starred}")
        print(f"  examples: {len(vocab_model.examples) if vocab_model.examples else 0} 个")
        
        # 3.2 使用Adapter转换为DTO
        print("\n[3.2] 使用VocabAdapter转换: Model -> DTO")
        print("     >>> VocabAdapter.model_to_dto(vocab_model)")
        print_separator()
        
        vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=True)
        
        print(f"[OK] 转换成功，得到VocabDTO")
        inspect_object(vocab_dto, "VocabDTO (业务数据对象)")
        print(f"\n关键字段:")
        print(f"  vocab_id: {vocab_dto.vocab_id}")
        print(f"  vocab_body: {vocab_dto.vocab_body}")
        print(f"  source: {vocab_dto.source} (类型: {type(vocab_dto.source).__name__})")
        print(f"  is_starred: {vocab_dto.is_starred}")
        print(f"  examples: {len(vocab_dto.examples)} 个")
        
        # 3.3 展示转换前后对比
        print("\n[3.3] 转换前后对比")
        print_separator()
        print(f"  字段              | Model                    | DTO")
        print(f"  source           | {vocab_model.source} | {vocab_dto.source}")
        print(f"  source类型       | {type(vocab_model.source).__name__:20} | {type(vocab_dto.source).__name__}")
        print(f"  examples类型     | relationship             | list[VocabExampleDTO]")
        
        print("\n[重点] 数据转换:")
        print(f"  1. source: SourceType.{vocab_model.source.name} -> 字符串 '{vocab_dto.source}'")
        print(f"  2. examples: SQLAlchemy关系 -> Python dataclass列表")
        print(f"  3. 对象类型: ORM Model -> 业务DTO")
    else:
        print("[INFO] 数据库中没有ID=1的词汇，使用其他测试")
    
    # ===== 步骤4: 创建词汇（展示DTO->Model转换） =====
    print_step(4, "创建词汇 - 展示DTO->Model转换")
    
    test_vocab_body = "flow_test_vocab"
    test_explanation = "流程测试词汇"
    
    # 清理旧数据
    existing = vocab_manager.get_vocab_by_body(test_vocab_body)
    if existing:
        print(f"[清理] 删除已存在的测试词汇 ID={existing.vocab_id}")
        vocab_manager.delete_vocab(existing.vocab_id)
        session.commit()
    
    print(f"\n>>> vocab_manager.add_new_vocab('{test_vocab_body}', '{test_explanation}')")
    print("     这是FastAPI路由中POST请求会调用的方法")
    print_separator()
    
    print("\n[4.1] 调用VocabManagerDB.add_new_vocab()")
    print(f"     参数: vocab_body='{test_vocab_body}', explanation='{test_explanation}'")
    print(f"           source='manual', is_starred=True")
    
    new_vocab = vocab_manager.add_new_vocab(
        vocab_body=test_vocab_body,
        explanation=test_explanation,
        source="manual",
        is_starred=True
    )
    session.commit()
    
    print(f"\n[4.2] 返回结果 (VocabDTO)")
    inspect_object(new_vocab, "创建的VocabDTO")
    print(f"\n关键字段:")
    print(f"  vocab_id: {new_vocab.vocab_id} (数据库自动生成)")
    print(f"  vocab_body: {new_vocab.vocab_body}")
    print(f"  source: {new_vocab.source} (已转换为字符串)")
    print(f"  is_starred: {new_vocab.is_starred}")
    
    # ===== 步骤5: 查询刚创建的词汇（验证完整性） =====
    print_step(5, "查询刚创建的词汇 - 验证数据完整性")
    
    print(f"\n>>> vocab_manager.get_vocab_by_id({new_vocab.vocab_id})")
    queried_vocab = vocab_manager.get_vocab_by_id(new_vocab.vocab_id)
    
    if queried_vocab:
        print(f"[OK] 查询成功")
        print(f"\n验证数据:")
        print(f"  vocab_id匹配: {queried_vocab.vocab_id == new_vocab.vocab_id}")
        print(f"  vocab_body匹配: {queried_vocab.vocab_body == new_vocab.vocab_body}")
        print(f"  source匹配: {queried_vocab.source == new_vocab.source}")
        print(f"  is_starred匹配: {queried_vocab.is_starred == new_vocab.is_starred}")
    
    # ===== 步骤6: 添加例句 =====
    print_step(6, "添加例句 - 展示关联数据处理")
    
    print(f"\n>>> vocab_manager.add_vocab_example(vocab_id={new_vocab.vocab_id}, ...)")
    
    example = vocab_manager.add_vocab_example(
        vocab_id=new_vocab.vocab_id,
        text_id=1,
        sentence_id=1,
        context_explanation="这是一个流程测试例句",
        token_indices=[1, 2, 3]
    )
    session.commit()
    
    print(f"[OK] 例句添加成功")
    inspect_object(example, "VocabExampleDTO")
    print(f"\n关键字段:")
    print(f"  vocab_id: {example.vocab_id}")
    print(f"  text_id: {example.text_id}")
    print(f"  sentence_id: {example.sentence_id}")
    print(f"  token_indices: {example.token_indices}")
    
    # ===== 步骤7: 再次查询，包含例句 =====
    print_step(7, "查询词汇（包含例句）")
    
    vocab_with_examples = vocab_manager.get_vocab_by_id(new_vocab.vocab_id)
    
    print(f"[OK] 查询成功")
    print(f"\n词汇信息:")
    print(f"  ID: {vocab_with_examples.vocab_id}")
    print(f"  内容: {vocab_with_examples.vocab_body}")
    print(f"  例句数量: {len(vocab_with_examples.examples)}")
    
    if vocab_with_examples.examples:
        ex = vocab_with_examples.examples[0]
        print(f"\n第一个例句:")
        print(f"  text_id: {ex.text_id}")
        print(f"  sentence_id: {ex.sentence_id}")
        print(f"  context: {ex.context_explanation}")
        print(f"  token_indices: {ex.token_indices}")
    
    # ===== 步骤8: 模拟FastAPI返回格式 =====
    print_step(8, "模拟FastAPI返回格式")
    
    api_response = {
        "success": True,
        "data": {
            "vocab_id": vocab_with_examples.vocab_id,
            "vocab_body": vocab_with_examples.vocab_body,
            "explanation": vocab_with_examples.explanation,
            "source": vocab_with_examples.source,
            "is_starred": vocab_with_examples.is_starred,
            "examples": [
                {
                    "vocab_id": ex.vocab_id,
                    "text_id": ex.text_id,
                    "sentence_id": ex.sentence_id,
                    "context_explanation": ex.context_explanation,
                    "token_indices": ex.token_indices
                }
                for ex in vocab_with_examples.examples
            ]
        }
    }
    
    print("\nFastAPI会返回的JSON:")
    import json
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    # ===== 步骤9: 清理测试数据 =====
    print_step(9, "清理测试数据")
    
    vocab_manager.delete_vocab(new_vocab.vocab_id)
    session.commit()
    print(f"[OK] 已删除测试词汇 ID={new_vocab.vocab_id}")
    
    # 关闭Session
    session.close()
    
    # ===== 总结 =====
    print_separator("流程总结")
    
    print("""
完整数据流转路径:

1. FastAPI路由接收请求
   └─> vocab_manager = VocabManagerDB(session)
   
2. 调用Manager方法
   └─> vocab = vocab_manager.get_vocab_by_id(id)
   
3. Manager内部操作
   ├─> vocab_model = db_manager.get_vocab(id)  # 获取ORM Model
   └─> vocab_dto = VocabAdapter.model_to_dto(vocab_model)  # 转换为DTO
   
4. Adapter转换细节
   ├─> source: SourceType枚举 -> 字符串 "auto"/"qa"/"manual"
   ├─> examples: SQLAlchemy关系 -> list[VocabExampleDTO]
   └─> Model对象 -> dataclass对象
   
5. 返回给FastAPI
   └─> FastAPI自动将DTO序列化为JSON返回前端

关键点:
✓ FastAPI只需要调用VocabManagerDB方法，无需处理转换
✓ 所有数据转换都在VocabAdapter中完成
✓ Session通过依赖注入自动管理
✓ DTO保证了类型安全和数据一致性
""")
    
    print("\n[SUCCESS] 流程验证完成!")


if __name__ == "__main__":
    try:
        test_complete_flow()
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

