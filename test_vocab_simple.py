#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocab 数据库适配简化测试

测试目标：
1. 数据库连接
2. VocabManagerDB CRUD操作
3. Model <-> DTO 转换
4. 完整的业务流程
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

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_database_connection():
    """测试1: 数据库连接"""
    print_header("测试1: 数据库连接")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        print("[OK] 数据库连接成功")
        print(f"    数据库路径: {db_manager.database_url}")
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False


def test_vocab_manager_basic():
    """测试2: VocabManagerDB 基本操作"""
    print_header("测试2: VocabManagerDB 基本操作")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        vocab_manager = VocabManagerDB(session)
        
        print("[OK] VocabManagerDB 初始化成功")
        
        # 获取所有词汇
        vocabs = vocab_manager.get_all_vocabs(limit=5)
        print(f"[OK] 获取词汇列表: {len(vocabs)} 个")
        
        if vocabs:
            print(f"    第一个词汇: {vocabs[0].vocab_body} - {vocabs[0].explanation}")
            print(f"    返回类型: {type(vocabs[0]).__name__}")
            print(f"    是否为DTO: {hasattr(vocabs[0], 'examples')}")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] VocabManagerDB 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_and_query():
    """测试3: 创建和查询词汇"""
    print_header("测试3: 创建和查询词汇")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        vocab_manager = VocabManagerDB(session)
        
        # 创建测试词汇
        test_vocab_body = "test_integration_vocab"
        
        # 检查是否已存在
        existing = vocab_manager.get_vocab_by_body(test_vocab_body)
        if existing:
            print(f"[INFO] 测试词汇已存在，删除旧数据...")
            vocab_manager.delete_vocab(existing.vocab_id)
            session.commit()
        
        # 创建新词汇
        print(f"[+] 创建词汇: {test_vocab_body}")
        new_vocab = vocab_manager.add_new_vocab(
            vocab_body=test_vocab_body,
            explanation="集成测试词汇",
            source="manual",
            is_starred=True
        )
        session.commit()
        
        print(f"[OK] 创建成功:")
        print(f"    ID: {new_vocab.vocab_id}")
        print(f"    内容: {new_vocab.vocab_body}")
        print(f"    解释: {new_vocab.explanation}")
        print(f"    来源: {new_vocab.source}")
        print(f"    收藏: {new_vocab.is_starred}")
        print(f"    类型: {type(new_vocab).__name__}")
        
        # 查询词汇
        print(f"\n[QUERY] 查询词汇 ID={new_vocab.vocab_id}")
        queried_vocab = vocab_manager.get_vocab_by_id(new_vocab.vocab_id)
        
        if queried_vocab:
            print(f"[OK] 查询成功:")
            print(f"    ID: {queried_vocab.vocab_id}")
            print(f"    内容: {queried_vocab.vocab_body}")
            print(f"    解释: {queried_vocab.explanation}")
            print(f"    类型: {type(queried_vocab).__name__}")
        else:
            print(f"[ERROR] 查询失败: 未找到词汇")
        
        # 清理测试数据
        print(f"\n[CLEAN] 清理测试数据...")
        vocab_manager.delete_vocab(new_vocab.vocab_id)
        session.commit()
        print("[OK] 清理完成")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] 创建和查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adapter_conversion():
    """测试4: Adapter Model <-> DTO 转换"""
    print_header("测试4: Adapter Model <-> DTO 转换")
    
    try:
        from backend.data_managers.data_classes_new import VocabExpression as VocabDTO
        from database_system.business_logic.models import SourceType
        
        # 创建一个数据库Model
        print("[CREATE] 创建数据库Model...")
        vocab_model = VocabModel(
            vocab_id=999,
            vocab_body="adapter_test",
            explanation="适配器测试",
            source=SourceType.MANUAL,
            is_starred=False
        )
        print(f"[OK] Model创建成功: {vocab_model.vocab_body}")
        print(f"    类型: {type(vocab_model).__name__}")
        print(f"    source类型: {type(vocab_model.source).__name__}")
        
        # 转换为DTO
        print("\n[CONVERT] Model -> DTO 转换...")
        vocab_dto = VocabAdapter.model_to_dto(vocab_model, include_examples=False)
        print(f"[OK] DTO转换成功:")
        print(f"    ID: {vocab_dto.vocab_id}")
        print(f"    内容: {vocab_dto.vocab_body}")
        print(f"    解释: {vocab_dto.explanation}")
        print(f"    来源: {vocab_dto.source} (类型: {type(vocab_dto.source).__name__})")
        print(f"    收藏: {vocab_dto.is_starred}")
        print(f"    类型: {type(vocab_dto).__name__}")
        
        # 转换回Model
        print("\n[CONVERT] DTO -> Model 转换...")
        vocab_model_2 = VocabAdapter.dto_to_model(vocab_dto, vocab_id=vocab_dto.vocab_id)
        print(f"[OK] Model转换成功:")
        print(f"    ID: {vocab_model_2.vocab_id}")
        print(f"    内容: {vocab_model_2.vocab_body}")
        print(f"    解释: {vocab_model_2.explanation}")
        print(f"    来源: {vocab_model_2.source} (类型: {type(vocab_model_2.source).__name__})")
        print(f"    类型: {type(vocab_model_2).__name__}")
        
        print("\n[OK] Adapter转换测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] Adapter转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vocab_example():
    """测试5: 词汇例句功能"""
    print_header("测试5: 词汇例句功能")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        vocab_manager = VocabManagerDB(session)
        
        # 创建测试词汇
        print("[+] 创建测试词汇...")
        test_vocab = vocab_manager.add_new_vocab(
            vocab_body="example_test_vocab",
            explanation="例句测试词汇",
            source="qa"
        )
        session.commit()
        print(f"[OK] 词汇创建成功: ID={test_vocab.vocab_id}")
        
        # 添加例句
        print(f"\n[+] 添加例句...")
        example = vocab_manager.add_vocab_example(
            vocab_id=test_vocab.vocab_id,
            text_id=1,
            sentence_id=1,
            context_explanation="这是一个测试例句",
            token_indices=[1, 2, 3]
        )
        session.commit()
        
        print(f"[OK] 例句添加成功:")
        print(f"    vocab_id: {example.vocab_id}")
        print(f"    text_id: {example.text_id}")
        print(f"    sentence_id: {example.sentence_id}")
        print(f"    context: {example.context_explanation}")
        print(f"    token_indices: {example.token_indices}")
        print(f"    类型: {type(example).__name__}")
        
        # 查询词汇（包含例句）
        print(f"\n[QUERY] 查询词汇（含例句）...")
        vocab_with_examples = vocab_manager.get_vocab_by_id(test_vocab.vocab_id)
        
        if vocab_with_examples:
            print(f"[OK] 查询成功:")
            print(f"    词汇: {vocab_with_examples.vocab_body}")
            print(f"    例句数量: {len(vocab_with_examples.examples)}")
            if vocab_with_examples.examples:
                ex = vocab_with_examples.examples[0]
                print(f"    第一个例句:")
                print(f"      - text_id: {ex.text_id}")
                print(f"      - sentence_id: {ex.sentence_id}")
                print(f"      - context: {ex.context_explanation}")
                print(f"      - token_indices: {ex.token_indices}")
        
        # 清理测试数据
        print(f"\n[CLEAN] 清理测试数据...")
        vocab_manager.delete_vocab(test_vocab.vocab_id)
        session.commit()
        print("[OK] 清理完成")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] 例句功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_and_stats():
    """测试6: 搜索和统计功能"""
    print_header("测试6: 搜索和统计功能")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        vocab_manager = VocabManagerDB(session)
        
        # 获取统计
        print("[STATS] 获取词汇统计...")
        stats = vocab_manager.get_vocab_stats()
        print(f"[OK] 统计获取成功:")
        print(f"    总词汇: {stats.get('total', 0)}")
        print(f"    收藏词汇: {stats.get('starred', 0)}")
        print(f"    自动生成: {stats.get('auto', 0)}")
        print(f"    手动添加: {stats.get('manual', 0)}")
        
        # 搜索词汇
        if stats.get('total', 0) > 0:
            print(f"\n[SEARCH] 搜索词汇...")
            # 获取第一个词汇作为搜索关键词
            first_vocab = vocab_manager.get_all_vocabs(limit=1)
            if first_vocab:
                keyword = first_vocab[0].vocab_body[:3]  # 使用前3个字符
                print(f"    搜索关键词: '{keyword}'")
                results = vocab_manager.search_vocabs(keyword)
                print(f"[OK] 搜索成功: 找到 {len(results)} 个结果")
                if results:
                    print(f"    第一个结果: {results[0].vocab_body}")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] 搜索和统计测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Vocab 数据库适配完整流程测试")
    print("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("VocabManagerDB 基本操作", test_vocab_manager_basic),
        ("创建和查询", test_create_and_query),
        ("Adapter 转换", test_adapter_conversion),
        ("词汇例句", test_vocab_example),
        ("搜索和统计", test_search_and_stats),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 '{name}' 发生异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！Vocab数据库适配完整流程正常！")
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败，需要修复")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

