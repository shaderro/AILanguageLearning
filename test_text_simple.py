#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OriginalText 数据库适配简化测试

测试目标：
1. 数据库连接
2. OriginalTextManagerDB CRUD操作
3. Model <-> DTO 转换
4. 文章和句子的完整流程
"""
import sys
import os

# 添加backend路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from backend.data_managers import OriginalTextManagerDB
from backend.adapters import TextAdapter, SentenceAdapter
from database_system.business_logic.models import OriginalText as TextModel

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


def test_text_manager_basic():
    """测试2: OriginalTextManagerDB 基本操作"""
    print_header("测试2: OriginalTextManagerDB 基本操作")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        text_manager = OriginalTextManagerDB(session)
        
        print("[OK] OriginalTextManagerDB 初始化成功")
        
        # 获取所有文章
        texts = text_manager.get_all_texts()
        print(f"[OK] 获取文章列表: {len(texts)} 个")
        
        if texts:
            print(f"    第一个文章: {texts[0].text_title}")
            print(f"    返回类型: {type(texts[0]).__name__}")
            print(f"    是否为DTO: {hasattr(texts[0], 'text_by_sentence')}")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] OriginalTextManagerDB 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_and_query():
    """测试3: 创建和查询文章"""
    print_header("测试3: 创建和查询文章")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        text_manager = OriginalTextManagerDB(session)
        
        # 创建测试文章
        test_title = "test_integration_text"
        
        print(f"[+] 创建文章: {test_title}")
        new_text = text_manager.add_text(test_title)
        session.commit()
        
        print(f"[OK] 创建成功:")
        print(f"    ID: {new_text.text_id}")
        print(f"    标题: {new_text.text_title}")
        print(f"    句子数: {len(new_text.text_by_sentence)}")
        print(f"    类型: {type(new_text).__name__}")
        
        # 查询文章
        print(f"\n[QUERY] 查询文章 ID={new_text.text_id}")
        queried_text = text_manager.get_text_by_id(new_text.text_id)
        
        if queried_text:
            print(f"[OK] 查询成功:")
            print(f"    ID: {queried_text.text_id}")
            print(f"    标题: {queried_text.text_title}")
            print(f"    类型: {type(queried_text).__name__}")
        else:
            print(f"[ERROR] 查询失败: 未找到文章")
        
        # 清理测试数据（注意：需要在数据库层实现delete方法）
        # 暂时跳过删除，因为没有实现
        print(f"\n[INFO] 保留测试数据（text_id={new_text.text_id}）")
        
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
        from backend.data_managers.data_classes_new import OriginalText as TextDTO
        
        # 创建一个数据库Model
        print("[CREATE] 创建数据库Model...")
        text_model = TextModel(
            text_id=999,
            text_title="adapter_test"
        )
        print(f"[OK] Model创建成功: {text_model.text_title}")
        print(f"    类型: {type(text_model).__name__}")
        
        # 转换为DTO
        print("\n[CONVERT] Model -> DTO 转换...")
        text_dto = TextAdapter.model_to_dto(text_model, include_sentences=False)
        print(f"[OK] DTO转换成功:")
        print(f"    ID: {text_dto.text_id}")
        print(f"    标题: {text_dto.text_title}")
        print(f"    句子数: {len(text_dto.text_by_sentence)}")
        print(f"    类型: {type(text_dto).__name__}")
        
        # 转换回Model
        print("\n[CONVERT] DTO -> Model 转换...")
        text_model_2 = TextAdapter.dto_to_model(text_dto, text_id=text_dto.text_id)
        print(f"[OK] Model转换成功:")
        print(f"    ID: {text_model_2.text_id}")
        print(f"    标题: {text_model_2.text_title}")
        print(f"    类型: {type(text_model_2).__name__}")
        
        print("\n[OK] Adapter转换测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] Adapter转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentence_operations():
    """测试5: 句子操作"""
    print_header("测试5: 句子操作")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        text_manager = OriginalTextManagerDB(session)
        
        # 创建测试文章
        print("[+] 创建测试文章...")
        test_text = text_manager.add_text("sentence_test_text")
        session.commit()
        print(f"[OK] 文章创建成功: ID={test_text.text_id}")
        
        # 添加句子
        print(f"\n[+] 添加句子...")
        sentence1 = text_manager.add_sentence_to_text(
            text_id=test_text.text_id,
            sentence_text="Dies ist der erste Satz.",
            difficulty_level="easy"
        )
        session.commit()
        
        print(f"[OK] 句子1添加成功:")
        print(f"    text_id: {sentence1.text_id}")
        print(f"    sentence_id: {sentence1.sentence_id}")
        print(f"    body: {sentence1.sentence_body}")
        print(f"    difficulty: {sentence1.sentence_difficulty_level}")
        
        # 添加第二个句子
        sentence2 = text_manager.add_sentence_to_text(
            text_id=test_text.text_id,
            sentence_text="Dies ist der zweite Satz.",
            difficulty_level="hard"
        )
        session.commit()
        
        print(f"\n[OK] 句子2添加成功:")
        print(f"    sentence_id: {sentence2.sentence_id}")
        print(f"    body: {sentence2.sentence_body}")
        
        # 查询文章（含句子）
        print(f"\n[QUERY] 查询文章（含句子）...")
        text_with_sentences = text_manager.get_text_by_id(test_text.text_id, include_sentences=True)
        
        if text_with_sentences:
            print(f"[OK] 查询成功:")
            print(f"    文章: {text_with_sentences.text_title}")
            print(f"    句子数量: {len(text_with_sentences.text_by_sentence)}")
            for s in text_with_sentences.text_by_sentence:
                print(f"      句子{s.sentence_id}: {s.sentence_body[:30]}...")
        
        print(f"\n[INFO] 保留测试数据（text_id={test_text.text_id}）")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] 句子操作测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_and_stats():
    """测试6: 搜索和统计功能"""
    print_header("测试6: 搜索和统计功能")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        text_manager = OriginalTextManagerDB(session)
        
        # 获取统计
        print("[STATS] 获取文章统计...")
        stats = text_manager.get_text_stats()
        print(f"[OK] 统计获取成功:")
        print(f"    总文章: {stats.get('total_texts', 0)}")
        print(f"    总句子: {stats.get('total_sentences', 0)}")
        
        # 搜索文章
        if stats.get('total_texts', 0) > 0:
            print(f"\n[SEARCH] 搜索文章...")
            # 使用"test"作为搜索关键词
            keyword = "test"
            print(f"    搜索关键词: '{keyword}'")
            results = text_manager.search_texts(keyword)
            print(f"[OK] 搜索成功: 找到 {len(results)} 个结果")
            if results:
                print(f"    第一个结果: {results[0].text_title}")
        
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
    print("OriginalText 数据库适配完整流程测试")
    print("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("OriginalTextManagerDB 基本操作", test_text_manager_basic),
        ("创建和查询", test_create_and_query),
        ("Adapter 转换", test_adapter_conversion),
        ("句子操作", test_sentence_operations),
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
        print("\n[SUCCESS] 所有测试通过！OriginalText数据库适配完整流程正常！")
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败，需要修复")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

