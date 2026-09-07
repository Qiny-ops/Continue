"""
需求数据访问层
"""
from django.db.models import Count

from apps.core.base.repository import BaseRepository
from apps.requirement.models import Requirement


class RequirementRepository(BaseRepository):
    model = Requirement

    @classmethod
    def get_by_project(cls, project_id):
        return Requirement.objects.filter(project_id=project_id).select_related(
            'project', 'version', 'created_by', 'updated_by'
        )

    @classmethod
    def get_by_version(cls, version_id):
        return Requirement.objects.filter(version_id=version_id).select_related(
            'version', 'created_by', 'updated_by'
        )

    @classmethod
    def get_by_status(cls, project_id, status):
        return Requirement.objects.filter(project_id=project_id, status=status)

    @classmethod
    def get_with_testcase_count(cls, version_id):
        return Requirement.objects.filter(
            version_id=version_id
        ).select_related(
            'version', 'created_by', 'updated_by'
        ).annotate(
            testcase_count=Count('test_cases')
        )

    @classmethod
    def get_module_statistics(cls, version_id):
        """获取版本下各功能点的需求统计"""
        from django.db.models import Q
        return list(
            Requirement.objects.filter(version_id=version_id)
            .values('func_point')
            .annotate(count=Count('id'))
            .exclude(Q(func_point=''))
            .order_by('func_point')
        )

    @classmethod
    def bulk_create_requirements(cls, requirements_data):
        objs = [Requirement(**data) for data in requirements_data]
        return Requirement.objects.bulk_create(objs)

    @classmethod
    def get_by_ids(cls, ids):
        return Requirement.objects.filter(id__in=ids)
