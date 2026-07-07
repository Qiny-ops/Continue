"""
用例库服务层
"""

import logging
from django.db import transaction
from apps.core.permissions import is_system_admin
from apps.core.exceptions import ValidationError, BusinessError
from apps.testcase.repositories import RepositoryRepository
from apps.testcase.models import TestCaseRepository, TestCaseVersion, TestModule, TestCase

logger = logging.getLogger(__name__)


class RepositoryService:
    """用例库服务"""

    @staticmethod
    def get_all_repositories():
        """获取所有用例库（管理员用）

        优化：预加载版本数据，避免 N+1 查询
        """
        return TestCaseRepository.objects.all().select_related(
            'project', 'created_by'
        ).prefetch_related('versions')

    @staticmethod
    def check_project_permission(project_id, user, require_write=False):
        """检查用户对项目的权限"""
        from apps.projects.repositories import ProjectMemberRepository

        if is_system_admin(user):
            return True

        is_member, role, _ = ProjectMemberRepository.is_project_member(project_id, user)
        if not is_member:
            return False

        if require_write:
            return role in ['owner', 'admin', 'developer']
        return True

    @staticmethod
    def get_repositories_by_project(project_id):
        """获取项目下的用例库列表"""
        return TestCaseRepository.objects.filter(project_id=project_id)

    @staticmethod
    def get_user_accessible_repositories(user):
        """获取用户有权限访问的用例库"""
        return RepositoryRepository.get_user_accessible_repositories(user)

    @staticmethod
    def create_repository(name, project, description='', is_default=False, created_by=None):
        """创建用例库

        业务逻辑：
        1. 用例库必须关联项目
        2. 用户必须有项目的写入权限
        """
        if not project:
            raise ValidationError('用例库必须关联项目')

        if created_by:
            if not RepositoryService.check_project_permission(project.id, created_by, require_write=True):
                raise BusinessError('您没有权限在该项目中创建用例库')

        return TestCaseRepository.objects.create(
            name=name,
            project=project,
            description=description,
            is_default=is_default,
            created_by=created_by
        )

    @staticmethod
    def get_repository_stats(repository_id):
        """获取用例库统计信息

        返回：版本数、模块数、用例数
        """
        versions_count = TestCaseVersion.objects.filter(repository_id=repository_id).count()
        modules_count = TestModule.objects.filter(
            version__repository_id=repository_id
        ).count()
        cases_count = TestCase.objects.filter(
            version__repository_id=repository_id
        ).count()

        return {
            'versions_count': versions_count,
            'modules_count': modules_count,
            'cases_count': cases_count
        }

    @staticmethod
    def check_can_delete(repository_id, user):
        """检查用例库是否可以删除

        业务逻辑：
        1. 用户必须有项目写入权限
        2. 返回关联数据统计，供前端确认

        Returns:
            can_delete: 是否可以删除
            stats: 关联数据统计
            error: 错误信息
        """
        try:
            repository = TestCaseRepository.objects.get(id=repository_id)
        except TestCaseRepository.DoesNotExist:
            return False, None, '用例库不存在'

        # 检查权限
        if not RepositoryService.check_project_permission(
            repository.project_id, user, require_write=True
        ):
            return False, None, '您没有权限删除该用例库'

        # 获取关联数据统计
        stats = RepositoryService.get_repository_stats(repository_id)

        return True, stats, None

    @staticmethod
    @transaction.atomic
    def delete_repository(repository_id, user, force=False):
        """删除用例库

        业务逻辑：
        1. 检查权限
        2. 检查关联数据，如果有关联数据需要用户确认
        3. 级联删除所有关联数据

        Args:
            repository_id: 用例库ID
            user: 操作用户
            force: 是否强制删除（跳过确认）

        Returns:
            deleted_stats: 删除的统计数据
            error: 错误信息
        """
        can_delete, stats, error = RepositoryService.check_can_delete(repository_id, user)
        if not can_delete:
            return None, error

        # 如果有关联数据且未确认，返回统计信息让用户确认
        if not force and (stats['versions_count'] > 0 or stats['cases_count'] > 0):
            return {
                'need_confirm': True,
                'stats': stats,
                'message': f"该用例库包含 {stats['versions_count']} 个版本、{stats['modules_count']} 个模块、{stats['cases_count']} 个测试用例，删除后将无法恢复。请确认是否继续删除？"
            }, None

        # 执行删除（Django 会自动级联删除）
        repository = TestCaseRepository.objects.get(id=repository_id)
        repository_name = repository.name
        repository.delete()

        logger.info(f"用户 {user.username} 删除了用例库 {repository_name}，删除统计: {stats}")

        return {
            'need_confirm': False,
            'stats': stats,
            'message': f"成功删除用例库 {repository_name}"
        }, None