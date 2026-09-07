"""
统一权限服务模块

提供系统级权限和项目级权限的统一管理。
所有权限检查逻辑集中在此模块，避免分散在各个视图文件中。
"""

import logging

from rest_framework.permissions import BasePermission

from apps.projects.models import Project, ProjectMember

logger = logging.getLogger(__name__)


class IsInternalServiceOrAuthenticated(BasePermission):
    """允许已认证用户，或携带有效内部服务 API Key 的请求。

    用于微服务之间互相调用的端点（如清理测试账号），关闭「匿名即可访问」
    的漏洞，同时保留内部服务用 X-Internal-API-Key 调用的能力。
    """

    def has_permission(self, request, view):
        if bool(request.user and request.user.is_authenticated):
            return True
        # InternalServiceAuthentication 校验成功时 request.auth == 'internal'
        return request.auth == 'internal'


# ==================== 系统权限 ====================

def is_system_admin(user):
    """
    检查用户是否是系统管理员

    Args:
        user: 用户对象

    Returns:
        bool: 是否是系统管理员
    """
    if not user or not user.system_role:
        return False
    return user.system_role.code == 'admin'


def get_all_permissions():
    """
    获取所有权限列表

    Returns:
        list: 权限列表，每项包含 key, name, group
    """
    permissions = []
    for code, name in PROJECT_PERMISSIONS.items():
        # 根据权限代码确定分组（按顺序匹配，避免 test_execute 被 testcase 匹配）
        if 'apitest' in code:
            group = 'apitest'
        elif 'knowledge' in code:
            group = 'knowledge'
        elif 'testcase' in code:
            group = 'testcase'
        elif 'test_execute' in code:
            group = 'testcase'
        elif 'member' in code:
            group = 'member'
        elif 'report' in code:
            group = 'report'
        elif 'project' in code or 'settings' in code:
            group = 'project'
        else:
            group = 'other'
        permissions.append({'key': code, 'name': name, 'group': group})
    return permissions


def get_permission_groups():
    """
    获取权限分组列表

    Returns:
        list: 分组列表，每项包含 key, name
    """
    group_names = {
        'project': '项目管理',
        'member': '成员管理',
        'testcase': '测试用例',
        'apitest': '接口测试',
        'knowledge': '知识库',
        'report': '报告中心',
    }
    return [{'key': g, 'name': n} for g, n in group_names.items()]


def get_default_permissions(role_key):
    """
    获取角色的默认权限列表

    Args:
        role_key: 角色标识 (admin/developer/tester/viewer)

    Returns:
        list: 权限代码列表
    """
    # admin 拥有所有项目权限
    admin_permissions = list(PROJECT_PERMISSIONS.keys())

    default_permissions = {
        'admin': admin_permissions,
        'developer': [
            'testcase_view', 'apitest_view', 'apitest_execute',
            'knowledge_view', 'report_view'
        ],
        'tester': [
            'testcase_manage', 'testcase_view', 'test_execute',
            'apitest_execute', 'knowledge_view', 'report_view'
        ],
        'viewer': [
            'testcase_view', 'knowledge_view', 'report_view'
        ]
    }
    return default_permissions.get(role_key, [])


# ==================== 系统权限常量 ====================

SYSTEM_PERMISSIONS = {
    # 系统管理
    'system_admin': '系统管理',
    'system_settings': '系统设置',

    # 用户管理
    'user_manage': '用户管理',
    'user_view': '用户查看',
    'role_manage': '角色管理',
    'role_view': '角色查看',

    # 项目管理
    'project_create': '创建项目',
    'project_view_all': '查看所有项目',
    'project_delete_any': '删除任意项目',

    # 报表统计
    'report_global': '全局报表',
    'report_export': '报表导出',
}

# 系统管理员默认拥有所有系统权限
ADMIN_SYSTEM_PERMISSIONS = list(SYSTEM_PERMISSIONS.keys())

# 普通用户默认权限
DEFAULT_USER_SYSTEM_PERMISSIONS = ['project_create']

# 系统角色默认权限映射
SYSTEM_ROLE_DEFAULTS = {
    'admin': ADMIN_SYSTEM_PERMISSIONS,
    'user': DEFAULT_USER_SYSTEM_PERMISSIONS,
}


# ==================== 项目权限常量 ====================

# 项目权限代码 - 根据实际功能模块定义
PROJECT_PERMISSIONS = {
    'project_manage': '项目管理',
    'member_manage': '成员管理',
    'testcase_manage': '测试用例管理',
    'testcase_view': '测试用例查看',
    'apitest_manage': '接口测试管理',
    'apitest_view': '接口测试查看',
    'apitest_execute': '接口测试执行',
    'knowledge_manage': '知识库管理',
    'knowledge_view': '知识库查看',
    'test_execute': '测试执行',
    'report_view': '报告查看',
    'settings_manage': '设置管理',
}


# ==================== 项目权限服务 ====================

