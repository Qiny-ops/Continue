"""
项目模型
"""

import uuid
from django.db import models
from apps.users.models import User


def generate_project_code():
    return f"proj_{uuid.uuid4().hex[:8].upper()}"


class Project(models.Model):
    """项目模型"""
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('completed', '已完成'),
        ('pending', '待开始'),
        ('archived', '已归档'),
    ]

    TYPE_CHOICES = [
        ('web', 'Web项目'),
        ('mobile', '移动应用'),
        ('api', 'API项目'),
        ('desktop', '桌面应用'),
        ('performance', '性能测试'),
        ('security', '安全测试'),
        ('other', '其他'),
    ]

    VISIBILITY_CHOICES = [
        ('public', '公开'),
        ('private', '私有'),
    ]

    name = models.CharField(max_length=255, verbose_name='项目名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='项目标识', help_text='项目的唯一标识符')
    identifier = models.CharField(max_length=50, blank=True, default='', verbose_name='项目标识符', help_text='项目URL标识')
    description = models.TextField(blank=True, verbose_name='项目描述')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='web', verbose_name='项目类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='项目状态')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public', verbose_name='可见性')
    icon = models.CharField(max_length=50, default='Folder', verbose_name='项目图标', help_text='Element Plus 图标名称')
    icon_color = models.CharField(max_length=20, default='#3b82f6', verbose_name='图标颜色')
    start_time = models.DateField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateField(null=True, blank=True, verbose_name='结束时间')

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_projects', verbose_name='项目负责人')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects', verbose_name='创建者')
    test_cases = models.IntegerField(default=0, verbose_name='测试用例数')
    test_plans = models.IntegerField(default=0, verbose_name='测试计划数')
    bugs = models.IntegerField(default=0, verbose_name='缺陷数')

    knowledge_base_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='知识库ID', help_text='关联的WeKnora知识库ID')
    knowledge_base_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='知识库名称', help_text='知识库显示名称')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['owner']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_project_code()
        if self.code:
            self.code = self.code.lower()
        if self.identifier and self.identifier != self.code:
            self.identifier = self.identifier.lower()
        super().save(*args, **kwargs)


class ProjectMember(models.Model):
    """项目成员模型"""
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('developer', '开发人员'),
        ('tester', '测试人员'),
        ('viewer', '观察者'),
    ]

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('disabled', '已禁用'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members', verbose_name='所属项目')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships', verbose_name='用户')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer', verbose_name='成员角色')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='成员状态')
    is_favorite = models.BooleanField(default=False, verbose_name='是否收藏')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目成员'
        verbose_name_plural = '项目成员'
        db_table = 'project_members'
        unique_together = ['project', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'role']),
            models.Index(fields=['user', 'is_favorite']),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.project.name} ({self.get_role_display()})"


class ProjectRole(models.Model):
    """项目角色权限配置模型"""
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('developer', '开发人员'),
        ('tester', '测试人员'),
        ('viewer', '观察者'),
        ('custom', '自定义角色'),
    ]

    PERMISSION_CHOICES = [
        ('project_manage', '项目管理'),
        ('member_manage', '成员管理'),
        ('testcase_manage', '测试用例管理'),
        ('testcase_view', '测试用例查看'),
        ('apitest_manage', '接口测试管理'),
        ('apitest_view', '接口测试查看'),
        ('apitest_execute', '接口测试执行'),
        ('knowledge_manage', '知识库管理'),
        ('knowledge_view', '知识库查看'),
        ('test_execute', '测试执行'),
        ('report_view', '报告查看'),
        ('settings_manage', '设置管理'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='role_permissions', verbose_name='所属项目')
    role_key = models.CharField(max_length=20, verbose_name='角色标识')
    name = models.CharField(max_length=50, blank=True, default='', verbose_name='角色名称')
    color = models.CharField(max_length=20, blank=True, default='', verbose_name='角色颜色')
    permissions = models.JSONField(default=list, verbose_name='权限列表', help_text='权限代码列表')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '项目角色权限'
        verbose_name_plural = '项目角色权限'
        db_table = 'project_roles'
        unique_together = ['project', 'role_key']
        ordering = ['role_key']

    def __str__(self):
        return f"{self.project.name} - {self.get_role_key_display()}"
