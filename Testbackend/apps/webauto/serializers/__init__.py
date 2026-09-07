# -*- coding: utf-8 -*-
"""Web 自动化序列化器"""

from rest_framework import serializers

from apps.webauto.models import WebAutomationRun


class WebAutomationRunSerializer(serializers.ModelSerializer):
    """执行记录详情"""

    executed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WebAutomationRun
        fields = [
            'id', 'test_case', 'case_title', 'start_url', 'result',
            'step_results', 'error_message', 'duration_ms',
            'executed_by', 'executed_by_name', 'started_at', 'end_time',
        ]
        read_only_fields = fields

    def get_executed_by_name(self, obj):
        if obj.executed_by:
            return obj.executed_by.username
        return None


class WebAutomationRunListSerializer(serializers.ModelSerializer):
    """执行记录列表"""

    executed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WebAutomationRun
        fields = [
            'id', 'case_title', 'start_url', 'result',
            'error_message', 'duration_ms',
            'executed_by_name', 'started_at', 'end_time',
        ]
        read_only_fields = fields

    def get_executed_by_name(self, obj):
        if obj.executed_by:
            return obj.executed_by.username
        return None
