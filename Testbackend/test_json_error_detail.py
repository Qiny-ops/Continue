"""
测试JSON格式错误的详细响应
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Testbackend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
django.setup()

from rest_framework.test import APIClient
from django.urls import reverse
from apps.users.models import User, Role


def test_json_format_errors():
    """测试JSON格式错误的实际响应"""
    client = APIClient()
    
    # 创建测试用户
    role = Role.objects.filter(code='user').first()
    if not role:
        role = Role.objects.create(
            name='普通用户',
            code='user',
            type='default',
            status='active'
        )
    
    # 清理之前的测试用户
    User.objects.filter(username='json_test_user').delete()
    
    user = User.objects.create_user(
        username='json_test_user',
        email='json_test@example.com',
        password='testpass123',
        name='JSON Test User',
        status='active',
        system_role=role
    )
    
    # 1. 先登录获取token
    login_url = reverse('login')
    login_response = client.post(login_url, {
        'username': 'json_test_user',
        'password': 'testpass123'
    }, format='json')
    
    print(f"\n登录响应状态码: {login_response.status_code}")
    print(f"登录响应数据: {login_response.data}")
    
    if login_response.status_code == 200:
        token = login_response.data['data']['token']
        
        # 2. 测试登出接口的JSON格式错误
        logout_url = reverse('logout')
        
        print("\n" + "="*60)
        print("测试登出接口 - JSON格式错误")
        print("="*60)
        
        # 测试1: 缺少闭合括号
        invalid_json1 = '{"key": "value"'
        response1 = client.post(
            logout_url,
            data=invalid_json1,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        print(f"\n测试1 - 缺少闭合括号:")
        print(f"  发送数据: {invalid_json1}")
        print(f"  状态码: {response1.status_code}")
        print(f"  响应数据: {response1.data}")
        
        # 测试2: 缺少冒号
        invalid_json2 = '{"key" "value"}'
        response2 = client.post(
            logout_url,
            data=invalid_json2,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        print(f"\n测试2 - 缺少冒号:")
        print(f"  发送数据: {invalid_json2}")
        print(f"  状态码: {response2.status_code}")
        print(f"  响应数据: {response2.data}")
        
        # 测试3: 多余逗号
        invalid_json3 = '{"key": "value",}'
        response3 = client.post(
            logout_url,
            data=invalid_json3,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        print(f"\n测试3 - 多余逗号:")
        print(f"  发送数据: {invalid_json3}")
        print(f"  状态码: {response3.status_code}")
        print(f"  响应数据: {response3.data}")
        
        # 3. 测试刷新Token接口的JSON格式错误
        refresh_url = reverse('refresh_token')
        
        print("\n" + "="*60)
        print("测试刷新Token接口 - JSON格式错误")
        print("="*60)
        
        # 重新登录获取新token
        login_response2 = client.post(login_url, {
            'username': 'json_test_user',
            'password': 'testpass123'
        }, format='json')
        token2 = login_response2.data['data']['token']
        
        # 测试4: 缺少闭合括号
        response4 = client.post(
            refresh_url,
            data=invalid_json1,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token2}'
        )
        print(f"\n测试4 - 缺少闭合括号:")
        print(f"  发送数据: {invalid_json1}")
        print(f"  状态码: {response4.status_code}")
        print(f"  响应数据: {response4.data}")
        
        # 测试5: 多余逗号
        response5 = client.post(
            refresh_url,
            data=invalid_json3,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token2}'
        )
        print(f"\n测试5 - 多余逗号:")
        print(f"  发送数据: {invalid_json3}")
        print(f"  状态码: {response5.status_code}")
        print(f"  响应数据: {response5.data}")
    
    # 清理测试用户
    User.objects.filter(username='json_test_user').delete()
    print("\n" + "="*60)
    print("测试用户已清理")
    print("="*60)


if __name__ == '__main__':
    test_json_format_errors()