"""
项目模块 - 序列化器

提供项目相关的数据序列化。
"""

from rest_framework import serializers


class ProjectSerializer(serializers.Serializer):
    """项目基础序列化器"""
    id = serializers.CharField()
    name = serializers.CharField()
    identifier = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)
    owner_name = serializers.CharField(required=False)
    member_count = serializers.IntegerField(required=False)


class ProjectListSerializer(serializers.Serializer):
    """项目列表序列化器"""
    projects = ProjectSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    limit = serializers.IntegerField()


class ProjectCreateSerializer(serializers.Serializer):
    """项目创建序列化器"""
    name = serializers.CharField(max_length=100)
    identifier = serializers.CharField(max_length=20)
    description = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(default='software')


class ProjectUpdateSerializer(serializers.Serializer):
    """项目更新序列化器"""
    name = serializers.CharField(required=False, max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)
    type = serializers.CharField(required=False)


class ProjectMemberSerializer(serializers.Serializer):
    """项目成员序列化器"""
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField(required=False)
    role = serializers.CharField()
    status = serializers.CharField()
    joined_at = serializers.DateTimeField()
    is_favorite = serializers.BooleanField(required=False)


class ProjectMemberListSerializer(serializers.Serializer):
    """项目成员列表序列化器"""
    members = ProjectMemberSerializer(many=True)


class ProjectRoleSerializer(serializers.Serializer):
    """项目角色序列化器"""
    key = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    permissions = serializers.ListField(child=serializers.CharField())


class ProjectStatsSerializer(serializers.Serializer):
    """项目统计序列化器"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    archived = serializers.IntegerField()
    owned = serializers.IntegerField()


class KnowledgeBaseSerializer(serializers.Serializer):
    """知识库序列化器"""
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
