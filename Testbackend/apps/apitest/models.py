# -*- coding: utf-8 -*-
"""
接口测试自动化数据模型

包含：
- ApiEnvironment: 测试环境配置（Base URL、认证、全局变量）
- ApiTestCase: 接口测试用例
- ApiTestRun: 执行记录
"""

from django.db import models
from django.conf import settings


class ApiEnvironment(models.Model):
    """
    API 测试环境配置

    存储被测系统的 Base URL、认证配置、全局变量等
    一个项目可以有多个环境（开发、测试、预发布、生产）
    """
    ENV_TYPE_CHOICES = [
        ('dev', '开发环境'),
        ('test', '测试环境'),
        ('staging', '预发布'),
        ('prod', '生产环境'),
    ]

    AUTH_TYPE_CHOICES = [
        ('none', '无认证'),
        ('token', 'Token'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('jwt', 'JWT'),
        ('api_key', 'API Key'),
    ]

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='api_environments',
        verbose_name='所属项目'
    )
    name = models.CharField(max_length=100, verbose_name='环境名称')
    env_type = models.CharField(
        max_length=20,
        choices=ENV_TYPE_CHOICES,
        default='test',
        verbose_name='环境类型'
    )

    # 核心配置：Base URL
    base_url = models.CharField(
        max_length=500,
        verbose_name='基础URL',
        help_text='如: http://api.example.com'
    )
    description = models.TextField(blank=True, verbose_name='环境描述')

    # 认证配置
    auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='none',
        verbose_name='认证类型'
    )
    auth_token = models.TextField(
        blank=True,
        verbose_name='认证Token',
        help_text='认证令牌，支持变量引用 {{token}}'
    )
    auth_header = models.CharField(
        max_length=100,
        default='Authorization',
        verbose_name='认证请求头',
        help_text='如: Authorization、X-API-Key'
    )
    auth_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Basic Auth 用户名'
    )
    auth_password = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Basic Auth 密码'
    )

    # 全局请求头
    default_headers = models.JSONField(
        default=dict,
        verbose_name='默认请求头',
        help_text='{"Content-Type": "application/json"}'
    )

    # 全局变量（可在用例中通过 {{var}} 引用）
    global_vars = models.JSONField(
        default=dict,
        verbose_name='全局变量',
        help_text='如: {"api_key": "xxx", "default_user": "admin"}'
    )

    is_default = models.BooleanField(default=False, verbose_name='默认环境')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_environments',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'apitest_environment'
        verbose_name = 'API测试环境'
        verbose_name_plural = 'API测试环境管理'
        ordering = ['-is_default', 'env_type']
        unique_together = ['project', 'name']
        indexes = [
            models.Index(fields=['project', 'env_type']),
            models.Index(fields=['project', 'is_default']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ApiTestCase(models.Model):
    """
    接口测试用例

    匹配微服务生成的测试用例格式：
    - name: 对应 apiname（接口名称）
    - precondition: 前置条件
    - testpoint: 测试点
    - expectation: 预期结果
    - test_data: 真实测试数据（可选，供 AI 参考）
    - run_list: AI 分析的执行顺序（缓存）
    """
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('ready', '就绪'),
        ('passed', '已通过'),
        ('failed', '已失败'),
    ]

    PRIORITY_CHOICES = [
        ('p0', 'P0'),
        ('p1', 'P1'),
        ('p2', 'P2'),
        ('p3', 'P3'),
    ]

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='api_test_cases',
        verbose_name='所属项目'
    )

    # 基本信息（匹配微服务生成格式）
    name = models.CharField(
        max_length=200,
        verbose_name='用例名称',
        help_text='对应微服务的 apiname'
    )
    precondition = models.TextField(
        blank=True,
        verbose_name='前置条件',
        help_text='如: 用户已登录、数据已准备'
    )
    testpoint = models.TextField(
        default='',
        blank=True,
        verbose_name='测试点',
        help_text='具体测试内容描述'
    )
    expectation = models.TextField(
        default='',
        blank=True,
        verbose_name='预期结果',
        help_text='如: HTTP状态码200，返回code为0'
    )

    # 优先级和标签
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='p2',
        verbose_name='优先级'
    )
    tags = models.JSONField(default=list, verbose_name='标签')

    # 测试数据（真实数据，供 AI 填充参数时参考）
    test_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='测试数据',
        help_text='如: {"username": "admin", "password": "123456"}'
    )

    # AI 生成的依赖信息（执行顺序，可缓存）
    run_list = models.JSONField(
        default=list,
        blank=True,
        verbose_name='执行列表',
        help_text='AI 分析的接口执行顺序，包含依赖接口'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 关联知识库
    knowledge_base_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='知识库ID'
    )

    # 来源
    source = models.CharField(
        max_length=20,
        choices=[('manual', '手动创建'), ('ai_generated', 'AI生成')],
        default='manual',
        verbose_name='来源'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_api_test_cases',
        verbose_name='创建者'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_api_test_cases',
        verbose_name='更新者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'apitest_case'
        verbose_name = '接口测试用例'
        verbose_name_plural = '接口测试用例管理'
        ordering = ['id']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name


class ApiTestRun(models.Model):
    """
    接口测试执行记录

    存储每次执行的详细结果
    """
    RESULT_CHOICES = [
        ('pass', '通过'),
        ('fail', '失败'),
        ('error', '错误'),
        ('running', '执行中'),
        ('cancelled', '已取消'),
    ]

    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='runs',
        verbose_name='所属用例'
    )
    environment = models.ForeignKey(
        ApiEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_runs',
        verbose_name='执行环境'
    )

    # 执行状态
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='running',
        verbose_name='执行结果'
    )
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束时间'
    )
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='耗时(ms)'
    )

    # 执行详情（每个步骤的结果）
    step_results = models.JSONField(
        default=list,
        verbose_name='步骤执行结果',
        help_text='每个接口的请求响应详情'
    )

    # 变量快照（执行时的变量值）
    variables_snapshot = models.JSONField(
        default=dict,
        verbose_name='变量快照'
    )

    # 错误信息
    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )
    error_step = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='出错步骤'
    )

    # AI 校验结果
    ai_validation = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='AI校验结果',
        help_text='{"passed": true, "reason": "..."}'
    )

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='api_test_runs',
        verbose_name='执行者'
    )

    class Meta:
        db_table = 'apitest_run'
        verbose_name = '接口测试执行记录'
        verbose_name_plural = '接口测试执行记录管理'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['test_case', 'result']),
            models.Index(fields=['environment']),
            models.Index(fields=['start_time']),
            models.Index(fields=['executed_by']),
        ]

    def __str__(self):
        return f"{self.test_case.name} - {self.get_result_display()} ({self.start_time})"
