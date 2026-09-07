"""
模块服务层
"""

import logging
from django.db.models import Count
from django.db import transaction
from apps.testcase.repositories import ModuleRepository
from apps.testcase.models import TestModule, TestCase, TestCaseVersion

logger = logging.getLogger(__name__)


class ModuleService:
    """模块服务"""

    @staticmethod
    def get_all_modules():
        """获取所有模块"""
        return TestModule.objects.all()

    @staticmethod
    def get_modules_with_relations():
        """获取带关联关系的模块列表"""
        return TestModule.objects.all().select_related('parent').prefetch_related('children')

    @staticmethod
    def get_module_by_id(module_id):
        """根据ID获取模块"""
        return TestModule.objects.filter(id=module_id).first()

    @staticmethod
    def get_modules_by_version(version_id):
        """获取版本下的模块列表"""
        return TestModule.objects.filter(version_id=version_id).select_related('parent')

    @staticmethod
    def build_tree(modules):
        """构建模块树形结构

        为所有模块设置 _children_list（即使为空），
        避免序列化器回退到 DB 查询（N+1 问题）。
        """
        module_dict = {m.id: m for m in modules}
        root_modules = []

        # 确保所有模块都有 _children_list
        for module in modules:
            if not hasattr(module, '_children_list'):
                module._children_list = []

        for module in modules:
            if module.parent_id is None:
                root_modules.append(module)
            else:
                parent = module_dict.get(module.parent_id)
                if parent:
                    parent._children_list.append(module)

        return root_modules

    @staticmethod
    def get_all_descendant_ids(module_id, version_id):
        """获取模块及其所有子模块的ID列表"""
        module_ids = [module_id]

        all_modules = list(TestModule.objects.filter(
            version_id=version_id
        ).values_list('id', 'parent_id'))

        children_map = {}
        for mid, parent_id in all_modules:
            if parent_id:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(mid)

        def collect_children(pid):
            children = children_map.get(pid, [])
            for child_id in children:
                module_ids.append(child_id)
                collect_children(child_id)

        collect_children(module_id)
        return module_ids

    @staticmethod
    def get_module_statistics(version_id, stat_type='testcase'):
        """获取模块统计信息

        Args:
            version_id: 版本ID
            stat_type: 统计类型，testcase=用例数，requirement=需求数
        """
        modules = list(TestModule.objects.filter(
            version_id=version_id
        ).values('id', 'parent_id'))

        if stat_type == 'requirement':
            from apps.requirement.models import Requirement
            # 需求不再关联模块，按版本统计总数
            total_count = Requirement.objects.filter(
                version_id=version_id
            ).count()
            # 为每个模块返回0（需求不再按模块分组）
            item_counts = {m['id']: 0 for m in modules}
        else:
            item_counts = dict(
                TestCase.objects.filter(
                    module_id__in=[m['id'] for m in modules]
                ).values_list('module_id').annotate(count=Count('id'))
            )

        children_map = {}
        for m in modules:
            pid = m['parent_id']
            if pid:
                if pid not in children_map:
                    children_map[pid] = []
                children_map[pid].append(m['id'])

        def get_total_count(module_id):
            direct_count = item_counts.get(module_id, 0)
            children = children_map.get(module_id, [])
            for child_id in children:
                direct_count += get_total_count(child_id)
            return direct_count

        statistics = {}
        for m in modules:
            statistics[m['id']] = {
                'id': m['id'],
                'count': get_total_count(m['id']),
                'direct_count': item_counts.get(m['id'], 0)
            }

        return statistics

    @staticmethod
    def get_module_case_count(module_id, version_id):
        """获取模块及其子模块下的用例数量"""
        module_ids = ModuleService.get_all_descendant_ids(module_id, version_id)
        return TestCase.objects.filter(module_id__in=module_ids).count()

    @staticmethod
    @transaction.atomic
    def batch_delete_modules(module_ids, version_id, delete_cases=False):
        """
        批量删除模块及其子模块

        业务逻辑：
        1. 收集所有要删除的模块ID（包括子模块）
        2. 检查模块下是否有测试用例
        3. 如果有用例且 delete_cases=False，返回错误信息
        4. 如果有用例且 delete_cases=True，同时删除用例

        Args:
            module_ids: 要删除的模块ID列表
            version_id: 版本ID
            delete_cases: 是否同时删除模块下的测试用例

        Returns:
            deleted_modules_count: 删除的模块数量
            deleted_cases_count: 删除的用例数量
            error: 错误信息（如果有）
        """
        # 归档版本冻结：模块与用例已冻结，禁止删除
        version = TestCaseVersion.objects.filter(id=version_id).first()
        if version and version.status == 'archived':
            return 0, 0, '该版本已归档，模块和测试用例已冻结，不可删除'

        # 收集所有要删除的模块ID（包括子模块）
        all_ids_to_delete = []
        for module_id in module_ids:
            descendant_ids = ModuleService.get_all_descendant_ids(module_id, version_id)
            all_ids_to_delete.extend(descendant_ids)

        all_ids_to_delete = list(set(all_ids_to_delete))

        # 检查这些模块下是否有测试用例
        case_count = TestCase.objects.filter(module_id__in=all_ids_to_delete).count()

        if case_count > 0 and not delete_cases:
            return 0, 0, f'这些模块下共有 {case_count} 个测试用例，请先移动或删除这些用例后再删除模块，或者确认同时删除用例'

        # 删除测试用例（如果需要）
        deleted_cases_count = 0
        if case_count > 0 and delete_cases:
            deleted_cases_count, _ = TestCase.objects.filter(module_id__in=all_ids_to_delete).delete()

        # 删除模块
        deleted_modules_count, _ = TestModule.objects.filter(
            id__in=all_ids_to_delete
        ).delete()

        return deleted_modules_count, deleted_cases_count, None
