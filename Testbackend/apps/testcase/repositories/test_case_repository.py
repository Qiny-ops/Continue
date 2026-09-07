"""
用例库、版本、模块、测试用例数据访问层
"""

from django.db.models import Count

from apps.core.base.repository import BaseRepository
from apps.testcase.models import (
    TestCaseRepository,
    TestCaseVersion,
    TestModule,
    TestCase
)


class RepositoryRepository(BaseRepository):
    """用例库数据访问层"""
    model = TestCaseRepository

    @classmethod
    def get_by_id(cls, repository_id):
        """根据ID获取用例库"""
        return TestCaseRepository.objects.filter(id=repository_id).select_related(
            'project', 'project__owner', 'created_by'
        ).first()

    @classmethod
    def get_by_project(cls, project):
        """获取项目的所有用例库"""
        return TestCaseRepository.objects.filter(project=project)

    @classmethod
    def get_user_accessible_repositories(cls, user):
        """获取用户有权限访问的用例库

        优化：预加载版本数据，避免 N+1 查询
        """
        from apps.projects.models import ProjectMember, Project

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )

        return TestCaseRepository.objects.filter(
            project_id__in=member_project_ids | owned_project_ids
        ).select_related(
            'project', 'project__owner', 'created_by'
        ).prefetch_related('versions')  # 预加载版本数据

    @classmethod
    def create_repository(cls, name, project, created_by, **extra_fields):
        """创建用例库"""
        return TestCaseRepository.objects.create(
            name=name,
            project=project,
            created_by=created_by,
            **extra_fields
        )

    @classmethod
    def update_repository(cls, repository, **kwargs):
        """更新用例库"""
        for attr, value in kwargs.items():
            setattr(repository, attr, value)
        repository.save()
        return repository


class VersionRepository(BaseRepository):
    """版本数据访问层"""
    model = TestCaseVersion

    @classmethod
    def get_by_id(cls, version_id):
        """根据ID获取版本"""
        return TestCaseVersion.objects.filter(id=version_id).select_related(
            'repository', 'repository__project', 'created_by'
        ).first()

    @classmethod
    def get_by_repository(cls, repository):
        """获取用例库下的版本列表"""
        return TestCaseVersion.objects.filter(repository=repository)

    @classmethod
    def get_by_project(cls, project_id):
        """获取项目下的版本列表"""
        return TestCaseVersion.objects.filter(repository__project_id=project_id).select_related(
            'repository', 'created_by'
        )

    @classmethod
    def get_default_version(cls, repository):
        """获取默认版本"""
        return TestCaseVersion.objects.filter(
            repository=repository, is_default=True
        ).first()

    @classmethod
    def get_default_version_by_project(cls, project_id):
        """获取项目下的默认版本"""
        return TestCaseVersion.objects.filter(
            repository__project_id=project_id, is_default=True
        ).first()

    @classmethod
    def create_version(cls, name, repository, created_by=None, **extra_fields):
        """创建版本"""
        return TestCaseVersion.objects.create(
            name=name,
            repository=repository,
            created_by=created_by,
            **extra_fields
        )

    @classmethod
    def set_default(cls, version):
        """设置默认版本"""
        TestCaseVersion.objects.filter(repository=version.repository).update(is_default=False)
        version.is_default = True
        version.save()


class ModuleRepository(BaseRepository):
    """模块数据访问层"""
    model = TestModule

    @classmethod
    def get_by_id(cls, module_id):
        """根据ID获取模块"""
        return TestModule.objects.filter(id=module_id).first()

    @classmethod
    def get_by_version(cls, version_id):
        """获取版本的所有模块"""
        return TestModule.objects.filter(version_id=version_id).select_related('parent')

    @classmethod
    def get_tree(cls, version_id):
        """获取模块树结构"""
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
    def get_all_descendant_ids(cls, module_id, version_id):
        """获取模块及其所有子模块的ID列表"""
        # 确保 module_id 是整数类型
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
    def create_module(cls, name, version, parent=None, sort_order=0):
        """创建模块"""
        return TestModule.objects.create(
            name=name,
            version=version,
            parent=parent,
            sort_order=sort_order
        )

    @classmethod
    def update_module(cls, module, **kwargs):
        """更新模块"""
        for attr, value in kwargs.items():
            setattr(module, attr, value)
        module.save()
        return module

    @classmethod
    def delete_module(cls, module):
        """删除模块"""
        module.delete()


