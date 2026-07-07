"""
测试用例视图层 - ViewSets

视图层只负责：
1. 接收请求参数
2. 调用 Service 层处理业务逻辑
3. 返回响应

严格遵循分层架构：
- 视图层不直接访问 Model
- 视图层不直接访问 Repository
- 所有业务逻辑通过 Service 层处理
"""

import logging
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.authentication import JWTAuthentication
from apps.core.response import StandardResponse
from apps.core.permissions import is_system_admin
from apps.testcase.services import (
    RepositoryService, VersionService, ModuleService,
    TestCaseService, ReviewService, ExecutionService
)
from apps.testcase.serializers import (
    TestCaseRepositorySerializer, TestCaseVersionSerializer,
    TestModuleSerializer, TestModuleTreeSerializer,
    TestCaseListSerializer, TestCaseDetailSerializer,
    TestCaseCreateUpdateSerializer, TestCaseReviewSerializer,
    TestCaseExecutionSerializer
)


logger = logging.getLogger(__name__)


class TestCaseRepositoryViewSet(viewsets.ModelViewSet):
    """用例库 API"""
    serializer_class = TestCaseRepositorySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        if is_system_admin(self.request.user):
            return RepositoryService.get_all_repositories()
        return RepositoryService.get_user_accessible_repositories(self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, pk=None):
        """删除用例库

        业务逻辑：
        1. 首次调用返回关联数据统计，需要用户确认
        2. 确认后（force=true）执行删除
        """
        force = request.query_params.get('force', 'false').lower() == 'true'

        result, error = RepositoryService.delete_repository(pk, request.user, force=force)
        if error:
            return StandardResponse(message=error, code=400)

        if result.get('need_confirm'):
            return StandardResponse(data=result, code=200)

        return StandardResponse(data=result, message=result.get('message'))

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取用例库统计信息"""
        stats = RepositoryService.get_repository_stats(pk)
        return StandardResponse(data=stats)


class TestCaseVersionViewSet(viewsets.ModelViewSet):
    """版本 API"""
    serializer_class = TestCaseVersionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['repository', 'status', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return VersionService.get_all_versions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置默认版本"""
        success, error = VersionService.set_default(pk)
        if error:
            return StandardResponse(message=error, code=404)
        return StandardResponse(message='已设置为默认版本')


