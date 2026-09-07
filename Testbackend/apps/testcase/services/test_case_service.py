"""
测试用例服务层
"""

import logging
import hashlib
import time
from django.db import transaction
from django.core.cache import cache
from apps.core.permissions import is_system_admin, has_project_permission
from apps.testcase.models import TestCase
from apps.testcase.repositories import ModuleRepository

logger = logging.getLogger(__name__)


class IdempotencyService:
    """幂等性服务

    用于防止重复提交导致的重复操作
    """

    IDEMPOTENCY_KEY_PREFIX = 'idempotency_'
    IDEMPOTENCY_KEY_TTL = 3600  # 1小时

    @staticmethod
    def generate_key(operation, user_id, data_hash):
        """生成幂等键"""
        return f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{operation}_{user_id}_{data_hash}"

    @staticmethod
    def check_and_set(operation, user_id, data_hash, result=None):
        """检查幂等键，如果已存在则返回之前的结果，否则设置新键"""
        key = IdempotencyService.generate_key(operation, user_id, data_hash)

        # 检查是否已存在
        cached_result = cache.get(key)
        if cached_result is not None:
            logger.info(f"幂等键命中: {key}")
            return cached_result, True  # 返回缓存结果和命中标志

        # 设置新键（如果提供了结果）
        if result is not None:
            cache.set(key, result, IdempotencyService.IDEMPOTENCY_KEY_TTL)

        return None, False

    @staticmethod
    def set_result(operation, user_id, data_hash, result):
        """设置幂等结果"""
        key = IdempotencyService.generate_key(operation, user_id, data_hash)
        cache.set(key, result, IdempotencyService.IDEMPOTENCY_KEY_TTL)

    @staticmethod
    def generate_data_hash(data):
        """生成数据哈希值"""
        import json
        # 对数据进行排序后序列化，确保相同数据生成相同哈希
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()