class TestCaseDataRepository(BaseRepository):
    """测试用例数据访问层"""
    model = TestCase

    @classmethod
    def get_base_queryset(cls):
        """获取基础查询集"""
        return TestCase.objects.select_related(
            'version', 'version__repository', 'version__repository__project',
            'module', 'created_by', 'updated_by'
        )

    @classmethod
    def get_by_id(cls, case_id):
        """根据ID获取测试用例"""
        return cls.get_base_queryset().filter(id=case_id).first()

    @classmethod
    def get_by_version(cls, version_id):
        """获取版本的所有测试用例"""
        return cls.get_base_queryset().filter(version_id=version_id)

    @classmethod
    def get_by_module(cls, module_id):
        """获取模块的测试用例"""
        return cls.get_base_queryset().filter(module_id=module_id)

    @classmethod
    def get_by_module_tree(cls, module_id, version_id):
        """获取模块及其子模块的所有测试用例"""
        module_ids = ModuleRepository.get_all_descendant_ids(module_id, version_id)
        return cls.get_base_queryset().filter(module_id__in=module_ids)

    @classmethod
    def get_user_accessible_cases(cls, user):
        """获取用户有权限访问的测试用例"""
        from apps.projects.models import ProjectMember, Project

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )

        return cls.get_base_queryset().filter(
            version__repository__project_id__in=member_project_ids | owned_project_ids
        ).distinct()

    @classmethod
    def create_case(cls, data, user):
        """创建测试用例"""
        test_case = TestCase.objects.create(**data, created_by=user, updated_by=user)
        return test_case

    @classmethod
    def update_case(cls, test_case, data, user):
        """更新测试用例"""
        for attr, value in data.items():
            setattr(test_case, attr, value)
        test_case.updated_by = user
        test_case.save()
        return test_case

    @classmethod
    def copy_case(cls, source_case, user):
        """复制测试用例"""
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
            created_by=user,
            updated_by=user
        )
        return new_case

    @classmethod
    def get_case_counts_by_modules(cls, module_ids):
        """获取模块的用例数量"""
        return dict(
            TestCase.objects.filter(module_id__in=module_ids)
            .values_list('module_id')
            .annotate(count=Count('id'))
        )

    @classmethod
    def bulk_create(cls, cases_data: list) -> list:
        """
        批量创建测试用例

        Args:
            cases_data: 用例数据列表，每个元素为字典

        Returns:
            创建的测试用例列表
        """
        cases = [TestCase(**data) for data in cases_data]
        return TestCase.objects.bulk_create(cases)

    @classmethod
    def create_ai_generated_case(cls, data: dict, user) -> TestCase:
        """
        创建AI生成的测试用例

        Args:
            data: 用例数据
            user: 创建用户

        Returns:
            创建的测试用例
        """
        return TestCase.objects.create(
            **data,
            generation_source='ai_generated',
            review_status='pending',
            created_by=user,
            updated_by=user
        )

    @classmethod
    def bulk_create_ai_cases(cls, cases_data: list, user) -> list:
        """
        批量创建AI生成的测试用例

        Args:
            cases_data: 用例数据列表
            user: 创建用户

        Returns:
            创建的测试用例列表
        """
        cases = []
        for data in cases_data:
            case = TestCase(
                **data,
                generation_source='ai_generated',
                review_status='pending',
                created_by=user,
                updated_by=user
            )
            cases.append(case)
        return TestCase.objects.bulk_create(cases)
