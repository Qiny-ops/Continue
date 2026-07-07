# -*- coding: utf-8 -*-
"""
接口测试序列化器
"""

from rest_framework import serializers
from apps.apitest.models import ApiEnvironment, ApiTestCase, ApiTestRun
from apps.projects.models import Project


class ApiEnvironmentSerializer(serializers.ModelSerializer):
    """API 测试环境序列化器"""

    project = serializers.SlugRelatedField(
        slug_field='code',
        queryset=Project.objects.all(),
        help_text='项目 code'
    )

    class Meta:
        model = ApiEnvironment
        fields = [
            'id', 'project', 'name', 'env_type', 'base_url', 'description',
            'auth_type', 'auth_token', 'auth_header', 'auth_username', 'auth_password',
            'default_headers', 'global_vars', 'is_default', 'is_active',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ApiEnvironmentListSerializer(serializers.ModelSerializer):
    """环境列表序列化器（精简版）"""

    class Meta:
        model = ApiEnvironment
        fields = ['id', 'name', 'env_type', 'base_url', 'is_default', 'is_active']


class ApiTestCaseSerializer(serializers.ModelSerializer):
    """接口测试用例序列化器"""

    class Meta:
        model = ApiTestCase
        fields = [
            'id', 'project', 'name', 'precondition', 'testpoint', 'expectation',
            'priority', 'tags', 'test_data', 'run_list', 'status',
            'knowledge_base_id', 'source',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'updated_by', 'created_at', 'updated_at']


class ApiTestCaseListSerializer(serializers.ModelSerializer):
    """用例列表序列化器"""

    last_run_result = serializers.SerializerMethodField()
    last_run_time = serializers.SerializerMethodField()

    class Meta:
        model = ApiTestCase
        fields = ['id', 'name', 'precondition', 'testpoint', 'expectation', 'status', 'last_run_result', 'last_run_time', 'created_at']

    def get_last_run_result(self, obj):
        """获取最近一次执行结果"""
        last_run = obj.runs.order_by('-start_time').first()
        return last_run.result if last_run else None

    def get_last_run_time(self, obj):
        """获取最近一次执行时间"""
        last_run = obj.runs.order_by('-start_time').first()
        return last_run.start_time if last_run else None


class ApiTestRunSerializer(serializers.ModelSerializer):
    """执行记录序列化器"""

    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)

    class Meta:
        model = ApiTestRun
        fields = [
            'id', 'test_case', 'test_case_name', 'environment', 'environment_name',
            'result', 'start_time', 'end_time', 'duration_ms',
            'step_results', 'variables_snapshot', 'error_message', 'error_step',
            'ai_validation', 'executed_by'
        ]
        read_only_fields = [
            'id', 'test_case_name', 'environment_name',
            'start_time', 'executed_by'
        ]


class ApiTestRunListSerializer(serializers.ModelSerializer):
    """执行记录列表序列化器"""

    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)

    class Meta:
        model = ApiTestRun
        fields = [
            'id', 'test_case_name', 'environment_name',
            'result', 'start_time', 'end_time', 'duration_ms'
        ]


# ==================== 执行请求参数 ====================

class ExecuteTestCaseParamsSerializer(serializers.Serializer):
    """执行测试用例参数"""

    environment_id = serializers.IntegerField(help_text='执行环境 ID')


class GenerateTestCaseParamsSerializer(serializers.Serializer):
    """AI 生成测试用例参数"""

    knowledge_base_id = serializers.CharField(help_text='知识库 ID')
    query = serializers.CharField(
        default='对文档中的接口设计接口测试用例',
        help_text='查询问题'
    )
