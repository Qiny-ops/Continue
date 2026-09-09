# -*- coding: utf-8 -*-
"""代码检查序列化器"""

from rest_framework import serializers

from apps.codecheck.models import CodeCheckTask, CodeCheckResult


class CodeCheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeCheckResult
        fields = [
            "id", "case_no", "testpoint", "steps", "expectation",
            "result", "reason", "success",
            "failure_type", "failure_reason", "evidence",
        ]


class CodeCheckTaskListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CodeCheckTask
        fields = [
            "id", "project", "project_name", "repository_url", "branch",
            "service_task_id", "trigger_source", "case_source", "commit_author", "status",
            "progress", "risk_level", "risk_score", "conclusion",
            "gate_provider", "gate_state", "created_by", "created_by_name", "created_at", "updated_at",
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else ""


class CodeCheckTaskDetailSerializer(serializers.ModelSerializer):
    results = CodeCheckResultSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CodeCheckTask
        fields = [
            "id", "project", "project_name", "repository_url", "branch",
            "commit_sha", "commit_author", "service_task_id", "trigger_source", "case_source",
            "test_case_file", "status", "progress", "risk_level", "risk_score",
            "risk_files", "risk_reason", "diff_info", "summary", "conclusion",
            "gate_provider", "gate_state", "gate_response", "error",
            "results", "created_by", "created_by_name", "created_at", "updated_at",
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else ""
