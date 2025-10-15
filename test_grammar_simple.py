#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grammar 数据库适配简化测试

测试目标：
1. 数据库连接
2. GrammarRuleManagerDB CRUD操作
3. Model <-> DTO 转换
4. 完整的业务流程
"""
import sys
import os

# 添加backend路径
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, BACKEND_DIR)

from database_system.database_manager import DatabaseManager
from backend.data_managers import GrammarRuleManagerDB
from backend.adapters import GrammarAdapter
from database_system.business_logic.models import GrammarRule as GrammarModel

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


def test_grammar_manager_basic():
    """测试2: GrammarRuleManagerDB 基本操作"""
    print_header("测试2: GrammarRuleManagerDB 基本操作")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        grammar_manager = GrammarRuleManagerDB(session)
        
        print("[OK] GrammarRuleManagerDB 初始化成功")
        
        # 获取所有规则
        rules = grammar_manager.get_all_rules(limit=5)
        print(f"[OK] 获取规则列表: {len(rules)} 个")
        
        if rules:
            print(f"    第一个规则: {rules[0].name} - {rules[0].explanation[:30]}...")
            print(f"    返回类型: {type(rules[0]).__name__}")
            print(f"    是否为DTO: {hasattr(rules[0], 'examples')}")
        
        session.close()
        return True
    except Exception as e:
        print(f"[ERROR] GrammarRuleManagerDB 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_and_query():
    """测试3: 创建和查询规则"""
    print_header("测试3: 创建和查询规则")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        grammar_manager = GrammarRuleManagerDB(session)
        
        # 创建测试规则
        test_rule_name = "test_integration_rule"
        
        # 检查是否已存在
        existing = grammar_manager.get_rule_by_name(test_rule_name)
        if existing:
            print(f"[INFO] 测试规则已存在，删除旧数据...")
            grammar_manager.delete_rule(existing.rule_id)
            session.commit()
        
        # 创建新规则
        print(f"[+] 创建规则: {test_rule_name}")
        new_rule = grammar_manager.add_new_rule(
            name=test_rule_name,
            explanation="集成测试语法规则",
            source="manual",
            is_starred=True
        )
        session.commit()
        
        print(f"[OK] 创建成功:")
        print(f"    ID: {new_rule.rule_id}")
        print(f"    名称: {new_rule.name}")
        print(f"    解释: {new_rule.explanation}")
        print(f"    来源: {new_rule.source}")
        print(f"    收藏: {new_rule.is_starred}")
        print(f"    类型: {type(new_rule).__name__}")
        
        # 查询规则
        print(f"\n[QUERY] 查询规则 ID={new_rule.rule_id}")
        queried_rule = grammar_manager.get_rule_by_id(new_rule.rule_id)
        
        if queried_rule:
            print(f"[OK] 查询成功:")
            print(f"    ID: {queried_rule.rule_id}")
            print(f"    名称: {queried_rule.name}")
            print(f"    解释: {queried_rule.explanation}")
            print(f"    类型: {type(queried_rule).__name__}")
        else:
            print(f"[ERROR] 查询失败: 未找到规则")
        
        # 清理测试数据
        print(f"\n[CLEAN] 清理测试数据...")
        grammar_manager.delete_rule(new_rule.rule_id)
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
        from backend.data_managers.data_classes_new import GrammarRule as GrammarDTO
        from database_system.business_logic.models import SourceType
        
        # 创建一个数据库Model
        print("[CREATE] 创建数据库Model...")
        grammar_model = GrammarModel(
            rule_id=999,
            rule_name="adapter_test",
            rule_summary="适配器测试规则",
            source=SourceType.MANUAL,
            is_starred=False
        )
        print(f"[OK] Model创建成功: {grammar_model.rule_name}")
        print(f"    类型: {type(grammar_model).__name__}")
        print(f"    source类型: {type(grammar_model.source).__name__}")
        
        # 转换为DTO
        print("\n[CONVERT] Model -> DTO 转换...")
        grammar_dto = GrammarAdapter.model_to_dto(grammar_model, include_examples=False)
        print(f"[OK] DTO转换成功:")
        print(f"    ID: {grammar_dto.rule_id}")
        print(f"    名称: {grammar_dto.name}")
        print(f"    解释: {grammar_dto.explanation}")
        print(f"    来源: {grammar_dto.source} (类型: {type(grammar_dto.source).__name__})")
        print(f"    收藏: {grammar_dto.is_starred}")
        print(f"    类型: {type(grammar_dto).__name__}")
        
        # 转换回Model
        print("\n[CONVERT] DTO -> Model 转换...")
        grammar_model_2 = GrammarAdapter.dto_to_model(grammar_dto, rule_id=grammar_dto.rule_id)
        print(f"[OK] Model转换成功:")
        print(f"    ID: {grammar_model_2.rule_id}")
        print(f"    名称: {grammar_model_2.rule_name}")
        print(f"    解释: {grammar_model_2.rule_summary}")
        print(f"    来源: {grammar_model_2.source} (类型: {type(grammar_model_2.source).__name__})")
        print(f"    类型: {type(grammar_model_2).__name__}")
        
        print("\n[OK] Adapter转换测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] Adapter转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grammar_example():
    """测试5: 语法例句功能"""
    print_header("测试5: 语法例句功能")
    
    try:
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        grammar_manager = GrammarRuleManagerDB(session)
        
        # 创建测试规则
        print("[+] 创建测试规则...")
        test_rule = grammar_manager.add_new_rule(
            name="example_test_rule",
            explanation="例句测试规则",
            source="qa"
        )
        session.commit()
        print(f"[OK] 规则创建成功: ID={test_rule.rule_id}")
        
        # 添加例句
        print(f"\n[+] 添加例句...")
        example = grammar_manager.add_grammar_example(
            rule_id=test_rule.rule_id,
            text_id=1,
            sentence_id=1,
            explanation_context="这是一个测试例句"
        )
        session.commit()
        
        print(f"[OK] 例句添加成功:")
        print(f"    rule_id: {example.rule_id}")
        print(f"    text_id: {example.text_id}")
        print(f"    sentence_id: {example.sentence_id}")
        print(f"    context: {example.explanation_context}")
        print(f"    类型: {type(example).__name__}")
        
        # 查询规则（包含例句）
        print(f"\n[QUERY] 查询规则（含例句）...")
        rule_with_examples = grammar_manager.get_rule_by_id(test_rule.rule_id)
        
        if rule_with_examples:
            print(f"[OK] 查询成功:")
            print(f"    规则: {rule_with_examples.name}")
            print(f"    例句数量: {len(rule_with_examples.examples)}")
            if rule_with_examples.examples:
                ex = rule_with_examples.examples[0]
                print(f"    第一个例句:")
                print(f"      - text_id: {ex.text_id}")
                print(f"      - sentence_id: {ex.sentence_id}")
                print(f"      - context: {ex.explanation_context}")
        
        # 清理测试数据
        print(f"\n[CLEAN] 清理测试数据...")
        grammar_manager.delete_rule(test_rule.rule_id)
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
        grammar_manager = GrammarRuleManagerDB(session)
        
        # 获取统计
        print("[STATS] 获取语法规则统计...")
        stats = grammar_manager.get_grammar_stats()
        print(f"[OK] 统计获取成功:")
        print(f"    总规则: {stats.get('total', 0)}")
        print(f"    收藏规则: {stats.get('starred', 0)}")
        print(f"    自动生成: {stats.get('auto', 0)}")
        print(f"    手动添加: {stats.get('manual', 0)}")
        print(f"    QA生成: {stats.get('qa', 0)}")
        
        # 搜索规则
        if stats.get('total', 0) > 0:
            print(f"\n[SEARCH] 搜索规则...")
            # 获取第一个规则作为搜索关键词
            first_rule = grammar_manager.get_all_rules(limit=1)
            if first_rule:
                keyword = first_rule[0].name[:3]  # 使用前3个字符
                print(f"    搜索关键词: '{keyword}'")
                results = grammar_manager.search_rules(keyword)
                print(f"[OK] 搜索成功: 找到 {len(results)} 个结果")
                if results:
                    print(f"    第一个结果: {results[0].name}")
        
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
    print("Grammar 数据库适配完整流程测试")
    print("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("GrammarRuleManagerDB 基本操作", test_grammar_manager_basic),
        ("创建和查询", test_create_and_query),
        ("Adapter 转换", test_adapter_conversion),
        ("语法例句", test_grammar_example),
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
        print("\n[SUCCESS] 所有测试通过！Grammar数据库适配完整流程正常！")
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败，需要修复")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

