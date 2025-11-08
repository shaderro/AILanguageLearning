#!/usr/bin/env python3
"""
测试认证 API 的脚本
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_register():
    """测试注册"""
    print("\n" + "="*60)
    print("测试 1: 用户注册")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "password": "test123456"
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ 注册成功!")
        print(f"   用户ID: {result['user_id']}")
        print(f"   Token: {result['access_token'][:50]}...")
        return result['user_id'], result['access_token']
    else:
        print(f"\n❌ 注册失败")
        return None, None

def test_login(user_id):
    """测试登录"""
    print("\n" + "="*60)
    print("测试 2: 用户登录")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "user_id": user_id,
        "password": "test123456"
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 登录成功!")
        print(f"   用户ID: {result['user_id']}")
        print(f"   Token: {result['access_token'][:50]}...")
        return result['access_token']
    else:
        print(f"\n❌ 登录失败")
        return None

def test_login_wrong_password(user_id):
    """测试错误密码登录"""
    print("\n" + "="*60)
    print("测试 3: 错误密码登录（应该失败）")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "user_id": user_id,
        "password": "wrongpassword"
    }
    
    response = requests.post(url, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 401:
        print(f"\n✅ 正确拒绝了错误密码")
    else:
        print(f"\n❌ 应该返回 401 状态码")

def test_get_current_user(token):
    """测试获取当前用户信息"""
    print("\n" + "="*60)
    print("测试 4: 获取当前用户信息（需要 token）")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"Debug - 使用的 token: {token[:50]}...")
    print(f"Debug - Authorization header: Bearer {token[:50]}...")
    
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print(f"\n✅ 成功获取用户信息")
    else:
        print(f"\n❌ 获取失败")
        print(f"Debug - 完整 token: {token}")

def test_protected_route_without_token():
    """测试没有 token 访问受保护路由"""
    print("\n" + "="*60)
    print("测试 5: 不带 token 访问受保护路由（应该失败）")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/me"
    
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 403:
        print(f"\n✅ 正确拒绝了未授权访问")
    else:
        print(f"\n⚠️ 状态码为 {response.status_code}（预期 403）")

def test_protected_route_with_invalid_token():
    """测试无效 token 访问受保护路由"""
    print("\n" + "="*60)
    print("测试 6: 使用无效 token 访问受保护路由（应该失败）")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/me"
    headers = {
        "Authorization": "Bearer invalid_token_here"
    }
    
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 401:
        print(f"\n✅ 正确拒绝了无效 token")
    else:
        print(f"\n❌ 应该返回 401 状态码")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试认证 API")
    print("="*60)
    print(f"服务器地址: {BASE_URL}")
    
    # 测试注册
    user_id, token = test_register()
    if not user_id or not token:
        print("\n❌ 注册失败，无法继续测试")
        return
    
    # 测试登录
    login_token = test_login(user_id)
    if not login_token:
        print("\n❌ 登录失败，无法继续测试")
        return
    
    # 测试错误密码
    test_login_wrong_password(user_id)
    
    # 测试获取当前用户
    test_get_current_user(login_token)
    
    # 测试未授权访问
    test_protected_route_without_token()
    
    # 测试无效token
    test_protected_route_with_invalid_token()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print(f"\n💾 保存以下信息用于后续测试:")
    print(f"   用户ID: {user_id}")
    print(f"   Token: {login_token}")
    print(f"\n使用方式:")
    print(f'   curl -H "Authorization: Bearer {login_token}" {BASE_URL}/api/auth/me')

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到服务器: {BASE_URL}")
        print("请确保后端服务器正在运行:")
        print("  python frontend/my-web-ui/backend/main.py")
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

