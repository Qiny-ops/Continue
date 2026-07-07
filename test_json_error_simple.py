"""
简单的测试脚本 - 直接使用requests库测试JSON格式错误
"""
import requests
import json

# 测试地址
BASE_URL = "http://localhost:8000/api/users"


def test_login_and_json_errors():
    """测试登录和JSON格式错误"""
    
    print("="*60)
    print("测试步骤1: 创建测试用户（如果不存在）")
    print("="*60)
    
    # 尝试注册一个测试用户
    register_data = {
        "username": "json_test_user2",
        "email": "json_test2@example.com",
        "password": "TestPass123",  # 包含大写字母
        "name": "JSON Test User 2"
    }
    
    try:
        register_response = requests.post(
            f"{BASE_URL}/register/",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"注册响应状态码: {register_response.status_code}")
        print(f"注册响应数据: {register_response.json()}")
    except Exception as e:
        print(f"注册失败（用户可能已存在）: {e}")
    
    print("\n" + "="*60)
    print("测试步骤2: 登录获取token")
    print("="*60)
    
    login_data = {
        "username": "json_test_user2",
        "password": "TestPass123"  # 包含大写字母
    }
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应数据: {login_response.json()}")
        
        if login_response.status_code == 200:
            token = login_response.json()['data']['token']
            
            print("\n" + "="*60)
            print("测试步骤3: 测试登出接口 - JSON格式错误")
            print("="*60)
            
            # 测试缺少闭合括号
            invalid_json1 = '{"key": "value"'
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response1 = requests.post(
                f"{BASE_URL}/logout/",
                data=invalid_json1,
                headers=headers
            )
            print(f"\n测试1 - 缺少闭合括号:")
            print(f"  发送数据: {invalid_json1}")
            print(f"  状态码: {response1.status_code}")
            try:
                print(f"  响应数据: {response1.json()}")
            except:
                print(f"  响应文本: {response1.text}")
            
            # 测试缺少冒号
            invalid_json2 = '{"key" "value"}'
            response2 = requests.post(
                f"{BASE_URL}/logout/",
                data=invalid_json2,
                headers=headers
            )
            print(f"\n测试2 - 缺少冒号:")
            print(f"  发送数据: {invalid_json2}")
            print(f"  状态码: {response2.status_code}")
            try:
                print(f"  响应数据: {response2.json()}")
            except:
                print(f"  响应文本: {response2.text}")
            
            # 测试多余逗号
            invalid_json3 = '{"key": "value",}'
            response3 = requests.post(
                f"{BASE_URL}/logout/",
                data=invalid_json3,
                headers=headers
            )
            print(f"\n测试3 - 多余逗号:")
            print(f"  发送数据: {invalid_json3}")
            print(f"  状态码: {response3.status_code}")
            try:
                print(f"  响应数据: {response3.json()}")
            except:
                print(f"  响应文本: {response3.text}")
            
            print("\n" + "="*60)
            print("测试步骤4: 测试刷新Token接口 - JSON格式错误")
            print("="*60)
            
            # 重新登录获取新token
            login_response2 = requests.post(
                f"{BASE_URL}/login/",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            token2 = login_response2.json()['data']['token']
            
            headers2 = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token2}"
            }
            
            # 测试缺少闭合括号
            response4 = requests.post(
                f"{BASE_URL}/refresh-token/",
                data=invalid_json1,
                headers=headers2
            )
            print(f"\n测试4 - 缺少闭合括号:")
            print(f"  发送数据: {invalid_json1}")
            print(f"  状态码: {response4.status_code}")
            try:
                print(f"  响应数据: {response4.json()}")
            except:
                print(f"  响应文本: {response4.text}")
            
            # 测试多余逗号
            response5 = requests.post(
                f"{BASE_URL}/refresh-token/",
                data=invalid_json3,
                headers=headers2
            )
            print(f"\n测试5 - 多余逗号:")
            print(f"  发送数据: {invalid_json3}")
            print(f"  状态码: {response5.status_code}")
            try:
                print(f"  响应数据: {response5.json()}")
            except:
                print(f"  响应文本: {response5.text}")
            
    except Exception as e:
        print(f"登录失败: {e}")
        print("请确保后端服务正在运行（http://localhost:8000）")


if __name__ == '__main__':
    test_login_and_json_errors()