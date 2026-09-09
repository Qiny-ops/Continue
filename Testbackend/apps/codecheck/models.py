# -*- coding: utf-8 -*-
"""
代码变更检查 模型

- CodeCheckTask: 一次代码检查任务（含风险评估、用例结果汇总、门禁状态）
- CodeCheckResult: 任务下每条用例的执行结果
"""
from django.db import models

from apps.users.models import User
from apps.projects.models import Project


class CodeCheckTask(models.Model):
    """代码检查任务"""

    STATUS_CHOICES = [
        ("pending", "等待执行"),
        ("running", "执行中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]
    TRIGGER_CHOICES = [
        ("manual", "手动"),
        ("webhook", "Webhook"),
    ]
    CASE_SOURCE_CHOICES = [
        ("inline", "内联"),
        ("file", "Excel"),
        ("platform", "平台"),
    ]
    CONCLUSION_CHOICES = [
        ("", "无"),
        ("passed", "通过"),
        ("blocked", "风险阻断"),
        ("failed", "未通过"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="code_check_tasks", verbose_name="所属项目",
    )
    project_name = models.CharField(max_length=255, verbose_name="项目名")
    repository_url = models.CharField(max_length=1024, verbose_name="仓库地址")
    branch = models.CharField(max_length=255, blank=True, verbose_name="分支")
    commit_sha = models.CharField(max_length=64, blank=True, verbose_name="Commit SHA")
    commit_author = models.CharField(max_length=128, blank=True, verbose_name="提交人")

    # 微服务侧 task_id（用于回写）
    service_task_id = models.CharField(
        max_length=64, unique=True, verbose_name="微服务任务ID"
    )

    trigger_source = models.CharField(
        max_length=16, choices=TRIGGER_CHOICES, default="manual", verbose_name="触发来源"
    )
    case_source = models.CharField(
        max_length=16, choices=CASE_SOURCE_CHOICES, default="platform", verbose_name="用例来源"
    )
    test_case_file = models.CharField(max_length=255, blank=True, verbose_name="Excel 文件名")

    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="状态"
    )
    progress = models.CharField(max_length=255, blank=True, verbose_name="当前进度")

    # 风险评估
    risk_level = models.CharField(max_length=16, blank=True, verbose_name="风险等级")
    risk_score = models.IntegerField(default=0, verbose_name="风险分数")
    risk_files = models.JSONField(default=list, blank=True, verbose_name="高风险文件")
    risk_reason = models.TextField(blank=True, verbose_name="风险理由")

    # diff
    diff_info = models.JSONField(default=dict, blank=True, verbose_name="代码变更")

    # 汇总
    summary = models.JSONField(default=dict, blank=True, verbose_name="汇总统计")

    # 结论
    conclusion = models.CharField(
        max_length=16, choices=CONCLUSION_CHOICES, default="", verbose_name="结论"
    )

    # 门禁（Commit Status）
    gate_provider = models.CharField(max_length=16, blank=True, verbose_name="门禁平台")
    gate_state = models.CharField(max_length=16, blank=True, verbose_name="门禁状态")
    gate_response = models.JSONField(default=dict, blank=True, verbose_name="门禁响应")

    error = models.TextField(blank=True, verbose_name="错误信息")

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="code_check_tasks", verbose_name="创建人",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "代码检查任务"
        verbose_name_plural = "代码检查任务"

    def __str__(self):
        return f"Check#{self.id} {self.project_name} [{self.status}/{self.conclusion}]"


class CodeCheckResult(models.Model):
    """任务下每条用例的结果"""

    RESULT_CHOICES = [
        ("通过", "通过"),
        ("失败", "失败"),
        ("异常", "异常"),
        ("解析失败", "解析失败"),
        ("未知", "未知"),
    ]

    task = models.ForeignKey(
        CodeCheckTask, on_delete=models.CASCADE,
        related_name="results", verbose_name="所属任务",
    )
    case_no = models.CharField(max_length=64, blank=True, verbose_name="用例编号")
    testpoint = models.CharField(max_length=512, blank=True, verbose_name="测试点")
    steps = models.TextField(blank=True, verbose_name="操作步骤")
    expectation = models.TextField(blank=True, verbose_name="预期结果")
    result = models.CharField(
        max_length=16, choices=RESULT_CHOICES, default="未知", verbose_name="结果"
    )
    reason = models.TextField(blank=True, verbose_name="校验理由")
    success = models.BooleanField(default=False, verbose_name="是否通过")
    # 结构化失败信息（审计报告直接引用）
    failure_type = models.CharField(
        max_length=32, blank=True, verbose_name="失败类型"
    )
    failure_reason = models.TextField(blank=True, verbose_name="失败原因")
    evidence = models.TextField(blank=True, verbose_name="证据位置")

    class Meta:
        verbose_name = "用例检查结果"
        verbose_name_plural = "用例检查结果"
        ordering = ["id"]

    def __str__(self):
        return f"{self.case_no}: {self.result}"
