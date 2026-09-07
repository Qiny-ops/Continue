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
from apps.core.exceptions import ValidationError, AuthenticationError, BusinessError, NotFoundError

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
        """更新用户登录信息（非关键副作用，失败不应阻断登录）

        使用 queryset.update() 而非 model.save(update_fields=...)：跨进程架构下
        (api-testing-service 经 HTTP 调用 Django 登录接口) 无法把注册/登录/清理纳入同一事务，
        测试账号在 authenticate 成功到本调用之间可能被删除（用例自带删除步骤、或并发
        cleanup 交错）。model.save() 在行已缺失时会抛 Django 5.1+ 的 NotUpdated 使登录 500；
        queryset.update() 影响 0 行时静默返回 0，从根上消除该异常路径，同时保留告警可见性。
        """
        affected = User.objects.filter(pk=user.pk).update(
            last_login_time=timezone.now(),
            last_login_ip=ip_address,
        )
        if affected == 0:
            # 账号可能已在登录前被清理/删除，登录信息更新为非关键操作，不应让登录 500
            logger.warning(
                'update_login_info 未影响任何行（账号可能已被删除/并发清理），已忽略。user=%s',
                getattr(user, 'username', None) or user.pk,
            )

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
            raise BusinessError('Token无效或已过期')

        try:
            user = User.objects.get(id=payload.get('user_id'))
        except User.DoesNotExist:
            raise NotFoundError('用户不存在')

        if user.status != 'active':
            raise BusinessError('用户已被禁用')

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
