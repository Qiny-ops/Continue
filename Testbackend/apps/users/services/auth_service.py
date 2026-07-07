"""
认证服务
"""

import jwt
import logging
from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.conf import settings

from apps.users.models import User, TokenBlacklist
from apps.users.repositories import TokenRepository
from apps.core.exceptions import ValidationError, AuthenticationError

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    @staticmethod
    def generate_token(user):
        """生成JWT Token"""
        expire_time = datetime.now() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        jti = get_random_string(32)
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': expire_time,
            'jti': jti
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        return token, jti

    @staticmethod
    def verify_token(token):
        """验证JWT Token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
            jti = payload.get('jti')
            if jti and TokenBlacklist.objects.filter(jti=jti).exists():
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def authenticate_user(username, password):
        """验证用户凭据"""
        if not username or not password:
            raise ValidationError('用户名和密码不能为空')

        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationError('用户名或密码错误')

        if user.status != 'active':
            raise AuthenticationError('账号已被禁用')

        return user

    @staticmethod
    def update_login_info(user, ip_address):
        """更新用户登录信息"""
        user.last_login_time = timezone.now()
        user.last_login_ip = ip_address
        user.save(update_fields=['last_login_time', 'last_login_ip'])

    @staticmethod
    def login(username, password, request=None):
        """用户登录（完整流程）"""
        try:
            user = AuthService.authenticate_user(username, password)
        except (ValidationError, AuthenticationError) as e:
            return None, str(e)

        ip_address = request.META.get('REMOTE_ADDR', '') if request else ''
        AuthService.update_login_info(user, ip_address)

        token, jti = AuthService.generate_token(user)
        return {
            'user': user,
            'token': token
        }, None

    @staticmethod
    def logout(token, user):
        """用户登出"""
        payload = AuthService.verify_token(token)
        if payload:
            exp = payload.get('exp')
            if exp:
                expires_at = datetime.fromtimestamp(exp)
                TokenBlacklist.objects.create(
                    jti=payload.get('jti'),
                    token=token,
                    user=user,
                    expires_at=expires_at
                )
        return True

    @staticmethod
    def refresh_token(token):
        """刷新Token

        安全说明：刷新后将旧 token 加入黑名单，防止双 token 有效风险。
        """
        payload = AuthService.verify_token(token)
        if not payload:
            return None, 'Token无效或已过期'

        try:
            user = User.objects.get(id=payload.get('user_id'))
        except User.DoesNotExist:
            return None, '用户不存在'

        if user.status != 'active':
            return None, '用户已被禁用'

        # 将旧 token 加入黑名单
        old_jti = payload.get('jti')
        old_exp = payload.get('exp')
        if old_jti and old_exp:
            expires_at = datetime.fromtimestamp(old_exp)
            TokenBlacklist.objects.create(
                jti=old_jti,
                token=token,
                user=user,
                expires_at=expires_at
            )
            logger.info(f"Token 刷新：旧 token (jti={old_jti}) 已加入黑名单")

        # 生成新 token
        new_token, new_jti = AuthService.generate_token(user)
        return new_token, None
