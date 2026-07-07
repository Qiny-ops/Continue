# -*- coding: utf-8 -*-
"""
接口测试视图模块
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.users.authentication import JWTAuthentication
from apps.apitest.models import ApiEnvironment
from apps.apitest.serializers import (
    ApiEnvironmentSerializer,
    ApiEnvironmentListSerializer
)
from apps.projects.models import Project, ProjectMember


class ApiEnvironmentViewSet(viewsets.ModelViewSet):
    """
    API 测试环境管理

    list: 获取环境列表
    create: 创建环境
    retrieve: 获取环境详情
    update: 更新环境
    destroy: 删除环境
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取用户有权限的项目环境"""
        project_param = self.request.query_params.get('project')
        queryset = ApiEnvironment.objects.select_related('project', 'created_by')

        if project_param:
            # 支持通过 id 或 code 查询
            try:
                project_id = int(project_param)
            except (ValueError, TypeError):
                # 如果不是数字，尝试通过 code 查找
                try:
                    project = Project.objects.get(code=project_param)
                    project_id = project.id
                except Project.DoesNotExist:
                    return queryset.none()
            queryset = queryset.filter(project_id=project_id)

        # 只返回用户有权限的项目环境
        user_project_ids = ProjectMember.objects.filter(
            user=self.request.user
        ).values_list('project_id', flat=True)

        return queryset.filter(project_id__in=user_project_ids)

    def get_serializer_class(self):
        if self.action == 'list':
            return ApiEnvironmentListSerializer
        return ApiEnvironmentSerializer

    def perform_create(self, serializer):
        """创建环境，支持通过 project code 创建"""
        project_code = serializer.validated_data.get('project')

        # project 通过 SlugRelatedField 验证后已是 Project 对象
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置默认环境"""
        environment = self.get_object()

        # 清除同项目其他默认环境
        ApiEnvironment.objects.filter(
            project=environment.project,
            is_default=True
        ).update(is_default=False)

        # 设置当前为默认
        environment.is_default = True
        environment.save(update_fields=['is_default'])

        return Response({'message': '已设置为默认环境'})

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试环境连接"""
        environment = self.get_object()

        # TODO: 实现实际的连接测试
        return Response({
            'success': True,
            'message': f'环境 {environment.name} 连接正常'
        })


# 导入其他视图
from .api_testcase import ApiTestCaseViewSet, ApiTestRunViewSet

__all__ = [
    'ApiEnvironmentViewSet',
    'ApiTestCaseViewSet',
    'ApiTestRunViewSet',
]