class TestCaseService:
    """测试用例服务"""

    @staticmethod
    def get_all_test_cases():
        """获取所有测试用例（管理员用）

        优化：预加载执行记录，避免 N+1 查询
        """
        return TestCase.objects.select_related(
            'version', 'version__repository', 'version__repository__project',
            'module', 'created_by', 'updated_by'
        ).prefetch_related(
            'executions'  # 预加载执行记录
        )

    @staticmethod
    def check_version_permission(version, user, require_write=False):
        """检查用户对版本的权限

        业务逻辑：
        1. 检查用户是否有项目权限
        2. 如果需要写权限，检查版本是否已归档
        """
        if not version or not version.repository or not version.repository.project:
            return False

        project = version.repository.project

        # 检查版本是否已归档
        if require_write and version.status == 'archived':
            # 归档版本不允许写入操作
            return False

        if require_write:
            return has_project_permission(project.id, user, 'testcase_manage')
        else:
            return has_project_permission(project.id, user, 'testcase_view')

    @staticmethod
    def get_user_accessible_cases(user):
        """获取用户有权限访问的测试用例

        优化：预加载执行记录，避免 N+1 查询
        """
        from apps.projects.models import ProjectMember, Project

        if is_system_admin(user):
            return TestCase.objects.all().select_related(
                'version', 'module', 'created_by', 'updated_by'
            ).prefetch_related(
                'executions'  # 预加载执行记录
            )

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )

        return TestCase.objects.filter(
            version__repository__project_id__in=member_project_ids | owned_project_ids
        ).select_related(
            'version', 'module', 'created_by', 'updated_by'
        ).prefetch_related(
            'executions'  # 预加载执行记录
        ).distinct()

    @staticmethod
    def get_test_cases_by_version(version_id, context=None):
        """获取版本下的测试用例列表"""
        queryset = TestCase.objects.filter(version_id=version_id)

        if context and not context.get('is_admin'):
            user = context.get('user')
            if user:
                queryset = queryset.filter(
                    version__repository__project_id__in=TestCaseService._get_user_project_ids(user)
                )

        return queryset.select_related('module', 'created_by')

    @staticmethod
    def get_test_cases_by_module(module_id, context=None):
        """获取模块下的测试用例列表"""
        queryset = TestCase.objects.filter(module_id=module_id)

        if context and not context.get('is_admin'):
            user = context.get('user')
            if user:
                queryset = queryset.filter(
                    version__repository__project_id__in=TestCaseService._get_user_project_ids(user)
                )

        return queryset.select_related('version', 'created_by')

    @staticmethod
    def get_test_cases_by_module_tree(module_id, user):
        """获取模块及其子模块的测试用例"""
        module = ModuleRepository.get_by_id(module_id)
        if not module:
            raise NotFoundError('模块不存在')

        module_ids = ModuleRepository.get_all_descendant_ids(module_id, module.version_id)
        queryset = TestCase.objects.filter(module_id__in=module_ids)

        if not is_system_admin(user):
            queryset = queryset.filter(
                version__repository__project_id__in=TestCaseService._get_user_project_ids(user)
            )

        return queryset.select_related('version', 'module', 'created_by'), None

    @staticmethod
    def _get_user_project_ids(user):
        """获取用户有权限的项目ID列表"""
        from apps.projects.models import ProjectMember, Project

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )
        return member_project_ids | owned_project_ids

    @staticmethod
    def get_test_cases_by_project(project_identifier, user):
        """根据项目获取测试用例"""
        from apps.projects.repositories import ProjectRepository, ProjectMemberRepository
        from apps.testcase.models import TestCaseRepository, TestCaseVersion

        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            raise NotFoundError('项目不存在')

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                raise BusinessError('您没有权限访问该项目')

        repositories = TestCaseRepository.objects.filter(project=project)
        if not repositories:
            return TestCase.objects.none(), None

        versions = TestCaseVersion.objects.filter(repository__in=repositories)
        if not versions:
            return TestCase.objects.none(), None

        queryset = TestCase.objects.filter(version__in=versions).select_related(
            'version', 'module', 'created_by', 'updated_by'
        )

        return queryset

    @staticmethod
    @transaction.atomic
    def create_test_case(data, created_by):
        """创建测试用例

        业务逻辑：
        1. 检查版本权限
        2. 归档版本不允许创建用例
        """
        version = data.get('version')
        if not version:
            raise Exception('必须指定版本')

        # 检查版本是否已归档
        if version.status == 'archived':
            raise Exception('该版本已归档，无法创建测试用例')

        if not TestCaseService.check_version_permission(version, created_by, require_write=True):
            raise Exception('您没有权限在该版本中创建测试用例')

        test_case = TestCase.objects.create(
            **data,
            created_by=created_by,
            updated_by=created_by
        )

        return test_case

    @staticmethod
    @transaction.atomic
    def update_test_case(test_case, data, updated_by):
        """更新测试用例

        业务逻辑：
        1. 检查版本权限
        2. 归档版本不允许更新用例
        """
        version = data.get('version') or test_case.version

        # 检查版本是否已归档
        if version.status == 'archived':
            raise Exception('该版本已归档，无法修改测试用例')

        if not TestCaseService.check_version_permission(version, updated_by, require_write=True):
            raise Exception('您没有权限修改该测试用例')

        for field, value in data.items():
            if hasattr(test_case, field):
                setattr(test_case, field, value)

        test_case.updated_by = updated_by
        test_case.save()

        return test_case

    @staticmethod
    def delete_test_case(test_case, user):
        """删除测试用例

        业务逻辑：
        1. 检查版本权限
        2. 归档版本不允许删除用例
        """
        # 检查版本是否已归档
        if test_case.version.status == 'archived':
            raise BusinessError('该版本已归档，无法删除测试用例')

        if not TestCaseService.check_version_permission(test_case.version, user, require_write=True):
            raise BusinessError('您没有权限删除该测试用例')

        test_case.delete()
        return True

    @staticmethod
    @transaction.atomic
    def copy_test_case(source_case, created_by):
        """复制测试用例"""
        if not TestCaseService.check_version_permission(source_case.version, created_by, require_write=True):
            raise Exception('您没有权限复制该测试用例')

        new_case = TestCase.objects.create(
            title=f"{source_case.title} (复制)",
            module=source_case.module,
            version=source_case.version,
            priority=source_case.priority,
            estimated_hours=source_case.estimated_hours,
            tags=source_case.tags,
            automation_status=source_case.automation_status,
            automation_case_id=source_case.automation_case_id,
            requirement=source_case.requirement,
            precondition=source_case.precondition,
            steps=source_case.steps,
            expected_result=source_case.expected_result,
            created_by=created_by,
            updated_by=created_by
        )

        return new_case

    @staticmethod
    @transaction.atomic
    def batch_copy_test_cases(ids, created_by, idempotency_key=None):
        """批量复制测试用例

        安全说明：
        1. 使用事务保证原子性，要么全部成功，要么全部失败
        2. 逐个检查用户对每个用例的权限
        3. 如果有任何权限检查失败，整个操作回滚
        4. 支持幂等性，防止重复提交

        Args:
            ids: 用例ID列表
            created_by: 创建者
            idempotency_key: 幂等键（可选，用于防止重复操作）
        """
        # 幂等性检查
        if idempotency_key:
            data_hash = IdempotencyService.generate_data_hash({'ids': sorted(ids)})
            cached_result, hit = IdempotencyService.check_and_set(
                'batch_copy', created_by.id, data_hash
            )
            if hit:
                logger.info(f"批量复制幂等键命中，返回缓存结果")
                return cached_result

        source_cases = TestCase.objects.filter(id__in=ids)
        copied_cases = []

        for source_case in source_cases:
            if not TestCaseService.check_version_permission(source_case.version, created_by, require_write=True):
                # 权限检查失败，抛出异常，触发事务回滚
                raise Exception(f'您没有权限复制用例 "{source_case.title}" (ID: {source_case.id})')

            new_case = TestCase.objects.create(
                title=f"{source_case.title} (复制)",
                module=source_case.module,
                version=source_case.version,
                priority=source_case.priority,
                estimated_hours=source_case.estimated_hours,
                tags=source_case.tags,
                automation_status=source_case.automation_status,
                automation_case_id=source_case.automation_case_id,
                requirement=source_case.requirement,
                precondition=source_case.precondition,
                steps=source_case.steps,
                expected_result=source_case.expected_result,
                created_by=created_by,
                updated_by=created_by
            )
            copied_cases.append(new_case)

        result = len(copied_cases)

        # 设置幂等结果
        if idempotency_key:
            IdempotencyService.set_result('batch_copy', created_by.id, data_hash, result)

        return result

    @staticmethod
    @transaction.atomic
    def batch_delete_test_cases(ids, user, idempotency_key=None):
        """批量删除测试用例

        安全说明：
        1. 使用事务保证原子性，要么全部成功，要么全部失败
        2. 逐个检查用户对每个用例的权限
        3. 如果有任何权限检查失败，整个操作回滚
        4. 支持幂等性，防止重复提交

        Args:
            ids: 用例ID列表
            user: 操作用户
            idempotency_key: 幂等键（可选）
        """
        # 幂等性检查
        if idempotency_key:
            data_hash = IdempotencyService.generate_data_hash({'ids': sorted(ids)})
            cached_result, hit = IdempotencyService.check_and_set(
                'batch_delete', user.id, data_hash
            )
            if hit:
                return cached_result

        cases = TestCase.objects.filter(id__in=ids)

        for case in cases:
            if not TestCaseService.check_version_permission(case.version, user, require_write=True):
                raise Exception(f'您没有权限删除用例 "{case.title}" (ID: {case.id})')

        # 权限检查全部通过，执行删除
        deleted_count = cases.count()
        cases.delete()

        # 设置幂等结果
        if idempotency_key:
            IdempotencyService.set_result('batch_delete', user.id, data_hash, deleted_count)

        return deleted_count

    @staticmethod
    @transaction.atomic
    def batch_move_test_cases(ids, target_module_id, user, idempotency_key=None):
        """批量移动测试用例

        安全说明：
        1. 使用事务保证原子性
        2. 支持幂等性

        Args:
            ids: 用例ID列表
            target_module_id: 目标模块ID
            user: 操作用户
            idempotency_key: 幂等键（可选）
        """
        from apps.testcase.models import TestModule

        # 幂等性检查
        if idempotency_key:
            data_hash = IdempotencyService.generate_data_hash({
                'ids': sorted(ids),
                'target_module': target_module_id
            })
            cached_result, hit = IdempotencyService.check_and_set(
                'batch_move', user.id, data_hash
            )
            if hit:
                return cached_result, None

        try:
            target_module = TestModule.objects.get(id=target_module_id)
        except TestModule.DoesNotExist:
            raise NotFoundError('目标模块不存在')

        if not TestCaseService.check_version_permission(target_module.version, user, require_write=True):
            raise BusinessError('您没有权限移动到目标模块')

        cases = TestCase.objects.filter(id__in=ids)

        for case in cases:
            if not TestCaseService.check_version_permission(case.version, user, require_write=True):
                raise Exception(f'您没有权限移动用例 "{case.title}" (ID: {case.id})')

        # 执行移动
        moved_count = cases.count()
        for case in cases:
            case.module = target_module
            case.version = target_module.version
            case.save()

        # 设置幂等结果
        if idempotency_key:
            IdempotencyService.set_result('batch_move', user.id, data_hash, moved_count)

        return moved_count, None

    @staticmethod
    @transaction.atomic
    def batch_update_test_cases(ids, update_fields, user, idempotency_key=None):
        """批量更新测试用例属性

        安全说明：
        1. 使用事务保证原子性
        2. 支持幂等性

        Args:
            ids: 用例ID列表
            update_fields: 更新字段
            user: 操作用户
            idempotency_key: 幂等键（可选）
        """
        allowed_fields = ['priority', 'automation_status', 'tags']

        fields_to_update = {}
        for field in allowed_fields:
            if field in update_fields:
                fields_to_update[field] = update_fields[field]

        if not fields_to_update:
            raise Exception('至少提供一个要更新的字段')

        # 幂等性检查
        if idempotency_key:
            data_hash = IdempotencyService.generate_data_hash({
                'ids': sorted(ids),
                'fields': fields_to_update
            })
            cached_result, hit = IdempotencyService.check_and_set(
                'batch_update', user.id, data_hash
            )
            if hit:
                return cached_result

        cases = TestCase.objects.filter(id__in=ids)

        for case in cases:
            if not TestCaseService.check_version_permission(case.version, user, require_write=True):
                raise Exception(f'您没有权限更新用例 "{case.title}" (ID: {case.id})')

        # 权限检查全部通过，执行更新
        updated_count = cases.count()
        for case in cases:
            for field, value in fields_to_update.items():
                setattr(case, field, value)
            case.save()

        # 设置幂等结果
        if idempotency_key:
            IdempotencyService.set_result('batch_update', user.id, data_hash, updated_count)

        return updated_count
