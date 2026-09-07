"""
需求视图层
"""
import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.users.authentication import JWTAuthentication
from apps.core.response import StandardResponse
from apps.requirement.models import Requirement
from apps.requirement.repositories.requirement_repository import RequirementRepository
from apps.requirement.services.requirement_service import RequirementService
from apps.requirement.serializers.requirement_serializers import (
    RequirementListSerializer,
    RequirementDetailSerializer,
    RequirementCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class RequirementViewSet(viewsets.ModelViewSet):
    serializer_class = RequirementListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'version', 'status', 'priority', 'source']
    search_fields = ['title', 'func_point']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        version_id = self.request.query_params.get('version')
        if version_id:
            return RequirementService.get_requirements_by_version(
                version_id, self.request.query_params
            )[0]
        project_id = self.request.query_params.get('project')
        if project_id:
            return RequirementRepository.get_by_project(project_id)
        return Requirement.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RequirementDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return RequirementCreateUpdateSerializer
        return RequirementListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        # 版本归档只读校验
        instance = self.get_object()
        if instance.is_readonly:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('该需求所属版本已归档，不可修改')
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, pk=None):
        result, error = RequirementService.delete_requirement(pk)
        if error:
            return StandardResponse(message=error, code=400)
        return StandardResponse(message='删除成功')

    @action(detail=False, methods=['get'])
    def by_version(self, request):
        version_id = request.query_params.get('version')
        if not version_id:
            return StandardResponse(message='缺少版本ID', code=400)

        queryset, error = RequirementService.get_requirements_by_version(
            version_id, request.query_params
        )
        if error:
            return StandardResponse(message=error, code=400)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RequirementListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RequirementListSerializer(queryset, many=True)
        return StandardResponse(data=serializer.data)

    @action(detail=False, methods=['get'])
    def module_statistics(self, request):
        """获取版本下各模块的需求统计"""
        version_id = request.query_params.get('version')
        if not version_id:
            return StandardResponse(message='缺少版本ID', code=400)

        stats = RequirementRepository.get_module_statistics(version_id)
        return StandardResponse(data=stats)

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return StandardResponse(message='请选择要删除的需求', code=400)

        result, error = RequirementService.batch_delete(ids)
        if error:
            return StandardResponse(message=error, code=400)
        return StandardResponse(data=result, message='批量删除成功')

    @action(detail=True, methods=['post'], url_path='generate-testcases')
    def generate_testcases(self, request, pk=None):
        """从单个需求生成测试用例"""
        requirement = self.get_object()
        version_id = request.data.get('version_id')
        if not version_id:
            return StandardResponse(message='请选择目标版本', code=400)

        from apps.requirement.services.requirement_generate_service import RequirementGenerateService
        result, error = RequirementGenerateService.generate_from_requirement(
            requirement_id=requirement.id,
            version_id=version_id,
            user=request.user,
        )
        if error:
            return StandardResponse(message=error, code=400)
        return StandardResponse(data=result, message='生成完成')

    @action(detail=False, methods=['post'], url_path='batch-generate-testcases')
    def batch_generate_testcases(self, request):
        """从多个需求批量生成测试用例"""
        ids = request.data.get('ids', [])
        version_id = request.data.get('version_id')
        if not ids:
            return StandardResponse(message='请选择需求', code=400)
        if not version_id:
            return StandardResponse(message='请选择目标版本', code=400)

        from apps.requirement.services.requirement_generate_service import RequirementGenerateService
        result, error = RequirementGenerateService.batch_generate_from_requirements(
            requirement_ids=ids,
            version_id=version_id,
            user=request.user,
        )
        if error:
            return StandardResponse(message=error, code=400)
        return StandardResponse(data=result, message='批量生成完成')
