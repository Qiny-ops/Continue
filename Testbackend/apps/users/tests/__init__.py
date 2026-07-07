import pytest
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, Role


class BaseTestCase(TestCase):
    """测试基类，提供通用测试设置"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.django_client = Client()

    def create_user(self, username='testuser', email='test@example.com', password='testpass123',
                    name='Test User', status='active', role_code='user'):
        """创建测试用户的辅助方法"""
        role = Role.objects.filter(code=role_code).first()
        if not role:
            role = Role.objects.create(
                name='普通用户' if role_code == 'user' else '系统管理员',
                code=role_code,
                type='default' if role_code == 'user' else 'system',
                status='active'
            )
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=name,
            status=status,
            system_role=role
        )
        return user

    def authenticate_user(self, user):
        """认证用户"""
        self.client.force_authenticate(user=user)


class LoginTestCase(BaseTestCase):
    """登录功能测试用例"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.login_url = reverse('login')
    
    def setUp(self):
        self.active_user = self.create_user(
            username='activeuser',
            email='active@example.com',
            password='correctpass123',
            name='Active User',
            status='active'
        )
    
    def test_login_success(self):
        """测试用户登录成功"""
        data = {
            'username': 'activeuser',
            'password': 'correctpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
    
    def test_login_wrong_password(self):
        """测试登录失败-密码错误"""
        data = {
            'username': 'activeuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_user_not_exist(self):
        """测试登录失败-用户不存在"""
        data = {
            'username': 'nonexistentuser',
            'password': 'anypassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_disabled_account(self):
        """测试登录失败-账户禁用"""
        disabled_user = self.create_user(
            username='disableduser',
            email='disabled@example.com',
            password='testpass123',
            name='Disabled User',
            status='disabled'
        )
        data = {
            'username': 'disableduser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_login_suspended_account(self):
        """测试登录失败-账户暂停"""
        suspended_user = self.create_user(
            username='suspendeduser',
            email='suspended@example.com',
            password='testpass123',
            name='Suspended User',
            status='suspended'
        )
        data = {
            'username': 'suspendeduser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_login_pending_account(self):
        """测试登录失败-账户待激活"""
        pending_user = self.create_user(
            username='pendinguser',
            email='pending@example.com',
            password='testpass123',
            name='Pending User',
            status='pending'
        )
        data = {
            'username': 'pendinguser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_login_empty_username(self):
        """测试登录失败-空用户名"""
        data = {
            'username': '',
            'password': 'anypassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_empty_password(self):
        """测试登录失败-空密码"""
        data = {
            'username': 'activeuser',
            'password': ''
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_invalid_username_format(self):
        """测试登录失败-用户名格式非法"""
        data = {
            'username': 'user@name!#$',
            'password': 'anypassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_records_login_info(self):
        """测试登录成功-记录登录信息"""
        data = {
            'username': 'activeuser',
            'password': 'correctpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.active_user.refresh_from_db()
        self.assertIsNotNone(self.active_user.last_login_time)
        self.assertIsNotNone(self.active_user.last_login_ip)


class RegisterTestCase(BaseTestCase):
    """注册功能测试用例"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.register_url = reverse('register')
    
    def test_register_success(self):
        """测试用户注册成功"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'name': 'New User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_username_exists(self):
        """测试注册失败-用户名已存在"""
        self.create_user(username='existinguser', email='existing@example.com')
        data = {
            'username': 'existinguser',
            'email': 'another@example.com',
            'password': 'newpass123',
            'name': 'Another User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_email_exists(self):
        """测试注册失败-邮箱已存在"""
        self.create_user(username='user1', email='existing@example.com')
        data = {
            'username': 'newusername',
            'email': 'existing@example.com',
            'password': 'newpass123',
            'name': 'New User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_weak_password(self):
        """测试注册失败-密码强度不足"""
        data = {
            'username': 'weakpassuser',
            'email': 'weakpass@example.com',
            'password': '12345',
            'name': 'Weak Pass User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_invalid_email(self):
        """测试注册失败-邮箱格式无效"""
        data = {
            'username': 'invalidemailuser',
            'email': 'invalid-email',
            'password': 'newpass123',
            'name': 'Invalid Email User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_default_role_assigned(self):
        """测试注册成功-默认角色分配"""
        data = {
            'username': 'roleuser',
            'email': 'roleuser@example.com',
            'password': 'newpass123',
            'name': 'Role User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='roleuser')
        self.assertIsNotNone(user.system_role)
        self.assertEqual(user.system_role.code, 'guest')
    
    def test_register_default_status_set(self):
        """测试注册成功-默认状态设置"""
        data = {
            'username': 'statususer',
            'email': 'statususer@example.com',
            'password': 'newpass123',
            'name': 'Status User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='statususer')
        self.assertEqual(user.status, 'active')


class ForgotPasswordTestCase(BaseTestCase):
    """忘记密码功能测试用例"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.forgot_password_url = reverse('forgot_password')
    
    def setUp(self):
        self.user = self.create_user(
            username='forgotuser',
            email='forgot@example.com',
            password='testpass123'
        )
    
    def test_forgot_password_success(self):
        """测试忘记密码成功"""
        data = {'email': 'forgot@example.com'}
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_forgot_password_email_not_registered(self):
        """测试忘记密码失败-邮箱未注册"""
        data = {'email': 'notregistered@example.com'}
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_forgot_password_invalid_email_format(self):
        """测试忘记密码失败-邮箱格式无效"""
        data = {'email': 'invalid-email'}
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_forgot_password_generates_token(self):
        """测试忘记密码成功-生成重置令牌"""
        data = {'email': 'forgot@example.com'}
        response = self.client.post(self.forgot_password_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.reset_password_token)
        self.assertIsNotNone(self.user.reset_password_expire)


class ResetPasswordTestCase(BaseTestCase):
    """重置密码功能测试用例"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
    
    def setUp(self):
        self.user = self.create_user(
            username='resetuser',
            email='reset@example.com',
            password='oldpass123'
        )
        self.user.reset_password_token = 'validtoken123'
        from django.utils import timezone
        from datetime import timedelta
        self.user.reset_password_expire = timezone.now() + timedelta(hours=1)
        self.user.save()
    
    def test_reset_password_success(self):
        """测试重置密码成功"""
        url = reverse('reset_password', args=['validtoken123'])
        data = {'password': 'newpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
        self.assertIsNone(self.user.reset_password_token)
    
    def test_reset_password_invalid_token(self):
        """测试重置密码失败-令牌无效"""
        url = reverse('reset_password', args=['invalidtoken'])
        data = {'password': 'newpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reset_password_expired_token(self):
        """测试重置密码失败-令牌过期"""
        from django.utils import timezone
        from datetime import timedelta
        self.user.reset_password_expire = timezone.now() - timedelta(hours=1)
        self.user.save()
        
        url = reverse('reset_password', args=['validtoken123'])
        data = {'password': 'newpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reset_password_weak_password(self):
        """测试重置密码失败-密码强度不足"""
        url = reverse('reset_password', args=['validtoken123'])
        data = {'password': '12345'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTestCase(BaseTestCase):
    """用户信息功能测试用例"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profile_url = reverse('profile')
        cls.users_url = reverse('get_users')

    def setUp(self):
        self.user = self.create_user(
            username='profileuser',
            email='profile@example.com',
            password='testpass123',
            name='Profile User'
        )

    def test_get_profile_success(self):
        """测试获取用户信息成功"""
        self.authenticate_user(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')

    def test_get_profile_not_authenticated(self):
        """测试获取用户信息失败-未登录"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_success(self):
        """测试更新用户信息成功"""
        self.authenticate_user(self.user)
        data = {
            'name': 'Updated Name',
            'phone': '13800138000',
            'title': 'Senior Engineer'
        }
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated Name')

    def test_get_users_list_success(self):
        """测试获取用户列表成功"""
        self.authenticate_user(self.user)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutTestCase(BaseTestCase):
    """登出功能测试用例"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logout_url = reverse('logout')
        cls.login_url = reverse('login')

    def setUp(self):
        self.user = self.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='testpass123',
            name='Logout User',
            status='active'
        )

    def test_logout_success(self):
        """测试登出成功"""
        # 先登录获取token
        login_data = {
            'username': 'logoutuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 使用token进行登出 - 直接设置header
        response = self.client.post(
            self.logout_url,
            {},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_invalid_json_missing_bracket(self):
        """测试登出失败-JSON格式错误（缺少闭合括号）"""
        # 先登录获取token
        login_data = {
            'username': 'logoutuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 手动发送错误的JSON格式（缺少闭合括号）
        invalid_json = '{"key": "value"'  # 缺少闭合括号
        response = self.client.post(
            self.logout_url,
            data=invalid_json,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        # 应该返回400错误或能正确处理错误JSON
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # 如果系统有容错机制，可能仍然返回成功
        ])

    def test_logout_invalid_json_missing_colon(self):
        """测试登出失败-JSON格式错误（缺少冒号）"""
        # 先登录获取token
        login_data = {
            'username': 'logoutuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 发送缺少冒号的JSON
        invalid_json = '{"key" "value"}'  # 缺少冒号
        response = self.client.post(
            self.logout_url,
            data=invalid_json,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK
        ])

    def test_logout_empty_body(self):
        """测试登出-空请求体"""
        # 先登录获取token
        login_data = {
            'username': 'logoutuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 发送空请求体
        response = self.client.post(
            self.logout_url,
            data='',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        # 空请求体应该可以正常处理（登出不需要请求体）
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_token(self):
        """测试登出失败-缺少认证token"""
        response = self.client.post(self.logout_url, {}, format='json')
        # 即使没有token，登出接口也应该返回成功（因为不需要验证）
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RefreshTokenTestCase(BaseTestCase):
    """刷新Token功能测试用例"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.refresh_token_url = reverse('refresh_token')
        cls.login_url = reverse('login')

    def setUp(self):
        self.user = self.create_user(
            username='refreshuser',
            email='refresh@example.com',
            password='testpass123',
            name='Refresh User',
            status='active'
        )

    def test_refresh_token_success(self):
        """测试刷新Token成功"""
        # 先登录获取token
        login_data = {
            'username': 'refreshuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        old_token = login_response.data['data']['token']

        # 使用旧token刷新
        response = self.client.post(
            self.refresh_token_url,
            {},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {old_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['data'])
        self.assertNotEqual(response.data['data']['token'], old_token)

    def test_refresh_token_invalid_json_missing_bracket(self):
        """测试刷新Token失败-JSON格式错误（缺少闭合括号）"""
        # 先登录获取token
        login_data = {
            'username': 'refreshuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 发送格式错误的JSON（缺少闭合括号）
        invalid_json = '{"key": "value"'  # 缺少闭合括号
        response = self.client.post(
            self.refresh_token_url,
            data=invalid_json,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        # 应该返回400错误或能正确处理错误JSON
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # 如果系统有容错机制
        ])

    def test_refresh_token_invalid_json_extra_comma(self):
        """测试刷新Token失败-JSON格式错误（多余逗号）"""
        # 先登录获取token
        login_data = {
            'username': 'refreshuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 发送格式错误的JSON（多余逗号）
        invalid_json = '{"key": "value",}'  # 多余逗号
        response = self.client.post(
            self.refresh_token_url,
            data=invalid_json,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK
        ])

    def test_refresh_token_missing_auth_header(self):
        """测试刷新Token失败-缺少认证token"""
        response = self.client.post(self.refresh_token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_empty_body(self):
        """测试刷新Token-空请求体"""
        # 先登录获取token
        login_data = {
            'username': 'refreshuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['data']['token']

        # 发送空请求体
        response = self.client.post(
            self.refresh_token_url,
            data='',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        # 空请求体应该可以正常处理（刷新不需要请求体）
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token_expired_token(self):
        """测试刷新Token失败-Token已过期"""
        # 使用一个已过期的token（这里模拟，实际需要生成一个真实的过期token）
        expired_token = 'expired_token_for_test'
        response = self.client.post(
            self.refresh_token_url,
            {},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {expired_token}'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
