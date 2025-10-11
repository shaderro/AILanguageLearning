#!/usr/bin/env python3
"""
Vocab API 集成测试

测试目标：
1. FastAPI 服务器启动
2. 所有API端点的功能
3. 端到端的数据流
"""
import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8001"
VOCAB_API_URL = f"{BASE_URL}/api/v2/vocab"


def print_section(title):
    """打印测试章节标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_health_check():
    """测试1: 健康检查"""
    print_section("测试1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务器健康状态: {data.get('status')}")
            print(f"   Services: {data.get('services')}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("   请先启动服务器: python server.py")
        return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False


def test_get_all_vocabs():
    """测试2: 获取所有词汇"""
    print_section("测试2: 获取所有词汇")
    
    try:
        response = requests.get(f"{VOCAB_API_URL}/", params={"limit": 5}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocabs = data.get("data", {}).get("vocabs", [])
                count = data.get("data", {}).get("count", 0)
                print(f"✅ 获取词汇成功: {count} 个")
                
                if vocabs:
                    print(f"\n前{min(3, len(vocabs))}个词汇:")
                    for vocab in vocabs[:3]:
                        print(f"  - {vocab.get('vocab_body')}: {vocab.get('explanation')}")
                        print(f"    (ID: {vocab.get('vocab_id')}, source: {vocab.get('source')}, starred: {vocab.get('is_starred')})")
                
                return True
            else:
                print(f"❌ API返回失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_create_vocab():
    """测试3: 创建词汇"""
    print_section("测试3: 创建词汇")
    
    try:
        # 创建测试词汇
        test_vocab = {
            "vocab_body": "api_test_vocab",
            "explanation": "API集成测试词汇",
            "source": "manual",
            "is_starred": True
        }
        
        print(f"➕ 创建词汇: {test_vocab['vocab_body']}")
        response = requests.post(f"{VOCAB_API_URL}/", json=test_vocab, timeout=5)
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                vocab_data = data.get("data", {})
                vocab_id = vocab_data.get("vocab_id")
                print(f"✅ 创建成功:")
                print(f"   ID: {vocab_id}")
                print(f"   内容: {vocab_data.get('vocab_body')}")
                print(f"   解释: {vocab_data.get('explanation')}")
                print(f"   来源: {vocab_data.get('source')}")
                print(f"   收藏: {vocab_data.get('is_starred')}")
                return vocab_id
            else:
                print(f"❌ 创建失败: {data.get('error')}")
                return None
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return None


def test_get_vocab(vocab_id):
    """测试4: 获取单个词汇"""
    print_section(f"测试4: 获取单个词汇 (ID={vocab_id})")
    
    try:
        response = requests.get(f"{VOCAB_API_URL}/{vocab_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocab = data.get("data", {})
                print(f"✅ 获取成功:")
                print(f"   ID: {vocab.get('vocab_id')}")
                print(f"   内容: {vocab.get('vocab_body')}")
                print(f"   解释: {vocab.get('explanation')}")
                print(f"   来源: {vocab.get('source')}")
                print(f"   收藏: {vocab.get('is_starred')}")
                print(f"   例句数: {len(vocab.get('examples', []))}")
                return True
            else:
                print(f"❌ 获取失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_update_vocab(vocab_id):
    """测试5: 更新词汇"""
    print_section(f"测试5: 更新词汇 (ID={vocab_id})")
    
    try:
        update_data = {
            "explanation": "更新后的解释",
            "is_starred": False
        }
        
        print(f"📝 更新词汇...")
        response = requests.put(f"{VOCAB_API_URL}/{vocab_id}", json=update_data, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocab = data.get("data", {})
                print(f"✅ 更新成功:")
                print(f"   新解释: {vocab.get('explanation')}")
                print(f"   新收藏状态: {vocab.get('is_starred')}")
                return True
            else:
                print(f"❌ 更新失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_toggle_star(vocab_id):
    """测试6: 切换收藏状态"""
    print_section(f"测试6: 切换收藏状态 (ID={vocab_id})")
    
    try:
        response = requests.post(f"{VOCAB_API_URL}/{vocab_id}/star", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                is_starred = data.get("data", {}).get("is_starred")
                print(f"✅ 收藏状态切换成功: {is_starred}")
                return True
            else:
                print(f"❌ 切换失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_add_example(vocab_id):
    """测试7: 添加例句"""
    print_section(f"测试7: 添加例句 (vocab_id={vocab_id})")
    
    try:
        example_data = {
            "vocab_id": vocab_id,
            "text_id": 1,
            "sentence_id": 1,
            "context_explanation": "这是一个API测试例句",
            "token_indices": [1, 2, 3]
        }
        
        print(f"➕ 添加例句...")
        response = requests.post(f"{VOCAB_API_URL}/examples", json=example_data, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                example = data.get("data", {})
                print(f"✅ 例句添加成功:")
                print(f"   text_id: {example.get('text_id')}")
                print(f"   sentence_id: {example.get('sentence_id')}")
                print(f"   context: {example.get('context_explanation')}")
                print(f"   token_indices: {example.get('token_indices')}")
                return True
            else:
                print(f"❌ 添加失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_search_vocab():
    """测试8: 搜索词汇"""
    print_section("测试8: 搜索词汇")
    
    try:
        keyword = "test"
        print(f"🔍 搜索关键词: '{keyword}'")
        
        response = requests.get(f"{VOCAB_API_URL}/search/", params={"keyword": keyword}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocabs = data.get("data", {}).get("vocabs", [])
                count = data.get("data", {}).get("count", 0)
                print(f"✅ 搜索成功: 找到 {count} 个结果")
                
                if vocabs:
                    print(f"\n前{min(3, len(vocabs))}个结果:")
                    for vocab in vocabs[:3]:
                        print(f"  - {vocab.get('vocab_body')}: {vocab.get('explanation')}")
                
                return True
            else:
                print(f"❌ 搜索失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_get_stats():
    """测试9: 获取统计"""
    print_section("测试9: 获取词汇统计")
    
    try:
        response = requests.get(f"{VOCAB_API_URL}/stats/summary", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data.get("data", {})
                print(f"✅ 统计获取成功:")
                print(f"   总词汇: {stats.get('total', 0)}")
                print(f"   收藏词汇: {stats.get('starred', 0)}")
                print(f"   自动生成: {stats.get('auto', 0)}")
                print(f"   手动添加: {stats.get('manual', 0)}")
                return True
            else:
                print(f"❌ 获取失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def test_delete_vocab(vocab_id):
    """测试10: 删除词汇"""
    print_section(f"测试10: 删除词汇 (ID={vocab_id})")
    
    try:
        print(f"🗑️  删除词汇...")
        response = requests.delete(f"{VOCAB_API_URL}/{vocab_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ 删除成功")
                return True
            else:
                print(f"❌ 删除失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Vocab API 集成测试")
    print("="*60)
    
    # 测试健康检查
    if not test_health_check():
        print("\n❌ 服务器未启动，无法继续测试")
        print("   请运行: python server.py")
        return False
    
    results = []
    test_vocab_id = None
    
    # 测试1: 获取所有词汇
    results.append(("获取所有词汇", test_get_all_vocabs()))
    
    # 测试2: 创建词汇
    test_vocab_id = test_create_vocab()
    results.append(("创建词汇", test_vocab_id is not None))
    
    if test_vocab_id:
        # 测试3: 获取单个词汇
        results.append(("获取单个词汇", test_get_vocab(test_vocab_id)))
        
        # 测试4: 更新词汇
        results.append(("更新词汇", test_update_vocab(test_vocab_id)))
        
        # 测试5: 切换收藏
        results.append(("切换收藏", test_toggle_star(test_vocab_id)))
        
        # 测试6: 添加例句
        results.append(("添加例句", test_add_example(test_vocab_id)))
        
        # 测试7: 搜索词汇
        results.append(("搜索词汇", test_search_vocab()))
        
        # 测试8: 获取统计
        results.append(("获取统计", test_get_stats()))
        
        # 测试9: 删除词汇
        results.append(("删除词汇", test_delete_vocab(test_vocab_id)))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n>>> 所有测试通过！Vocab API集成测试成功！")
        return True
    else:
        print(f"\n>>> {total - passed} 个测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

