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
from apps.apitest.services import ApiTestPermissionService
from apps.projects.models import Project


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

        # 按用途类型过滤（接口测试 / Web 自动化）
        target_type = self.request.query_params.get('target_type')
        if target_type in ('api', 'web'):
            queryset = queryset.filter(target_type=target_type)

        # 只返回用户有权限的项目环境
        user_project_ids = ApiTestPermissionService.get_user_project_ids(self.request.user)

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
        import logging
        import urllib.parse
        from urllib.request import Request, urlopen
        from urllib.error import URLError

        logger = logging.getLogger(__name__)
        environment = self.get_object()
        base_url = (environment.base_url or '').strip()

        if not base_url:
            return Response({
                'success': False,
                'message': '环境未配置 Base URL',
            }, status=400)

        parsed = urllib.parse.urlparse(base_url)
        if parsed.scheme not in ('http', 'https'):
            return Response({
                'success': False,
                'message': f'不支持的协议: {parsed.scheme}',
            }, status=400)

        # 健康检查路径：优先用 _health，回退到 /
        for path in ('/_health', '/health', '/'):
            try:
                check_url = urllib.parse.urljoin(base_url, path)
                req = Request(check_url, method='HEAD')
                req.add_header('User-Agent', 'ApiTesting/1.0 HealthCheck')
                with urlopen(req, timeout=5) as resp:
                    logger.info(
                        'Connection test to %s: HTTP %s (via %s)',
                        environment.name, resp.status, check_url,
                    )
                    return Response({
                        'success': True,
                        'message': f'环境 {environment.name} 连接正常 (HTTP {resp.status})',
                        'detail': {
                            'checked_url': check_url,
                            'status_code': resp.status,
                        },
                    })
            except URLError as e:
                logger.warning('Connection test %s → %s failed: %s', environment.name, check_url, e)
                continue
            except Exception:
                logger.warning(
                    'Connection test %s → %s failed unexpectedly',
                    environment.name, check_url, exc_info=True,
                )
                continue

        return Response({
            'success': False,
            'message': f'环境 {environment.name} 连接失败: 无法访问 {base_url}',
        }, status=502)


# 导入其他视图
from .api_testcase import ApiTestCaseViewSet, ApiTestRunViewSet

__all__ = [
    'ApiEnvironmentViewSet',
    'ApiTestCaseViewSet',
    'ApiTestRunViewSet',
]