class ProjectPermissionService:
    """
    项目权限服务

    提供项目级别的权限检查功能，包括成员检查、管理员检查、写权限检查等。
    所有项目相关的权限检查应通过此类进行。
    """

    @staticmethod
    def check_member(project_id, user):
        """
        检查用户是否是项目成员

        Args:
            project_id: 项目ID
            user: 用户对象

        Returns:
            tuple: (is_member, role, project)
                - is_member: 是否是成员
                - role: 角色标识 (owner/admin/developer/tester/viewer)
                - project: 项目对象
        """
        try:
            project = Project.objects.select_related('owner').get(id=project_id)
        except Project.DoesNotExist:
            return False, None, None

        # 项目所有者拥有最高权限
        if project.owner and project.owner.id == user.id:
            return True, 'owner', project

        # 检查成员关系
        member = ProjectMember.objects.filter(
            project_id=project_id,
            user=user,
            status='active'
        ).first()

        if member:
            return True, member.role, project

        return False, None, project

    @staticmethod
    def check_admin(project_id, user):
        """
        检查用户是否是项目管理员

        Args:
            project_id: 项目ID
            user: 用户对象

        Returns:
            tuple: (is_admin, project)
        """
        is_member, role, project = ProjectPermissionService.check_member(project_id, user)
        if not project:
            return False, None
        if role in ['owner', 'admin']:
            return True, project
        return False, project

    @staticmethod
    def check_write_permission(project_id, user):
        """
        检查用户是否有项目的写权限

        写权限角色: owner, admin, developer, tester

        Args:
            project_id: 项目ID
            user: 用户对象

        Returns:
            tuple: (has_permission, project)
        """
        is_member, role, project = ProjectPermissionService.check_member(project_id, user)
        if not project:
            return False, None
        if role in ['owner', 'admin', 'developer', 'tester']:
            return True, project
        return False, project

    @staticmethod
    def check_testcase_permission(project_id, user, require_write=False):
        """
        检查用户是否有测试用例相关权限

        Args:
            project_id: 项目ID
            user: 用户对象
            require_write: 是否需要写权限

        Returns:
            tuple: (has_permission, project)
        """
        is_member, role, project = ProjectPermissionService.check_member(project_id, user)
        if not project:
            return False, None

        if require_write:
            # 写权限: owner, admin, developer, tester
            if role in ['owner', 'admin', 'developer', 'tester']:
                return True, project
            return False, project

        # 读权限: 所有成员
        return is_member, project

    @staticmethod
    def get_user_project_ids(user):
        """
        获取用户有权限访问的项目ID列表

        Args:
            user: 用户对象

        Returns:
            set: 项目ID集合
        """
        # 作为成员的项目
        member_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )

        # 作为所有者的项目
        owned_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )

        return member_ids | owned_ids

    @staticmethod
    def get_user_favorite_project_ids(user):
        """
        获取用户收藏的项目ID列表

        Args:
            user: 用户对象

        Returns:
            set: 项目ID集合
        """
        return set(
            ProjectMember.objects.filter(user=user, is_favorite=True)
            .values_list('project_id', flat=True)
        )

    @staticmethod
    def get_role_permissions(project_id, role_key):
        """
        获取项目角色的权限列表

        Args:
            project_id: 项目ID
            role_key: 角色标识 (admin/developer/tester/viewer)

        Returns:
            list: 权限代码列表
        """
        # owner 和 admin 拥有所有权限
        if role_key in ['owner', 'admin']:
            return list(PROJECT_PERMISSIONS.keys())

        # 查询自定义权限配置
        try:
            from apps.projects.models import ProjectRole
            role_config = ProjectRole.objects.get(project_id=project_id, role_key=role_key)
            return role_config.permissions
        except ProjectRole.DoesNotExist:
            logger.debug(f"ProjectRole not found for project={project_id}, role={role_key}, using defaults")
            return get_default_permissions(role_key)
        except Exception as e:
            logger.warning(f"Error getting role permissions: {e}")
            return get_default_permissions(role_key)

    @staticmethod
    def get_user_permissions(project_id, user):
        """
        获取用户在项目中的所有权限

        Args:
            project_id: 项目ID
            user: 用户对象

        Returns:
            list: 权限代码列表
        """
        # 系统管理员拥有所有权限
        if is_system_admin(user):
            return list(PROJECT_PERMISSIONS.keys())

        # 检查项目成员身份
        is_member, role, project = ProjectPermissionService.check_member(project_id, user)
        if not is_member:
            return []

        # owner 拥有所有权限
        if role == 'owner':
            return list(PROJECT_PERMISSIONS.keys())

        # 获取角色权限
        return ProjectPermissionService.get_role_permissions(project_id, role)


def has_project_permission(project_id, user, permission_code):
    """
    检查用户是否有指定的项目权限

    Args:
        project_id: 项目ID
        user: 用户对象
        permission_code: 权限代码 (如 'testcase_manage')

    Returns:
        bool: 是否有权限
    """
    # 系统管理员直接通过
    if is_system_admin(user):
        return True

    # 获取用户权限列表
    permissions = ProjectPermissionService.get_user_permissions(project_id, user)

    # 检查是否包含指定权限
    return permission_code in permissions


def get_user_project_permissions(project_id, user):
    """
    获取用户在项目中的所有权限（便捷函数）

    Args:
        project_id: 项目ID
        user: 用户对象

    Returns:
        list: 权限代码列表
    """
    return ProjectPermissionService.get_user_permissions(project_id, user)


# ==================== 便捷函数（向后兼容） ====================

def check_project_member(project_id, user):
    """
    检查用户是否是项目成员（便捷函数）

    保持与旧代码的向后兼容性
    """
    return ProjectPermissionService.check_member(project_id, user)


def check_project_admin(project_id, user):
    """
    检查用户是否是项目管理员（便捷函数）

    保持与旧代码的向后兼容性
    """
    return ProjectPermissionService.check_admin(project_id, user)