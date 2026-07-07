"""
用户模型
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class TokenBlacklist(models.Model):
    """
    JWT Token 黑名单模型
    用于存储已失效的 token，实现登出后 token 立即失效
    """

    jti = models.CharField(max_length=64, unique=True, verbose_name='Token ID', help_text='JWT唯一标识符')
    token = models.CharField(max_length=500, blank=True, verbose_name='Token')
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        verbose_name='用户'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='加入黑名单时间')
    expires_at = models.DateTimeField(verbose_name='Token过期时间')

    class Meta:
        verbose_name = 'Token黑名单'
        verbose_name_plural = 'Token黑名单'
        db_table = 'token_blacklist'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['jti']),
            models.Index(fields=['user']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Blacklisted token for {self.user.username}"

    @classmethod
    def is_blacklisted(cls, token_or_jti):
        """检查 token 或 jti 是否在黑名单中"""
        import jwt
        from django.conf import settings
        try:
            if len(token_or_jti) > 100:
                payload = jwt.decode(token_or_jti, settings.JWT_SECRET, algorithms=['HS256'], options={"verify_exp": False})
                jti = payload.get('jti')
                if jti:
                    return cls.objects.filter(jti=jti).exists()
            else:
                return cls.objects.filter(jti=token_or_jti).exists()
        except (jwt.InvalidTokenError, Exception):
            pass

        return cls.objects.filter(token=token_or_jti).exists()

    @classmethod
    def add_to_blacklist(cls, token, user, expires_at, jti=None):
        """将 token 加入黑名单"""
        import jwt
        from django.conf import settings

        if not jti:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'], options={"verify_exp": False})
                jti = payload.get('jti')
            except (jwt.InvalidTokenError, Exception):
                jti = None

        if not jti:
            raise ValueError("无法获取 Token JTI")

        return cls.objects.create(
            jti=jti,
            token=token,
            user=user,
            expires_at=expires_at
        )

    @classmethod
    def cleanup_expired(cls):
        """清理过期的黑名单记录"""
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()


class User(AbstractUser):
    """
    用户模型 - 基于Django的AbstractUser扩展

    注意：username 和 email 都有数据库级别的唯一约束，确保并发注册时的数据一致性。
    """

    name = models.CharField(max_length=100, blank=True, default='', verbose_name='用户真实姓名', help_text='显示用姓名')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号码', help_text='可选联系方式')
    avatar = models.CharField(max_length=255, blank=True, null=True, verbose_name='头像URL', help_text='用户头像图片地址')
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name='职位/头衔', help_text='如：高级前端工程师')
    # 覆盖 email 字段，添加唯一约束以防止并发注册时的竞态条件
    email = models.EmailField(unique=True, verbose_name='邮箱地址', help_text='用户邮箱，用于登录和通知')
    system_role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='系统角色',
        help_text='关联roles.id，决定用户在平台全局的权限'
    )

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('disabled', '禁用'),
        ('suspended', '暂停'),
        ('pending', '待激活'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='用户状态',
        help_text='用户账户的当前状态'
    )

    last_login_time = models.DateTimeField(blank=True, null=True, verbose_name='最后登录时间', help_text='记录用户最后登录时间')
    last_login_ip = models.CharField(max_length=45, blank=True, null=True, verbose_name='最后登录IP', help_text='记录用户最后登录IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', help_text='用户注册时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间', help_text='最后修改时间')
    remark = models.TextField(blank=True, null=True, verbose_name='备注信息', help_text='用户备注说明')
    reset_password_token = models.CharField(max_length=64, blank=True, null=True, verbose_name='重置密码令牌')
    reset_password_expire = models.DateTimeField(blank=True, null=True, verbose_name='重置密码令牌过期时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['system_role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.name})"

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    @property
    def is_admin(self):
        """检查用户是否是系统管理员"""
        return self.system_role.code == 'admin' if self.system_role else False

    def save(self, *args, **kwargs):
        old_role_id = None
        if self.pk:
            try:
                old_user = User.objects.get(pk=self.pk)
                old_role_id = old_user.system_role_id
            except User.DoesNotExist:
                pass

        if not self.system_role_id:
            from .role import Role
            default_role = Role.get_default_role()
            self.system_role = default_role

        super().save(*args, **kwargs)
