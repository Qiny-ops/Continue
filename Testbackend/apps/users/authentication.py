"""
自定义 JWT 认证模块

为 Django REST Framework 提供 JWT 认证支持
"""

import jwt
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from apps.users.models import TokenBlacklist

User = get_user_model()

# JWT 配置从 settings 读取
JWT_SECRET = settings.JWT_SECRET

# 内部服务 API Key（用于微服务之间调用）
INTERNAL_API_KEY = os.environ.get('INTERNAL_API_KEY', 'internal-service-key-dev')


class InternalServiceAuthentication(authentication.BaseAuthentication):
    """
    内部服务认证类

    用于微服务之间的 API 调用认证。
    通过 X-Internal-API-Key 请求头验证。
    """

    def authenticate(self, request):
        """
        认证方法

        Args:
            request: HTTP 请求对象

        Returns:
            tuple: (None, 'internal') 表示内部服务调用
        """
        # 从请求头获取内部服务 API Key
        api_key = request.META.get('HTTP_X_INTERNAL_API_KEY')

        if not api_key:
            return None

        # 验证 API Key
        if api_key != INTERNAL_API_KEY:
            raise exceptions.AuthenticationFailed('内部服务 API Key 无效')

        # 返回 None 作为 user，'internal' 作为认证标识
        # 表示这是一个内部服务调用，而非用户调用
        return (None, 'internal')

    def authenticate_header(self, request):
        """
        返回认证头信息
        """
        return 'X-Internal-API-Key'


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT 认证类
    
    从请求头中提取并验证 JWT token，返回对应的用户
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """
        认证方法
        
        Args:
            request: HTTP 请求对象
            
        Returns:
            tuple: (user, token) 或 None
        """
        # 从请求头获取认证信息
        auth_header = authentication.get_authorization_header(request).split()
        
        # 如果没有认证头，返回 None
        if not auth_header:
            return None
        
        # 检查认证头格式
        if len(auth_header) == 1:
            msg = '认证 token 格式错误'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = '认证 token 格式错误，不应包含空格'
            raise exceptions.AuthenticationFailed(msg)
        
        try:
            keyword = auth_header[0].decode()
            token = auth_header[1].decode()
        except UnicodeError:
            msg = '认证 token 包含非法字符'
            raise exceptions.AuthenticationFailed(msg)
        
        # 检查认证类型
        if keyword.lower() != self.keyword.lower():
            msg = '不支持的认证类型'
            raise exceptions.AuthenticationFailed(msg)
        
        # 验证 token
        return self.authenticate_credentials(token)
    
    def authenticate_credentials(self, token):
        """
        验证 token 并返回用户
        
        Args:
            token: JWT token 字符串
            
        Returns:
            tuple: (user, token)
        """
        try:
            # 解码 token
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            msg = '认证 token 已过期'
            raise exceptions.AuthenticationFailed(msg)
        except jwt.InvalidTokenError:
            msg = '认证 token 无效'
            raise exceptions.AuthenticationFailed(msg)
        
        # 检查 token 是否在黑名单中
        if TokenBlacklist.is_blacklisted(token):
            msg = '认证 token 已失效'
            raise exceptions.AuthenticationFailed(msg)
        
        # 获取用户 ID
        user_id = payload.get('user_id')
        if not user_id:
            msg = 'token 中不包含用户 ID'
            raise exceptions.AuthenticationFailed(msg)
        
        # 获取用户
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            msg = '用户不存在'
            raise exceptions.AuthenticationFailed(msg)
        
        # 检查用户状态
        if user.status != 'active':
            msg = '用户已被禁用'
            raise exceptions.AuthenticationFailed(msg)
        
        return (user, token)
    
    def authenticate_header(self, request):
        """
        返回认证头信息
        
        Args:
            request: HTTP 请求对象
            
        Returns:
            str: 认证头字符串
        """
        return f'{self.keyword} realm="api"'
