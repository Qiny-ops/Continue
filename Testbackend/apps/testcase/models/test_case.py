"""
测试用例模型定义

包含用例库、版本、模块、测试用例、评审、执行记录等模型。
"""

from django.db import models
from apps.projects.models import Project
from apps.users.models import User


class TestCaseRepository(models.Model):
    """
    用例库模型
    一个用例库对应一个被测应用（如Web应用、APP、API服务等）

    业务逻辑：用例库必须关联项目，通过项目权限控制访问
    """
    name = models.CharField(max_length=255, verbose_name='用例库名称')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='test_repositories',
        verbose_name='所属项目'
    )
    description = models.TextField(blank=True, verbose_name='描述')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_repositories',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用例库'
        verbose_name_plural = '用例库管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """确保每个项目只有一个默认用例库，且项目不为空"""
        if not self.project_id:
            raise ValueError('用例库必须关联项目')
        if self.is_default and self.project_id:
            TestCaseRepository.objects.filter(
                project_id=self.project_id, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class TestCaseVersion(models.Model):
    """
    版本模型
    版本属于用例库，通过用例库归属项目。
    需求和用例都通过版本关联，共享同一模块体系。
    """
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('archived', '已归档'),
    ]

    repository = models.ForeignKey(
        TestCaseRepository,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='所属用例库'
    )
    name = models.CharField(max_length=100, verbose_name='版本名称')
    description = models.TextField(blank=True, verbose_name='版本描述')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='版本状态'
    )
    is_default = models.BooleanField(default=False, verbose_name='是否默认版本')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_versions',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '版本'
        verbose_name_plural = '版本管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', 'status']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.repository.name} - {self.name}"


class TestModule(models.Model):
    """
    模块模型
    支持树形结构组织测试用例
    """
    version = models.ForeignKey(
        TestCaseVersion,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='所属版本'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父模块'
    )
    name = models.CharField(max_length=255, verbose_name='模块名称')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序序号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '模块'
        verbose_name_plural = '模块管理'
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['version', 'parent']),
        ]

    def __str__(self):
        return self.name


