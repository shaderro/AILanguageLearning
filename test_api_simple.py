#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vocab API 简化测试
"""
import requests
import time

BASE_URL = "http://localhost:8001"
VOCAB_API = f"{BASE_URL}/api/v2/vocab"

def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_health():
    """测试健康检查"""
    print_header("测试1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 服务器状态: {data.get('status')}")
            print(f"    Services: {data.get('services')}")
            return True
        else:
            print(f"[ERROR] 状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] 无法连接到服务器，请确保服务器已启动")
        print("        运行: python server.py")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_get_all():
    """测试获取所有词汇"""
    print_header("测试2: 获取所有词汇")
    try:
        response = requests.get(f"{VOCAB_API}/", params={"limit": 5}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocabs = data.get("data", {}).get("vocabs", [])
                count = len(vocabs)
                print(f"[OK] 获取成功: {count} 个词汇")
                if vocabs:
                    v = vocabs[0]
                    print(f"    示例: {v.get('vocab_body')} - {v.get('explanation')[:30]}...")
                return True
        print(f"[ERROR] 请求失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_create():
    """测试创建词汇"""
    print_header("测试3: 创建词汇")
    try:
        vocab_data = {
            "vocab_body": "api_integration_test",
            "explanation": "API集成测试词汇",
            "source": "manual",
            "is_starred": True
        }
        print(f"[CREATE] 创建词汇: {vocab_data['vocab_body']}")
        response = requests.post(f"{VOCAB_API}/", json=vocab_data, timeout=5)
        
        if response.status_code == 201:
            data = response.json()
            if data.get("success"):
                vocab = data.get("data", {})
                vocab_id = vocab.get("vocab_id")
                print(f"[OK] 创建成功: ID={vocab_id}")
                print(f"    内容: {vocab.get('vocab_body')}")
                print(f"    来源: {vocab.get('source')}")
                return vocab_id
        print(f"[ERROR] 创建失败: {response.status_code}")
        print(f"    响应: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def test_get_one(vocab_id):
    """测试获取单个词汇"""
    print_header(f"测试4: 获取单个词汇 ID={vocab_id}")
    try:
        response = requests.get(f"{VOCAB_API}/{vocab_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vocab = data.get("data", {})
                print(f"[OK] 获取成功:")
                print(f"    ID: {vocab.get('vocab_id')}")
                print(f"    内容: {vocab.get('vocab_body')}")
                print(f"    收藏: {vocab.get('is_starred')}")
                return True
        print(f"[ERROR] 获取失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_search():
    """测试搜索"""
    print_header("测试5: 搜索词汇")
    try:
        response = requests.get(f"{VOCAB_API}/search/", params={"keyword": "test"}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                count = data.get("data", {}).get("count", 0)
                print(f"[OK] 搜索成功: 找到 {count} 个结果")
                return True
        print(f"[ERROR] 搜索失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_stats():
    """测试统计"""
    print_header("测试6: 获取统计")
    try:
        response = requests.get(f"{VOCAB_API}/stats/summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data.get("data", {})
                print(f"[OK] 统计获取成功:")
                print(f"    总词汇: {stats.get('total', 0)}")
                print(f"    收藏: {stats.get('starred', 0)}")
                return True
        print(f"[ERROR] 获取失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_delete(vocab_id):
    """测试删除"""
    print_header(f"测试7: 删除词汇 ID={vocab_id}")
    try:
        response = requests.delete(f"{VOCAB_API}/{vocab_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"[OK] 删除成功")
                return True
        print(f"[ERROR] 删除失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("Vocab API 集成测试")
    print("=" * 60)
    
    # 等待服务器启动
    print("\n[WAIT] 等待服务器启动...")
    time.sleep(3)
    
    # 测试健康检查
    if not test_health():
        print("\n[FAIL] 服务器未就绪")
        return False
    
    results = []
    test_vocab_id = None
    
    # 运行测试
    results.append(("健康检查", True))
    results.append(("获取所有词汇", test_get_all()))
    
    test_vocab_id = test_create()
    results.append(("创建词汇", test_vocab_id is not None))
    
    if test_vocab_id:
        results.append(("获取单个词汇", test_get_one(test_vocab_id)))
        results.append(("搜索词汇", test_search()))
        results.append(("获取统计", test_stats()))
        results.append(("删除词汇", test_delete(test_vocab_id)))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有API测试通过！")
        return True
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