class TestModuleViewSet(viewsets.ModelViewSet):
    """模块 API"""
    serializer_class = TestModuleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['version', 'parent']
    search_fields = ['name']
    ordering_fields = ['sort_order', 'created_at']
    ordering = ['sort_order', 'created_at']

    def get_queryset(self):
        queryset = ModuleService.get_all_modules()
        if self.action == 'list':
            queryset = ModuleService.get_modules_with_relations()
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return TestModuleTreeSerializer
        return TestModuleSerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取模块树

        优化：预计算模块统计数据，避免 N+1 查询
        """
        version_id = request.query_params.get('version')
        if not version_id:
            return StandardResponse(message='version parameter is required', code=400)

        modules = ModuleService.get_modules_by_version(version_id)
        root_modules = ModuleService.build_tree(modules)

        # 预计算模块统计数据，避免序列化时的 N+1 查询
        statistics = ModuleService.get_module_statistics(version_id)

        serializer = TestModuleSerializer(
            root_modules,
            many=True,
            context={'module_statistics': statistics}
        )
        return StandardResponse(data=serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取模块统计信息"""
        version_id = request.query_params.get('version')
        if not version_id:
            return StandardResponse(message='version parameter is required', code=400)

        statistics = ModuleService.get_module_statistics(version_id)
        return StandardResponse(data=statistics)

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除模块

        业务逻辑：
        1. 如果模块下有测试用例，需要用户确认是否同时删除用例
        2. delete_cases=true 时同时删除模块和用例
        """
        ids = request.data.get('ids', [])
        version_id = request.data.get('version')
        delete_cases = request.data.get('delete_cases', False)

        if not ids:
            return StandardResponse(message='ids parameter is required', code=400)
        if not version_id:
            return StandardResponse(message='version parameter is required', code=400)

        deleted_modules_count, deleted_cases_count, error = ModuleService.batch_delete_modules(
            ids, version_id, delete_cases=delete_cases
        )
        if error:
            return StandardResponse(message=error, code=400)

        message = f'成功删除 {deleted_modules_count} 个模块'
        if deleted_cases_count > 0:
            message += f'，同时删除 {deleted_cases_count} 个测试用例'

        return StandardResponse(
            data={
                'deleted_modules_count': deleted_modules_count,
                'deleted_cases_count': deleted_cases_count
            },
            message=message
        )


class TestCaseViewSet(viewsets.ModelViewSet):
    """测试用例 API"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['version', 'module', 'priority', 'automation_status', 'review_status']
    search_fields = ['title', 'precondition', 'requirement']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        if is_system_admin(self.request.user):
            return TestCaseService.get_all_test_cases()
        return TestCaseService.get_user_accessible_cases(self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return TestCaseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TestCaseCreateUpdateSerializer
        return TestCaseDetailSerializer

    def perform_create(self, serializer):
        try:
            test_case = TestCaseService.create_test_case(
                serializer.validated_data, self.request.user
            )
            serializer.instance = test_case
        except Exception as e:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(str(e))

    def perform_update(self, serializer):
        try:
            test_case = TestCaseService.update_test_case(
                serializer.instance, serializer.validated_data, self.request.user
            )
            serializer.instance = test_case
        except Exception as e:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(str(e))

    def perform_destroy(self, instance):
        success, error = TestCaseService.delete_test_case(instance, self.request.user)
        if error:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(error)

    @action(detail=False, methods=['get'])
    def by_version(self, request):
        """根据版本获取用例列表（支持搜索和筛选）"""
        version_id = request.query_params.get('version')
        if not version_id:
            return StandardResponse(message='version parameter is required', code=400)

        test_cases = TestCaseService.get_test_cases_by_version(version_id, {
            'user': request.user,
            'is_admin': is_system_admin(request.user)
        })

        # 应用搜索筛选
        search_query = request.query_params.get('search')
        if search_query:
            test_cases = test_cases.filter(
                title__icontains=search_query
            ) | test_cases.filter(
                precondition__icontains=search_query
            ) | test_cases.filter(
                requirement__icontains=search_query
            )

        # 应用优先级筛选
        priority = request.query_params.get('priority')
        if priority:
            test_cases = test_cases.filter(priority=priority)

        # 应用执行状态筛选
        last_execution_result = request.query_params.get('last_execution_result')
        if last_execution_result:
            test_cases = test_cases.filter(last_execution_result=last_execution_result)

        # 应用排序
        test_cases = test_cases.order_by('-created_at')

        page = self.paginate_queryset(test_cases)
        if page is not None:
            serializer = TestCaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TestCaseListSerializer(test_cases, many=True)
        return StandardResponse(data=serializer.data, message='获取成功')

    @action(detail=False, methods=['get'])
    def by_module(self, request):
        """根据模块获取用例列表（支持搜索和筛选）"""
        module_id = request.query_params.get('module')
        if not module_id:
            return StandardResponse(message='module parameter is required', code=400)

        test_cases = TestCaseService.get_test_cases_by_module(module_id, {
            'user': request.user,
            'is_admin': is_system_admin(request.user)
        })

        # 应用搜索筛选
        search_query = request.query_params.get('search')
        if search_query:
            test_cases = test_cases.filter(
                title__icontains=search_query
            ) | test_cases.filter(
                precondition__icontains=search_query
            ) | test_cases.filter(
                requirement__icontains=search_query
            )

        # 应用优先级筛选
        priority = request.query_params.get('priority')
        if priority:
            test_cases = test_cases.filter(priority=priority)

        # 应用执行状态筛选
        last_execution_result = request.query_params.get('last_execution_result')
        if last_execution_result:
            test_cases = test_cases.filter(last_execution_result=last_execution_result)

        # 应用排序
        test_cases = test_cases.order_by('-created_at')

        page = self.paginate_queryset(test_cases)
        if page is not None:
            serializer = TestCaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TestCaseListSerializer(test_cases, many=True)
        return StandardResponse(data=serializer.data, message='获取成功')

    @action(detail=False, methods=['get'])
    def by_module_tree(self, request):
        """根据模块获取用例列表（包含所有子模块的用例，支持搜索和筛选）"""
        module_id = request.query_params.get('module')
        if not module_id:
            return StandardResponse(message='module parameter is required', code=400)

        test_cases, error = TestCaseService.get_test_cases_by_module_tree(
            module_id, request.user
        )
        if error:
            return StandardResponse(message=error, code=404)

        # 应用搜索筛选
        search_query = request.query_params.get('search')
        if search_query:
            test_cases = test_cases.filter(
                title__icontains=search_query
            ) | test_cases.filter(
                precondition__icontains=search_query
            ) | test_cases.filter(
                requirement__icontains=search_query
            )

        # 应用优先级筛选
        priority = request.query_params.get('priority')
        if priority:
            test_cases = test_cases.filter(priority=priority)

        # 应用执行状态筛选
        last_execution_result = request.query_params.get('last_execution_result')
        if last_execution_result:
            test_cases = test_cases.filter(last_execution_result=last_execution_result)

        # 应用排序
        test_cases = test_cases.order_by('-created_at')

        page = self.paginate_queryset(test_cases)
        if page is not None:
            serializer = TestCaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TestCaseListSerializer(test_cases, many=True)
        return StandardResponse(data=serializer.data, message='获取成功')

    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """根据项目获取用例列表"""
        project_identifier = request.query_params.get('project')
        if not project_identifier:
            return StandardResponse(message='project parameter is required', code=400)

        queryset, error = TestCaseService.get_test_cases_by_project(
            project_identifier, request.user
        )
        if error:
            code = 404 if '不存在' in error else 403
            return StandardResponse(message=error, code=code)

        if queryset is None:
            return StandardResponse(data=[])

        # 支持按 review_status 筛选
        review_status = request.query_params.get('review_status')
        if review_status:
            queryset = queryset.filter(review_status=review_status)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TestCaseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TestCaseListSerializer(queryset, many=True)
        return StandardResponse(data=serializer.data, message='获取成功')

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """复制用例"""
        source_case = self.get_object()

        try:
            new_case = TestCaseService.copy_test_case(source_case, request.user)
        except Exception as e:
            return StandardResponse(message=str(e), code=403)

        serializer = TestCaseDetailSerializer(new_case)
        return StandardResponse(data=serializer.data, message='复制成功')

    @action(detail=False, methods=['post'])
    def batch_copy(self, request):
        """批量复制用例"""
        ids = request.data.get('ids', [])
        if not ids:
            return StandardResponse(message='ids parameter is required', code=400)

        try:
            copied_count = TestCaseService.batch_copy_test_cases(ids, request.user)
            return StandardResponse(
                data={'copied_count': copied_count},
                message=f'成功复制 {copied_count} 个用例'
            )
        except Exception as e:
            return StandardResponse(message=str(e), code=403)

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除用例"""
        ids = request.data.get('ids', [])
        if not ids:
            return StandardResponse(message='ids parameter is required', code=400)

        try:
            deleted_count = TestCaseService.batch_delete_test_cases(ids, request.user)
            return StandardResponse(
                data={'deleted_count': deleted_count},
                message=f'成功删除 {deleted_count} 个用例'
            )
        except Exception as e:
            return StandardResponse(message=str(e), code=403)

    @action(detail=False, methods=['post'])
    def batch_move(self, request):
        """批量移动用例到目标模块"""
        ids = request.data.get('ids', [])
        target_module_id = request.data.get('target_module')

        if not ids:
            return StandardResponse(message='ids parameter is required', code=400)
        if not target_module_id:
            return StandardResponse(message='target_module parameter is required', code=400)

        moved_count, error = TestCaseService.batch_move_test_cases(
            ids, target_module_id, request.user
        )
        if error:
            return StandardResponse(message=error, code=400)

        return StandardResponse(
            data={'moved_count': moved_count},
            message=f'成功移动 {moved_count} 个用例'
        )

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """批量更新用例属性"""
        ids = request.data.get('ids', [])
        if not ids:
            return StandardResponse(message='ids parameter is required', code=400)

        try:
            updated_count = TestCaseService.batch_update_test_cases(
                ids, request.data, request.user
            )
            return StandardResponse(
                data={'updated_count': updated_count},
                message=f'成功更新 {updated_count} 个用例'
            )
        except Exception as e:
            return StandardResponse(message=str(e), code=403)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """通过评审"""
        test_case = self.get_object()
        comment = request.data.get('comment', '')

        # 检查评审权限
        if not ReviewService.check_review_permission(test_case, request.user):
            return StandardResponse(message='您没有权限评审该测试用例', code=403)

        try:
            review = ReviewService.approve_review(test_case, request.user, comment)
            return StandardResponse(
                data=TestCaseReviewSerializer(review).data,
                message='评审通过'
            )
        except Exception as e:
            return StandardResponse(message=str(e), code=400)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """驳回评审"""
        test_case = self.get_object()
        comment = request.data.get('comment', '')

        if not comment or not comment.strip():
            return StandardResponse(message='驳回原因不能为空', code=400)

        # 检查评审权限
        if not ReviewService.check_review_permission(test_case, request.user):
            return StandardResponse(message='您没有权限评审该测试用例', code=403)

        try:
            review = ReviewService.reject_with_feedback(test_case, request.user, comment)
            return StandardResponse(
                data=TestCaseReviewSerializer(review).data,
                message='已驳回'
            )
        except Exception as e:
            return StandardResponse(message=str(e), code=400)

    @action(detail=True, methods=['post'])
    def resubmit(self, request, pk=None):
        """修改后重新提交评审"""
        test_case = self.get_object()
        revision_note = request.data.get('revision_note', '')

        try:
            review = ReviewService.resubmit_for_review(test_case, request.user, revision_note)
            return StandardResponse(
                data=TestCaseReviewSerializer(review).data,
                message='已重新提交评审'
            )
        except ValueError as e:
            return StandardResponse(message=str(e), code=400)

    @action(detail=True, methods=['get'])
    def review_history(self, request, pk=None):
        """获取评审历史"""
        reviews = ReviewService.get_review_history(pk)
        return StandardResponse(data=TestCaseReviewSerializer(reviews, many=True).data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出测试用例（不分页，用于批量导出）

        参数：
        - version: 版本ID（必填）
        - module: 模块ID（可选，导出指定模块及子模块的用例）
        """
        version_id = request.query_params.get('version')
        module_id = request.query_params.get('module')

        if not version_id and not module_id:
            return StandardResponse(message='version 或 module 参数至少需要一个', code=400)

        if module_id:
            # 按模块导出（包含子模块）
            test_cases, error = TestCaseService.get_test_cases_by_module_tree(
                module_id, request.user
            )
            if error:
                return StandardResponse(message=error, code=404)
        else:
            # 按版本导出
            test_cases = TestCaseService.get_test_cases_by_version(version_id, {
                'user': request.user,
                'is_admin': is_system_admin(request.user)
            })

        # 应用排序
        test_cases = test_cases.order_by('module__sort_order', '-created_at')

        # 序列化
        serializer = TestCaseListSerializer(test_cases, many=True)
        return StandardResponse(data=serializer.data, message='获取成功')


class TestCaseReviewViewSet(viewsets.ModelViewSet):
    """用例评审 API"""
    serializer_class = TestCaseReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['test_case', 'reviewer', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return ReviewService.get_user_accessible_reviews(self.request.user)

    def perform_create(self, serializer):
        test_case = serializer.validated_data.get('test_case')
        if test_case:
            has_permission = ReviewService.check_review_permission(
                test_case, self.request.user
            )
            if not has_permission:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您没有权限评审该测试用例')

        serializer.save(reviewer=self.request.user)


class TestCaseExecutionViewSet(viewsets.ModelViewSet):
    """用例执行记录 API"""
    serializer_class = TestCaseExecutionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['test_case', 'executed_by', 'result']
    ordering_fields = ['executed_at']
    ordering = ['-executed_at']

    def get_queryset(self):
        return ExecutionService.get_user_accessible_executions(self.request.user)

    def perform_create(self, serializer):
        test_case = serializer.validated_data.get('test_case')
        if test_case:
            has_permission, error = ExecutionService.check_execution_permission(
                test_case, self.request.user
            )
            if not has_permission:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(error)

        serializer.save(executed_by=self.request.user)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取用例执行统计"""
        stats = ExecutionService.get_execution_statistics(pk)
        return StandardResponse(data=stats)

    @action(detail=True, methods=['get'])
    def since_approval(self, request, pk=None):
        """获取评审通过后的执行记录"""
        executions = ExecutionService.get_executions_since_approval(pk)
        page = self.paginate_queryset(executions)
        if page is not None:
            serializer = TestCaseExecutionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TestCaseExecutionSerializer(executions, many=True)
        return StandardResponse(data=serializer.data)
