"""
需求序列化器
"""
from rest_framework import serializers
from apps.requirement.models import Requirement


class RequirementListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    testcase_count = serializers.IntegerField(read_only=True, default=0)
    is_readonly = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Requirement
        fields = [
            'id', 'project', 'version', 'title', 'func_point',
            'priority', 'status', 'source', 'is_readonly',
            'created_by', 'created_by_name', 'testcase_count',
            'created_at', 'updated_at'
        ]


class RequirementDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, default='')
    testcase_count = serializers.IntegerField(read_only=True, default=0)
    is_readonly = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Requirement
        fields = [
            'id', 'project', 'version', 'title', 'description', 'func_point',
            'priority', 'status', 'source', 'is_readonly',
            'knowledge_base_id', 'knowledge_id', 'session_id',
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name',
            'testcase_count',
            'created_at', 'updated_at'
        ]


class RequirementCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = [
            'id', 'project', 'version', 'title', 'description', 'func_point',
            'priority', 'status',
        ]
