"""
版本服务层
"""

import logging
from django.db import transaction
from django.db.models import F
from apps.testcase.repositories import VersionRepository
from apps.testcase.models import TestCaseVersion
from apps.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class VersionService:
    """版本服务"""

    @staticmethod
    def get_all_versions():
        """获取所有版本"""
        return TestCaseVersion.objects.all().select_related('repository', 'repository__project', 'created_by')

    @staticmethod
    @transaction.atomic
    def create_version(name, repository_id, created_by=None, description='', is_default=False, status='active'):
        """创建版本

        业务逻辑：
        1. 校验用例库存在
        2. 版本归属用例库
        3. 若设为默认，先取消同用例库下其他默认版本，保证唯一默认
        """
        from apps.testcase.models import TestCaseRepository

        try:
            repository = TestCaseRepository.objects.get(id=repository_id)
        except TestCaseRepository.DoesNotExist:
            raise NotFoundError('用例库不存在')

        # 设为默认时，先取消同用例库其他默认版本
        if is_default:
            TestCaseVersion.objects.filter(
                repository=repository, is_default=True
            ).update(is_default=False)

        version = TestCaseVersion.objects.create(
            repository=repository,
            name=name,
            description=description,
            status=status,
            is_default=is_default,
            created_by=created_by,
        )

        logger.info(f"版本 {version.name} 已创建（用例库: {repository.name}）")
        return version

    @staticmethod
    def get_versions_by_repository(repository_id):
        """获取用例库下的版本列表"""
        return TestCaseVersion.objects.filter(repository_id=repository_id)

    @staticmethod
    def get_versions_by_project(project_id):
        """获取项目下的版本列表"""
        return TestCaseVersion.objects.filter(repository__project_id=project_id).select_related(
            'repository', 'created_by'
        )

    @staticmethod
    @transaction.atomic
    def set_default(version_id):
        """设置默认版本

        业务逻辑：
        1. 使用事务保证原子性
        2. 先将同用例库所有版本的 is_default 设为 False
        3. 再将目标版本设为默认
        4. 使用 select_for_update 锁定记录，防止并发问题
        """
        try:
            # 使用 select_for_update 锁定版本记录，防止并发
            version = TestCaseVersion.objects.select_for_update().get(id=version_id)
        except TestCaseVersion.DoesNotExist:
            raise NotFoundError('版本不存在')

        # 锁定同用例库的所有版本并更新
        TestCaseVersion.objects.select_for_update().filter(
            repository=version.repository
        ).update(is_default=False)

        # 设置当前版本为默认
        version.is_default = True
        version.save()

        logger.info(f"版本 {version.name} (ID: {version_id}) 已设置为默认版本")
        return version, None
