# -*- coding: utf-8 -*-
"""Web 自动化执行记录模型"""

from django.db import models

from apps.users.models import User
from apps.testcase.models import TestCase


class WebAutomationRun(models.Model):
    """Web 自动化用例执行记录"""

    RESULT_CHOICES = [
        ('running', '运行中'),
        ('pass', '通过'),
        ('fail', '失败'),
        ('error', '错误'),
    ]

    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='web_runs',
        verbose_name='关联功能用例',
    )
    case_title = models.CharField(max_length=255, blank=True, verbose_name='用例标题')
    start_url = models.CharField(max_length=2048, blank=True, verbose_name='起始 URL')
    environment_id = models.IntegerField(
        null=True, blank=True, verbose_name='环境ID',
        help_text='关联「环境管理」中的环境（ApiEnvironment.id），记录执行所用环境'
    )
    result = models.CharField(
        max_length=16, choices=RESULT_CHOICES, default='running', verbose_name='执行结果'
    )
    step_results = models.JSONField(default=list, blank=True, verbose_name='步骤结果')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    duration_ms = models.IntegerField(default=0, verbose_name='耗时(ms)')
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='web_runs',
        verbose_name='执行人',
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Web自动化执行记录'
        verbose_name_plural = 'Web自动化执行记录'

    def __str__(self):
        return f"WebRun#{self.id} {self.case_title or ''} [{self.result}]"
