# -*- coding: utf-8 -*-
"""
接口测试 Admin 管理
"""

from django.contrib import admin
from apps.apitest.models import ApiEnvironment, ApiTestCase, ApiTestRun


@admin.register(ApiEnvironment)
class ApiEnvironmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'env_type', 'base_url', 'is_default', 'is_active']
    list_filter = ['env_type', 'is_default', 'is_active']
    search_fields = ['name', 'base_url']
    raw_id_fields = ['project', 'created_by']


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'priority', 'status', 'source', 'created_at']
    list_filter = ['priority', 'status', 'source']
    search_fields = ['name', 'description']
    raw_id_fields = ['project', 'created_by', 'updated_by']


@admin.register(ApiTestRun)
class ApiTestRunAdmin(admin.ModelAdmin):
    list_display = ['test_case', 'environment', 'result', 'duration_ms', 'start_time']
    list_filter = ['result']
    raw_id_fields = ['test_case', 'environment', 'executed_by']
    readonly_fields = ['start_time', 'end_time', 'step_results', 'variables_snapshot']