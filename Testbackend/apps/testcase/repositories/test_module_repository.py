"""
测试模块数据访问层

负责测试模块的CRUD操作。
"""
from typing import Optional, List, Dict
from django.db.models import Count

from apps.core.base.repository import BaseRepository
from apps.testcase.models import TestModule


class TestModuleRepository(BaseRepository):
    """测试模块数据访问层"""
    model = TestModule

    @classmethod
    def get_by_id(cls, module_id: int) -> Optional[TestModule]:
        """根据ID获取模块"""
        return TestModule.objects.filter(id=module_id).first()

    @classmethod
    def get_by_version(cls, version_id: int):
        """获取版本的所有模块"""
        return TestModule.objects.filter(version_id=version_id).select_related('parent').order_by('sort_order')

    @classmethod
    def get_or_create(
        cls,
        version_id: int,
        name: str,
        defaults: Optional[Dict] = None
    ) -> TestModule:
        """
        获取或创建模块

        Args:
            version_id: 版本ID
            name: 模块名称
            defaults: 创建时的默认值

        Returns:
            TestModule: 模块实例
        """
        defaults = defaults or {'sort_order': 0}
        module, _ = TestModule.objects.get_or_create(
            version_id=version_id,
            name=name,
            defaults=defaults
        )
        return module

    @classmethod
    def create_module(
        cls,
        name: str,
        version_id: int,
        parent_id: Optional[int] = None,
        sort_order: int = 0
    ) -> TestModule:
        """创建模块"""
        return TestModule.objects.create(
            name=name,
            version_id=version_id,
            parent_id=parent_id,
            sort_order=sort_order
        )

    @classmethod
    def update_module(cls, module: TestModule, **kwargs) -> TestModule:
        """更新模块"""
        for attr, value in kwargs.items():
            setattr(module, attr, value)
        module.save()
        return module

    @classmethod
    def delete_module(cls, module: TestModule) -> bool:
        """删除模块"""
        module.delete()
        return True

    @classmethod
    def get_tree(cls, version_id: int) -> List[Dict]:
        """
        获取模块树结构

        Args:
            version_id: 版本ID

        Returns:
            模块树列表
        """
        modules = list(TestModule.objects.filter(
            version_id=version_id
        ).values('id', 'name', 'parent_id', 'sort_order'))

        children_map = {}
        root_modules = []

        for m in modules:
            m['children'] = []
            if m['parent_id']:
                if m['parent_id'] not in children_map:
                    children_map[m['parent_id']] = []
                children_map[m['parent_id']].append(m)
            else:
                root_modules.append(m)

        def add_children(module):
            module['children'] = children_map.get(module['id'], [])
            for child in module['children']:
                add_children(child)
            return module

        return [add_children(m) for m in root_modules]

    @classmethod
    def get_all_descendant_ids(cls, module_id: int, version_id: int) -> List[int]:
        """
        获取模块及其所有子模块的ID列表

        Args:
            module_id: 模块ID
            version_id: 版本ID

        Returns:
            ID列表
        """
        module_id = int(module_id) if module_id else None
        version_id = int(version_id) if version_id else None

        modules = list(TestModule.objects.filter(
            version_id=version_id
        ).values_list('id', 'parent_id'))

        children_map = {}
        for mid, parent_id in modules:
            if parent_id:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(mid)

        module_ids = [module_id]

        def collect_children(pid):
            for child_id in children_map.get(pid, []):
                module_ids.append(child_id)
                collect_children(child_id)

        collect_children(module_id)
        return module_ids

    @classmethod
    def bulk_create(cls, modules_data: List[Dict]) -> List[TestModule]:
        """
        批量创建模块

        Args:
            modules_data: 模块数据列表

        Returns:
            创建的模块列表
        """
        modules = [TestModule(**data) for data in modules_data]
        return TestModule.objects.bulk_create(modules)
