"""
测试用例模块 - 序列化器

提供测试用例相关的数据序列化。
"""

from rest_framework import serializers
from apps.testcase.models import (
    TestCaseRepository,
    TestCaseVersion,
    TestModule,
    TestCase,
    TestCaseReview,
    TestCaseExecution
)


class TestCaseListSerializer(serializers.ModelSerializer):
    """测试用例列表序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    created_by_avatar = serializers.CharField(source='created_by.avatar', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)
    last_execution_result = serializers.SerializerMethodField()

    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'module', 'module_name', 'version',
            'priority', 'automation_status', 'review_status', 'steps',
            'expected_result',
            'created_by', 'created_by_name', 'created_by_avatar',
            'last_execution_result', 'created_at', 'updated_at'
        ]

    def get_last_execution_result(self, obj):
        """获取最新执行结果

        优化：优先使用预加载的数据，避免 N+1 查询
        """
        # 检查是否有预加载的执行记录
        if hasattr(obj, '_prefetched_objects_cache') and 'executions' in obj._prefetched_objects_cache:
            executions = obj._prefetched_objects_cache['executions']
            if executions:
                # 预加载的数据已按 executed_at 排序，取第一个
                # 如果没有排序，需要手动排序
                sorted_executions = sorted(executions, key=lambda e: e.executed_at, reverse=True)
                return sorted_executions[0].result if sorted_executions else None
            return None

        # 没有预加载时，执行单次查询（用于单个对象详情）
        latest_execution = obj.executions.order_by('-executed_at').first()
        return latest_execution.result if latest_execution else None


class TestCaseDetailSerializer(serializers.ModelSerializer):
    """测试用例详情序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)

    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'module', 'module_name', 'version',
            'priority', 'estimated_hours', 'tags', 'automation_status',
            'automation_case_id', 'requirement', 'precondition', 'review_status',
            'steps', 'expected_result',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]


class TestCaseCreateUpdateSerializer(serializers.ModelSerializer):
    """测试用例创建/更新序列化器"""

    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'module', 'version',
            'priority', 'estimated_hours', 'tags', 'automation_status',
            'automation_case_id', 'requirement', 'precondition', 'review_status',
            'steps', 'expected_result'
        ]


class TestModuleSerializer(serializers.ModelSerializer):
    """测试模块序列化器"""
    children = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    class Meta:
        model = TestModule
        fields = ['id', 'name', 'version', 'parent', 'sort_order', 'children', 'count', 'created_at']

    def validate_parent(self, value):
        """验证 parent 字段，将空字符串转换为 None"""
        if value == '' or value == 'null' or value == 'undefined':
            return None
        return value

    def get_children(self, obj):
        """获取子模块 - 优先使用预加载的数据"""
        if hasattr(obj, '_children_list'):
            return TestModuleSerializer(obj._children_list, many=True, context=self.context).data

        if hasattr(obj, '_prefetched_objects_cache') and 'children' in obj._prefetched_objects_cache:
            children = obj._prefetched_objects_cache['children']
        else:
            children = obj.children.all().order_by('sort_order')

        return TestModuleSerializer(children, many=True, context=self.context).data

    def get_count(self, obj):
        """获取该模块下的用例数量（包括子模块）

        优化：优先使用预计算的统计数据，避免 N+1 查询
        """
        # 检查是否有预计算的统计数据（来自 ModuleService.get_module_statistics）
        if hasattr(obj, '_case_count'):
            return obj._case_count

        # 检查上下文中是否有预计算的统计数据
        if self.context and 'module_statistics' in self.context:
            statistics = self.context['module_statistics']
            if obj.id in statistics:
                return statistics[obj.id].get('count', 0)

        # 没有预计算数据时，使用优化的批量查询
        module_ids = self._get_all_module_ids(obj)
        return TestCase.objects.filter(module_id__in=module_ids).count()

    def _get_all_module_ids(self, module):
        """递归获取模块及其所有子模块的ID列表"""
        ids = [module.id]

        if hasattr(module, '_children_list'):
            children = module._children_list
        elif hasattr(module, '_prefetched_objects_cache') and 'children' in module._prefetched_objects_cache:
            children = module._prefetched_objects_cache['children']
        else:
            children = module.children.all()

        for child in children:
            ids.extend(self._get_all_module_ids(child))
        return ids


class TestModuleTreeSerializer(serializers.ModelSerializer):
    """模块树序列化器（只获取顶层模块）"""

    class Meta:
        model = TestModule
        fields = ['id', 'name', 'parent', 'sort_order', 'created_at']


class TestCaseVersionSerializer(serializers.ModelSerializer):
    """版本序列化器"""
    repository_name = serializers.CharField(source='repository.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = TestCaseVersion
        fields = [
            'id', 'name', 'repository', 'repository_name',
            'description', 'status', 'is_default',
            'created_by', 'created_by_name', 'created_at'
        ]


class TestCaseRepositorySerializer(serializers.ModelSerializer):
    """用例库序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    versions_count = serializers.SerializerMethodField()

    class Meta:
        model = TestCaseRepository
        fields = [
            'id', 'name', 'project', 'project_name',
            'description', 'is_default', 'versions_count',
            'created_by', 'created_by_name', 'created_at'
        ]

    def get_versions_count(self, obj):
        """获取版本数量

        优化：优先使用预加载的数据，避免 N+1 查询
        """
        # 检查是否有预加载的版本数据
        if hasattr(obj, '_prefetched_objects_cache') and 'versions' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['versions'])

        # 检查是否有预计算的数量（使用 annotate）
        if hasattr(obj, '_versions_count'):
            return obj._versions_count

        # 没有预加载时执行查询
        return obj.versions.count()


class TestCaseReviewSerializer(serializers.ModelSerializer):
    """用例评审序列化器"""
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)

    class Meta:
        model = TestCaseReview
        fields = [
            'id', 'test_case', 'test_case_title', 'reviewer', 'reviewer_name',
            'status', 'comment', 'revision_number', 'revision_note', 'previous_review',
            'created_at', 'updated_at'
        ]


class TestCaseExecutionSerializer(serializers.ModelSerializer):
    """用例执行记录序列化器"""
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)
    test_case_title = serializers.CharField(source='test_case.title', read_only=True)

    class Meta:
        model = TestCaseExecution
        fields = [
            'id', 'test_case', 'test_case_title', 'executed_by', 'executed_by_name',
            'result', 'actual_result', 'remark', 'executed_at'
        ]
