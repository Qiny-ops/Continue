"""
需求业务逻辑层
"""
import logging
from typing import Tuple

from apps.core.base.service import BaseService
from apps.requirement.repositories.requirement_repository import RequirementRepository

logger = logging.getLogger(__name__)


class RequirementService(BaseService):
    repository = RequirementRepository

    @classmethod
    def get_requirements_by_version(cls, version_id, params=None):
        params = params or {}
        queryset = cls.repository.get_with_testcase_count(version_id)

        status = params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        module = params.get('module')
        if module:
            # 需求不再关联模块，忽略此筛选条件
            pass

        search = params.get('search')
        if search:
            queryset = (queryset.filter(title__icontains=search) |
                        queryset.filter(func_point__icontains=search))
            queryset = queryset.distinct()

        return cls.success(queryset)

    @classmethod
    def create_requirement(cls, data, user):
        try:
            requirement = cls.repository.create(
                created_by=user,
                updated_by=user,
                **data
            )
            return cls.success(requirement)
        except Exception as e:
            logger.error(f"创建需求失败: {e}")
            return cls.error(str(e))

    @classmethod
    def update_requirement(cls, requirement_id, data, user):
        try:
            requirement = cls.repository.get_by_id(requirement_id)
            if not requirement:
                return cls.error('需求不存在')

            # 版本归档时只读
            if requirement.is_readonly:
                return cls.error('该需求所属版本已归档，不可修改')

            data['updated_by'] = user
            cls.repository.update(requirement, **data)
            return cls.success(requirement)
        except Exception as e:
            logger.error(f"更新需求失败: {e}")
            return cls.error(str(e))

    @classmethod
    def delete_requirement(cls, requirement_id):
        try:
            requirement = cls.repository.get_by_id(requirement_id)
            if not requirement:
                return cls.error('需求不存在')

            # 版本归档时只读
            if requirement.is_readonly:
                return cls.error('该需求所属版本已归档，不可删除')

            # 关联测试用例预警：删除需求会将其关联用例的 requirement 置空，
            # 造成需求追溯链断裂，因此必须显式解除关联后才能删除
            related_cases = requirement.test_cases.count()
            if related_cases > 0:
                return cls.error(
                    f'该需求还关联 {related_cases} 个测试用例，请先解除关联后再删除'
                )

            cls.repository.delete(requirement)
            return cls.success(None)
        except Exception as e:
            logger.error(f"删除需求失败: {e}")
            return cls.error(str(e))

    @classmethod
    def batch_delete(cls, ids):
        try:
            # 过滤掉归档版本下的需求
            queryset = cls.repository.model.objects.filter(id__in=ids)
            readonly_ids = []
            for req in queryset.select_related('version'):
                if req.is_readonly:
                    readonly_ids.append(req.id)

            deletable_ids = set(ids) - set(readonly_ids)
            if not deletable_ids:
                return cls.error('选中的需求均属于已归档版本，不可删除')

            deleted_count, _ = cls.repository.model.objects.filter(id__in=deletable_ids).delete()
            result = {'deleted_count': deleted_count}
            if readonly_ids:
                result['readonly_skipped'] = len(readonly_ids)
            return cls.success(result)
        except Exception as e:
            logger.error(f"批量删除需求失败: {e}")
            return cls.error(str(e))

    @classmethod
    def save_extracted_requirements(cls, project_id, version_id, requirements_data,
                                    user=None, knowledge_base_id='', knowledge_id='', session_id=''):
        """保存AI提取的需求（去重），关联版本"""
        if not requirements_data:
            return cls.success([])

        created = []
        for item in requirements_data:
            module_name = item.get('模块', '') or item.get('module', '')
            func_point = item.get('功能点', '') or item.get('func_point', '')
            title = func_point or module_name

            if not title:
                continue

            # 去重：同版本同功能点不重复创建
            exists = cls.repository.model.objects.filter(
                version_id=version_id,
                func_point=func_point,
            ).exists()

            if not exists:
                requirement = cls.repository.create(
                    project_id=project_id,
                    version_id=version_id,
                    title=title,
                    func_point=func_point,
                    source='ai_extracted',
                    status='active',
                    knowledge_base_id=knowledge_base_id,
                    knowledge_id=knowledge_id,
                    session_id=session_id,
                    created_by=user,
                    updated_by=user,
                )
                created.append(requirement)

        logger.info(f"AI提取需求入库: 新增 {len(created)} 条, 跳过重复 {len(requirements_data) - len(created)} 条")
        return cls.success(created)
