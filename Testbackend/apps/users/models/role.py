"""
角色模型

系统角色用于控制全局功能访问权限。
简化为两个角色：admin（系统管理员）和 user（普通用户）。
"""

from django.db import models


class Role(models.Model):
    """
    系统角色模型
    """

    TYPE_CHOICES = [
        ('system', '系统角色'),
        ('default', '默认角色'),
    ]

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('disabled', '禁用'),
        ('deprecated', '已弃用'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='角色名称',
        help_text='如：系统管理员'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='角色代码',
        help_text='如：admin'
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='default',
        verbose_name='角色类型'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='角色描述',
        help_text='角色功能描述'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='角色状态'
    )

    permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='系统权限列表',
        help_text='系统权限代码列表，如 ["system_admin", "user_manage"]'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='角色创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='最后修改时间'
    )

    class Meta:
        verbose_name = '系统角色'
        verbose_name_plural = '系统角色'
        db_table = 'roles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_default_role(cls):
        """获取默认角色（普通用户角色）"""
        try:
            return cls.objects.get(code='user')
        except cls.DoesNotExist:
            max_id = cls.objects.aggregate(models.Max('id'))['id__max'] or 0
            new_id = max_id + 1
            return cls.objects.create(
                id=new_id,
                name='普通用户',
                code='user',
                type='default',
                description='普通用户角色，可创建和加入项目',
                status='active'
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
