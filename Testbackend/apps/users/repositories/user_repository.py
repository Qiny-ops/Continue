"""
用户数据访问层
"""

from django.db import models
from apps.users.models import User, TokenBlacklist


class UserRepository:
    """用户数据访问层"""

    @staticmethod
    def get_by_id(user_id):
        """根据ID获取用户"""
        return User.objects.filter(id=user_id).select_related('system_role').first()

    @staticmethod
    def get_by_username(username):
        """根据用户名获取用户"""
        return User.objects.filter(username=username).first()

    @staticmethod
    def get_by_email(email):
        """根据邮箱获取用户"""
        return User.objects.filter(email=email).first()

    @staticmethod
    def get_active_users():
        """获取所有活跃用户"""
        return User.objects.filter(status='active')

    @staticmethod
    def search(keyword=None, status=None, role=None):
        """搜索用户"""
        queryset = User.objects.all().select_related('system_role')

        if keyword:
            queryset = queryset.filter(
                models.Q(username__icontains=keyword) |
                models.Q(name__icontains=keyword) |
                models.Q(email__icontains=keyword)
            )

        if status:
            queryset = queryset.filter(status=status)

        if role:
            queryset = queryset.filter(system_role__code=role)

        return queryset

    @staticmethod
    def create_user(username, email, password, **extra_fields):
        """创建用户"""
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )

    @staticmethod
    def update_user(user, **kwargs):
        """更新用户信息"""
        for attr, value in kwargs.items():
            setattr(user, attr, value)
        user.save()
        return user

    @staticmethod
    def exists_by_username(username):
        """检查用户名是否存在"""
        return User.objects.filter(username=username).exists()

    @staticmethod
    def exists_by_email(email, exclude_id=None):
        """检查邮箱是否存在"""
        queryset = User.objects.filter(email=email)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()


class TokenRepository:
    """Token数据访问层"""

    @staticmethod
    def add_to_blacklist(jti, token, user, expires_at):
        """将Token加入黑名单"""
        return TokenBlacklist.objects.create(
            jti=jti,
            token=token,
            user=user,
            expires_at=expires_at
        )

    @staticmethod
    def is_blacklisted(jti):
        """检查JTI是否在黑名单中"""
        return TokenBlacklist.objects.filter(jti=jti).exists()

    @staticmethod
    def is_token_blacklisted(token):
        """检查Token是否在黑名单中"""
        return TokenBlacklist.is_blacklisted(token)

    @staticmethod
    def cleanup_expired():
        """清理过期的黑名单记录"""
        from django.utils import timezone
        return TokenBlacklist.objects.filter(expires_at__lt=timezone.now()).delete()
