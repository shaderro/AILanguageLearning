"""
测试词汇 API 脚本

运行前确保：
1. 数据库中有词汇数据（运行 migrate_vocab_only.py）
2. 服务器已启动（python server.py）
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v2/vocab"


def test_health():
    """测试服务器健康状态"""
    print("\n" + "="*50)
    print("测试1: 服务器健康检查")
    print("="*50)
    
    response = requests.get("http://localhost:8000/api/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200


def test_get_all_vocabs():
    """测试获取所有词汇"""
    print("\n" + "="*50)
    print("测试2: 获取所有词汇")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/", params={"limit": 5})
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"成功: {data.get('success')}")
    print(f"词汇数量: {data.get('data', {}).get('count')}")
    
    if data.get('data', {}).get('vocabs'):
        print(f"\n前5个词汇:")
        for vocab in data['data']['vocabs'][:5]:
            print(f"  - [{vocab['vocab_id']}] {vocab['vocab_body']}: {vocab['explanation'][:30]}...")
    
    return response.status_code == 200


def test_get_single_vocab():
    """测试获取单个词汇"""
    print("\n" + "="*50)
    print("测试3: 获取单个词汇 (ID=1)")
    print("="*50)
    
    vocab_id = 1
    response = requests.get(f"{BASE_URL}/{vocab_id}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        vocab = data.get('data', {})
        print(f"词汇ID: {vocab.get('vocab_id')}")
        print(f"词汇内容: {vocab.get('vocab_body')}")
        print(f"解释: {vocab.get('explanation')}")
        print(f"来源: {vocab.get('source')}")
        print(f"收藏: {vocab.get('is_starred')}")
        print(f"例句数量: {len(vocab.get('examples', []))}")
    else:
        print(f"错误: {response.json()}")
    
    return response.status_code == 200


def test_create_vocab():
    """测试创建新词汇"""
    print("\n" + "="*50)
    print("测试4: 创建新词汇")
    print("="*50)
    
    new_vocab = {
        "vocab_body": "test_api_word",
        "explanation": "通过API创建的测试词汇",
        "source": "manual",
        "is_starred": False
    }
    
    print(f"创建词汇: {new_vocab['vocab_body']}")
    response = requests.post(f"{BASE_URL}/", json=new_vocab)
    print(f"状态码: {response.status_code}")
    
    data = response.json()
    print(f"成功: {data.get('success')}")
    
    if response.status_code == 201:
        vocab = data.get('data', {})
        print(f"新词汇ID: {vocab.get('vocab_id')}")
        print(f"词汇内容: {vocab.get('vocab_body')}")
        return vocab.get('vocab_id')
    else:
        print(f"消息: {data.get('detail', data.get('error'))}")
        return None


def test_search_vocabs():
    """测试搜索词汇"""
    print("\n" + "="*50)
    print("测试5: 搜索词汇")
    print("="*50)
    
    keyword = "test"
    print(f"搜索关键词: {keyword}")
    
    response = requests.get(f"{BASE_URL}/search/", params={"keyword": keyword})
    print(f"状态码: {response.status_code}")
    
    data = response.json()
    print(f"找到 {data.get('data', {}).get('count')} 个结果")
    
    if data.get('data', {}).get('vocabs'):
        for vocab in data['data']['vocabs'][:3]:
            print(f"  - {vocab['vocab_body']}: {vocab['explanation'][:40]}...")
    
    return response.status_code == 200


def test_toggle_star(vocab_id):
    """测试切换收藏状态"""
    print("\n" + "="*50)
    print(f"测试6: 切换收藏状态 (ID={vocab_id})")
    print("="*50)
    
    response = requests.post(f"{BASE_URL}/{vocab_id}/star")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data.get('message')}")
        print(f"新收藏状态: {data.get('data', {}).get('is_starred')}")
    
    return response.status_code == 200


def test_update_vocab(vocab_id):
    """测试更新词汇"""
    print("\n" + "="*50)
    print(f"测试7: 更新词汇 (ID={vocab_id})")
    print("="*50)
    
    update_data = {
        "explanation": "更新后的解释（通过API）",
        "is_starred": True
    }
    
    response = requests.put(f"{BASE_URL}/{vocab_id}", json=update_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data.get('message')}")
        vocab = data.get('data', {})
        print(f"新解释: {vocab.get('explanation')}")
        print(f"收藏状态: {vocab.get('is_starred')}")
    
    return response.status_code == 200


def test_get_stats():
    """测试获取统计信息"""
    print("\n" + "="*50)
    print("测试8: 获取词汇统计")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/stats/summary")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json().get('data', {})
        print(f"总词汇数: {stats.get('total')}")
        print(f"收藏词汇: {stats.get('starred')}")
        print(f"自动生成: {stats.get('auto')}")
        print(f"手动添加: {stats.get('manual')}")
    
    return response.status_code == 200


def test_delete_vocab(vocab_id):
    """测试删除词汇"""
    print("\n" + "="*50)
    print(f"测试9: 删除词汇 (ID={vocab_id})")
    print("="*50)
    
    confirm = input(f"确认删除词汇 ID {vocab_id}? (y/n): ")
    if confirm.lower() != 'y':
        print("取消删除")
        return False
    
    response = requests.delete(f"{BASE_URL}/{vocab_id}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data.get('message')}")
    
    return response.status_code == 200


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("           词汇 API 测试脚本")
    print("="*60)
    
    try:
        # 测试1: 健康检查
        if not test_health():
            print("\n❌ 服务器未启动或无法访问")
            print("请先运行: python server.py")
            return
        
        # 测试2: 获取所有词汇
        if not test_get_all_vocabs():
            print("\n⚠️ 获取词汇列表失败，可能数据库为空")
            print("请先运行: python migrate_vocab_only.py")
        
        # 测试3: 获取单个词汇
        test_get_single_vocab()
        
        # 测试4: 创建新词汇
        new_vocab_id = test_create_vocab()
        
        # 测试5: 搜索词汇
        test_search_vocabs()
        
        # 如果成功创建了词汇，继续测试
        if new_vocab_id:
            # 测试6: 切换收藏
            test_toggle_star(new_vocab_id)
            
            # 测试7: 更新词汇
            test_update_vocab(new_vocab_id)
            
            # 测试8: 获取统计
            test_get_stats()
            
            # 测试9: 删除词汇
            test_delete_vocab(new_vocab_id)
        
        print("\n" + "="*60)
        print("✅ 测试完成！")
        print("="*60)
        print("\n访问 http://localhost:8000/docs 查看完整 API 文档")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器")
        print("请确保服务器已启动: python server.py")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")


if __name__ == "__main__":
    main()

