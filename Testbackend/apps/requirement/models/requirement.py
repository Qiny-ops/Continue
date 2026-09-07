"""
需求模型定义

管理项目需求，支持手动创建和AI提取。
需求关联用例库版本和测试模块，与测试用例共享模块体系。
"""
from django.db import models
from apps.projects.models import Project
from apps.users.models import User


class Requirement(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '活跃'),
        ('completed', '已完成'),
        ('archived', '已归档'),
    ]

    PRIORITY_CHOICES = [
        ('p0', 'P0'),
        ('p1', 'P1'),
        ('p2', 'P2'),
        ('p3', 'P3'),
    ]

    SOURCE_CHOICES = [
        ('manual', '手动创建'),
        ('ai_extracted', 'AI提取'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name='所属项目'
    )
    version = models.ForeignKey(
        'testcase.TestCaseVersion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='requirements',
        verbose_name='所属版本'
    )
    title = models.CharField(max_length=255, verbose_name='需求标题')
    description = models.TextField(blank=True, verbose_name='需求描述')
    func_point = models.CharField(max_length=500, blank=True, verbose_name='功能点')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='p2',
        verbose_name='优先级'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='manual',
        verbose_name='来源'
    )
    knowledge_base_id = models.CharField(
        max_length=100, blank=True, verbose_name='来源知识库ID'
    )
    knowledge_id = models.CharField(
        max_length=100, blank=True, verbose_name='来源文档ID'
    )
    session_id = models.CharField(
        max_length=100, blank=True, verbose_name='AI提取会话ID'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_requirements',
        verbose_name='创建者'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_requirements',
        verbose_name='更新者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '需求'
        verbose_name_plural = '需求管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_readonly(self):
        """版本归档时需求只读"""
        if self.version_id and self.version.status == 'archived':
            return True
        return False
