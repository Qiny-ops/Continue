"""
API测试权限服务

消除 apitest 视图中重复 4 次的权限过滤模式：
    ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
"""

from apps.projects.models import ProjectMember


class ApiTestPermissionService:
    """API测试模块的权限查询"""

    @staticmethod
    def get_user_project_ids(user):
        """获取用户有权限的项目 ID 集合（仅活跃成员）"""
        return set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )

    @staticmethod
    def user_is_project_member(user, project_id):
        """检查用户是否是项目成员（仅活跃成员）"""
        return ProjectMember.objects.filter(
            user=user, project_id=project_id, status='active'
        ).exists()
