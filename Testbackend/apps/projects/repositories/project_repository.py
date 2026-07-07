"""
项目数据访问层
"""

from django.db import models
from django.db.models import Count, Q
from apps.projects.models import Project, ProjectMember, ProjectRole


class ProjectRepository:
    """项目数据访问层"""

    @staticmethod
    def get_by_id(project_id):
        """根据ID获取项目"""
        return Project.objects.filter(id=project_id).select_related('owner').first()

    @staticmethod
    def get_by_identifier(identifier):
        """根据标识符获取项目

        业务逻辑：
        1. 如果 identifier 是纯数字，按 ID 查找
        2. 否则按 code 字段查找（不区分大小写）
        3. 优先使用 code 查找，因为 code 是业务标识符
        """
        # 先尝试按 code 查找（业务标识符）
        project = Project.objects.filter(code__iexact=identifier).select_related('owner').first()
        if project:
            return project

        # 如果是数字，再尝试按 ID 查找
        if identifier.isdigit():
            return Project.objects.filter(id=int(identifier)).select_related('owner').first()

        return None

    @staticmethod
    def get_by_code(code):
        """根据code获取项目"""
        return Project.objects.filter(code__iexact=code).first()

    @staticmethod
    def get_user_projects(user):
        """获取用户有权限的项目ID集合

        业务逻辑：只返回用户作为活跃成员或所有者的项目
        """
        # 只统计活跃状态的成员
        member_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )
        return member_ids | owned_ids

    @staticmethod
    def get_projects_by_ids(project_ids):
        """根据ID列表获取项目"""
        return Project.objects.filter(id__in=project_ids).select_related('owner')

    @staticmethod
    def create_project(name, code, owner, **extra_fields):
        """创建项目"""
        return Project.objects.create(
            name=name,
            code=code,
            owner=owner,
            **extra_fields
        )

    @staticmethod
    def update_project(project, **kwargs):
        """更新项目"""
        for attr, value in kwargs.items():
            setattr(project, attr, value)
        project.save()
        return project

    @staticmethod
    def delete_project(project):
        """删除项目"""
        project.delete()

    @staticmethod
    def exists_by_code(code):
        """检查项目code是否存在"""
        return Project.objects.filter(code__iexact=code).exists()

    @staticmethod
    def get_project_stats(project_ids):
        """获取项目统计信息"""
        queryset = Project.objects.filter(id__in=project_ids)

        status_stats = queryset.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status='pending')),
            archived=Count('id', filter=Q(status='archived'))
        )

        type_stats = dict(
            queryset.values('type')
            .annotate(count=Count('id'))
            .values_list('type', 'count')
        )

        return {
            'total': status_stats['total'],
            'active': status_stats['active'],
            'completed': status_stats['completed'],
            'pending': status_stats['pending'],
            'archived': status_stats['archived'],
            'by_type': type_stats
        }


class ProjectMemberRepository:
    """项目成员数据访问层"""

    @staticmethod
    def get_member(project, user):
        """获取项目成员关系"""
        return ProjectMember.objects.filter(
            project=project, user=user
        ).select_related('user', 'user__system_role').first()

    @staticmethod
    def get_project_members(project):
        """获取项目所有成员"""
        return ProjectMember.objects.filter(
            project=project
        ).select_related('user', 'user__system_role')

    @staticmethod
    def get_user_favorite_projects(user):
        """获取用户收藏的项目成员关系"""
        return ProjectMember.objects.filter(
            user=user, is_favorite=True
        ).select_related('project', 'project__owner')

    @staticmethod
    def get_user_member_projects(user):
        """获取用户作为成员的项目关系"""
        return ProjectMember.objects.filter(user=user)

    @staticmethod
    def add_member(project, user, role='viewer', status='active'):
        """添加项目成员"""
        return ProjectMember.objects.create(
            project=project,
            user=user,
            role=role,
            status=status
        )

    @staticmethod
    def update_member(member, **kwargs):
        """更新成员信息"""
        for attr, value in kwargs.items():
            setattr(member, attr, value)
        member.save()
        return member

    @staticmethod
    def remove_member(member):
        """移除成员"""
        member.delete()

    @staticmethod
    def is_project_member(project_id, user):
        """检查用户是否是项目成员"""
        project = Project.objects.select_related('owner').filter(id=project_id).first()
        if not project:
            return False, None, None

        if project.owner and project.owner.id == user.id:
            return True, 'owner', project

        member = ProjectMember.objects.filter(
            project_id=project_id,
            user=user,
            status='active'
        ).first()

        if member:
            return True, member.role, project

        return False, None, project

    @staticmethod
    def get_member_role_counts(project):
        """获取项目各角色的成员数量"""
        return dict(
            ProjectMember.objects.filter(project=project)
            .values('role')
            .annotate(count=Count('id'))
            .values_list('role', 'count')
        )

    @staticmethod
    def batch_update_members(project, member_ids, **kwargs):
        """批量更新成员"""
        return ProjectMember.objects.filter(
            id__in=member_ids, project=project
        ).update(**kwargs)


class ProjectRoleRepository:
    """项目角色权限数据访问层"""

    @staticmethod
    def get_project_roles(project):
        """获取项目的角色权限配置"""
        return dict(
            ProjectRole.objects.filter(project=project)
            .values_list('role_key', 'permissions')
        )

    @staticmethod
    def update_role_permissions(project, role_key, permissions):
        """更新角色权限"""
        return ProjectRole.objects.update_or_create(
            project=project,
            role_key=role_key,
            defaults={'permissions': permissions}
        )

    @staticmethod
    def create_default_roles(project, get_default_permissions_func):
        """创建默认角色权限配置"""
        for role_key in ['admin', 'developer', 'tester', 'viewer']:
            ProjectRole.objects.create(
                project=project,
                role_key=role_key,
                permissions=get_default_permissions_func(role_key)
            )
