"""
统一权限服务

提供系统级权限和项目级权限的统一管理。
所有权限检查逻辑集中在此模块，避免分散在各个视图文件中。
"""

import logging
from apps.core.permissions import (
    is_system_admin,
    has_project_permission,
    get_user_project_permissions,
    PROJECT_PERMISSIONS,
    SYSTEM_PERMISSIONS,
    ADMIN_SYSTEM_PERMISSIONS,
    DEFAULT_USER_SYSTEM_PERMISSIONS,
    SYSTEM_ROLE_DEFAULTS,
)

logger = logging.getLogger(__name__)


# ==================== 系统权限常量（向后兼容） ====================

# 以下常量从 permissions.py 导入，保留此处的引用以兼容旧代码
# SYSTEM_PERMISSIONS, ADMIN_PERMISSIONS, DEFAULT_USER_PERMISSIONS 已移至 permissions.py


class UnifiedPermissionService:
    """
    统一权限服务

    提供系统权限和项目权限的统一检查入口。
    所有权限验证都应通过此服务进行。
    """

    # ==================== 系统权限 ====================

    @staticmethod
    def check_system_permission(user, permission_code):
        """
        检查用户是否拥有指定的系统权限

        Args:
            user: 用户对象
            permission_code: 权限代码

        Returns:
            bool: 是否拥有权限
        """
        if not user or not user.is_authenticated:
            return False

        # 系统管理员拥有所有权限
        if is_system_admin(user):
            return True

        # 检查用户的系统角色是否有该权限
        if not user.system_role:
            return False

        # 从 Role.permissions JSONField 读取权限列表
        role_permissions = user.system_role.permissions or []
        return permission_code in role_permissions

    @staticmethod
    def get_user_system_permissions(user):
        """
        获取用户的系统权限列表

        Args:
            user: 用户对象

        Returns:
            list: 权限代码列表
        """
        if not user or not user.is_authenticated:
            return []

        # 系统管理员拥有所有权限
        if is_system_admin(user):
            return ADMIN_SYSTEM_PERMISSIONS

        # 检查用户的系统角色
        if not user.system_role:
            return []

        # 从 Role.permissions JSONField 读取权限列表
        role_permissions = user.system_role.permissions or []

        # 如果 JSONField 为空，使用默认权限映射
        if not role_permissions and user.system_role.code in SYSTEM_ROLE_DEFAULTS:
            return SYSTEM_ROLE_DEFAULTS[user.system_role.code].copy()

        return list(role_permissions)

    @staticmethod
    def is_system_admin(user):
        """
        检查用户是否是系统管理员

        Args:
            user: 用户对象

        Returns:
            bool: 是否是系统管理员
        """
        return is_system_admin(user)

    # ==================== 项目权限 ====================

    @staticmethod
    def check_project_permission(project_id, user, permission_code):
        """
        检查用户在项目中是否拥有指定权限

        权限检查优先级：
        1. 系统管理员 -> 所有权限
        2. 项目所有者 -> 所有权限
        3. 项目角色权限 -> 按配置检查

        Args:
            project_id: 项目ID
            user: 用户对象
            permission_code: 权限代码

        Returns:
            bool: 是否拥有权限
        """
        if not user or not user.is_authenticated:
            return False

        # 系统管理员拥有所有权限
        if is_system_admin(user):
            return True

        # 项目级权限检查
        return has_project_permission(project_id, user, permission_code)

    @staticmethod
    def get_user_project_permissions(project_id, user):
        """
        获取用户在项目中的权限列表

        Args:
            project_id: 项目ID
            user: 用户对象

        Returns:
            list: 权限代码列表
        """
        if not user or not user.is_authenticated:
            return []

        return get_user_project_permissions(project_id, user)

    # ==================== 统一权限检查 ====================

    @staticmethod
    def check_permission(user, permission_code, project_id=None):
        """
        统一权限检查入口

        自动判断是系统权限还是项目权限：
        - 如果 permission_code 在 SYSTEM_PERMISSIONS 中，检查系统权限
        - 如果 permission_code 在 PROJECT_PERMISSIONS 中，检查项目权限
        - 如果提供了 project_id，优先检查项目权限

        Args:
            user: 用户对象
            permission_code: 权限代码
            project_id: 项目ID（可选）

        Returns:
            bool: 是否拥有权限
        """
        if not user or not user.is_authenticated:
            return False

        # 判断权限类型
        is_system_perm = permission_code in SYSTEM_PERMISSIONS
        is_project_perm = permission_code in PROJECT_PERMISSIONS

        # 如果明确是系统权限
        if is_system_perm and not project_id:
            return UnifiedPermissionService.check_system_permission(user, permission_code)

        # 如果是项目权限且有项目ID
        if is_project_perm and project_id:
            return UnifiedPermissionService.check_project_permission(
                project_id, user, permission_code
            )

        # 如果权限代码同时存在于两个体系中，优先检查系统权限
        if is_system_perm:
            return UnifiedPermissionService.check_system_permission(user, permission_code)

        if is_project_perm and project_id:
            return UnifiedPermissionService.check_project_permission(
                project_id, user, permission_code
            )

        # 未知权限类型
        logger.warning(f"Unknown permission code: {permission_code}")
        return False

    @staticmethod
    def get_user_all_permissions(user, project_id=None):
        """
        获取用户的所有权限（系统+项目）

        Args:
            user: 用户对象
            project_id: 项目ID（可选）

        Returns:
            dict: {
                'system': [...],  # 系统权限列表
                'project': [...]  # 项目权限列表（如果有项目ID）
            }
        """
        result = {
            'system': UnifiedPermissionService.get_user_system_permissions(user),
            'project': []
        }

        if project_id:
            result['project'] = UnifiedPermissionService.get_user_project_permissions(
                project_id, user
            )

        return result

    @staticmethod
    def get_permission_info():
        """
        获取权限体系信息

        Returns:
            dict: 权限体系结构信息
        """
        return {
            'system_permissions': [
                {'code': code, 'name': name}
                for code, name in SYSTEM_PERMISSIONS.items()
            ],
            'project_permissions': [
                {'code': code, 'name': name}
                for code, name in PROJECT_PERMISSIONS.items()
            ]
        }