class TestCase(models.Model):
    """
    测试用例模型
    """
    PRIORITY_CHOICES = [
        ('p0', 'P0'),
        ('p1', 'P1'),
        ('p2', 'P2'),
        ('p3', 'P3'),
    ]

    AUTOMATION_STATUS_CHOICES = [
        ('not_analyzed', '未分析'),
        ('not_automated', '未自动化'),
        ('automated', '已自动化'),
    ]

    GENERATION_SOURCE_CHOICES = [
        ('manual', '手动创建'),
        ('ai_generated', 'AI生成'),
    ]

    REVIEW_STATUS_CHOICES = [
        ('pending', '待评审'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('revision_pending', '修改后待重审'),
    ]

    title = models.CharField(max_length=128, verbose_name='用例标题')
    module = models.ForeignKey(
        TestModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_cases',
        verbose_name='所在目录'
    )
    version = models.ForeignKey(
        TestCaseVersion,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='所属版本'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='p2',
        verbose_name='等级'
    )
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='评估工时'
    )
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    automation_status = models.CharField(
        max_length=20,
        choices=AUTOMATION_STATUS_CHOICES,
        default='not_analyzed',
        verbose_name='是否自动化'
    )
    automation_case_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='关联的自动化用例ID'
    )
    requirement = models.ForeignKey(
        'requirement.Requirement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_cases',
        verbose_name='关联需求'
    )
    precondition = models.TextField(blank=True, verbose_name='前置条件')
    steps = models.TextField(blank=True, verbose_name='测试步骤')
    expected_result = models.TextField(blank=True, verbose_name='预期结果')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_test_cases',
        verbose_name='创建者'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_test_cases',
        verbose_name='更新者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 来源
    generation_source = models.CharField(
        max_length=20,
        choices=GENERATION_SOURCE_CHOICES,
        default='manual',
        verbose_name='生成来源'
    )
    review_status = models.CharField(
        max_length=20,
        choices=REVIEW_STATUS_CHOICES,
        default='pending',
        verbose_name='审核状态'
    )

    class Meta:
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['version', 'priority']),
            models.Index(fields=['version', 'automation_status']),
            models.Index(fields=['module']),
            models.Index(fields=['title']),
            models.Index(fields=['created_by']),
            models.Index(fields=['priority']),
            models.Index(fields=['generation_source']),
            models.Index(fields=['review_status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """保证用例所属版本与所在模块版本一致，防止产生跨版本的"幽灵用例"。

        当用例归属某个模块时，强制将其 version 同步为模块的 version：
        - 仅设置 module 而未设置 version 时，自动从模块派生 version；
        - module 与 version 不一致时，以 module 的版本为准（模块树统计/按版本查询依赖这一约束）。
        """
        if self.module_id:
            try:
                module = TestModule.objects.get(id=self.module_id)
                if module.version_id and (
                    not self.version_id or self.version_id != module.version_id
                ):
                    self.version = module.version
            except TestModule.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class TestCaseReview(models.Model):
    """
    用例评审模型

    支持多轮评审流程：
    1. 评审人创建评审记录（pending）
    2. 评审通过（approved）或驳回（rejected）
    3. 驳回后，用例创建者可修改用例并重新提交评审（revision_pending）
    4. 评审人再次评审，形成闭环
    """
    STATUS_CHOICES = [
        ('pending', '待评审'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='所属用例'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_case_reviews',
        verbose_name='评审人'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='评审状态'
    )
    comment = models.TextField(blank=True, verbose_name='评审意见')
    # 评审轮次相关字段
    revision_number = models.PositiveIntegerField(
        default=1,
        verbose_name='评审轮次',
        help_text='表示这是第几轮评审，首次评审为1'
    )
    revision_note = models.TextField(
        blank=True,
        verbose_name='修改说明',
        help_text='重新提交评审时填写的修改说明'
    )
    previous_review = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_reviews',
        verbose_name='上一轮评审',
        help_text='关联到上一轮被驳回的评审记录'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用例评审'
        verbose_name_plural = '用例评审管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['test_case', 'status']),
            models.Index(fields=['reviewer']),
        ]

    def __str__(self):
        return f"{self.test_case.title} - {self.get_status_display()}"


class TestCaseExecution(models.Model):
    """
    用例执行记录模型
    """
    RESULT_CHOICES = [
        ('pass', '通过'),
        ('fail', '失败'),
        ('block', '阻塞'),
        ('skip', '跳过'),
    ]

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='所属用例'
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='test_case_executions',
        verbose_name='执行人'
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        verbose_name='执行结果'
    )
    actual_result = models.TextField(blank=True, verbose_name='实际结果')
    remark = models.TextField(blank=True, verbose_name='备注')
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name='执行时间')

    class Meta:
        verbose_name = '用例执行记录'
        verbose_name_plural = '用例执行记录管理'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['test_case', 'result']),
            models.Index(fields=['executed_by']),
            models.Index(fields=['executed_at']),
        ]

    def __str__(self):
        return f"{self.test_case.title} - {self.get_result_display()}"


class AIGenerationRecord(models.Model):
    """
    AI生成记录模型

    存储AI生成测试用例的元数据，与TestCase解耦。
    """
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    # 关联
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_generation_records',
        verbose_name='关联用例'
    )
    version = models.ForeignKey(
        TestCaseVersion,
        on_delete=models.CASCADE,
        related_name='ai_generation_records',
        verbose_name='所属版本'
    )
    module = models.ForeignKey(
        TestModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_generation_records',
        verbose_name='所属模块'
    )

    # 生成参数
    knowledge_base_ids = models.JSONField(
        default=list, verbose_name='知识库ID列表'
    )
    knowledge_ids = models.JSONField(
        default=list, verbose_name='知识文档ID列表'
    )
    module_name = models.CharField(
        max_length=255, blank=True, verbose_name='模块名称'
    )
    func_point = models.CharField(
        max_length=500, blank=True, verbose_name='功能点'
    )
    test_type = models.CharField(
        max_length=50, blank=True, verbose_name='测试类型'
    )

    # AI 元数据
    ai_request_id = models.CharField(
        max_length=100, blank=True, verbose_name='AI请求ID'
    )
    ai_model_version = models.CharField(
        max_length=50, blank=True, verbose_name='AI模型版本'
    )
    ai_confidence = models.FloatField(
        null=True, blank=True, verbose_name='AI置信度'
    )
    ai_raw_result = models.JSONField(
        default=dict, blank=True, verbose_name='AI原始返回'
    )
    ai_prompt_tokens = models.IntegerField(
        null=True, blank=True, verbose_name='Prompt Token数'
    )
    ai_completion_tokens = models.IntegerField(
        null=True, blank=True, verbose_name='Completion Token数'
    )

    # 结果
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )
    cases_created_count = models.IntegerField(
        default=0, verbose_name='创建用例数'
    )
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # 审计
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_generation_records',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'AI生成记录'
        verbose_name_plural = 'AI生成记录管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['version', 'status']),
            models.Index(fields=['test_case']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"AI生成 - {self.func_point or self.module_name} ({self.get_status_display()})"
