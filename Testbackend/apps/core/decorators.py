"""
权限装饰器模块

提供用于视图函数的权限检查装饰器。
"""

from functools import wraps
from apps.core.permissions import has_project_permission, is_system_admin
from apps.core.response import StandardResponse
from apps.core.permission_service import UnifiedPermissionService


# ---- 内部辅助 ----

def _resolve_project_id(kwargs):
    """从视图 kwargs 中解析项目 ID，支持 project_identifier→project_id 自动转换。
    原来三处装饰器(project_permission/member/admin)各复制了同一段 12 行转换逻辑。
    """
    project_id = kwargs.get('project_id')
    project_identifier = kwargs.get('project_identifier')
    if project_identifier and not project_id:
        from apps.projects.repositories import ProjectRepository
        project = ProjectRepository.get_by_identifier(project_identifier)
        if project:
            return project.id
    return project_id


# ---- 系统级权限装饰器 ----


def require_system_permission(permission_code):
    """
    系统权限检查装饰器

    用于检查用户是否有指定的系统权限。

    用法:
        @api_view(['GET'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_system_permission('user_manage')
        def list_users(request):
            ...

    Args:
        permission_code: 系统权限代码

    Returns:
        装饰器函数
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not UnifiedPermissionService.check_system_permission(
                request.user, permission_code
            ):
                return StandardResponse(message=f'缺少系统权限: {permission_code}', code=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_system_permission(*permission_codes):
    """
    要求任意一个系统权限

    用法:
        @require_any_system_permission('user_manage', 'user_view')
        def user_list(request):
            ...

    Args:
        permission_codes: 权限代码列表

    Returns:
        装饰器函数
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            has_permission = any(
                UnifiedPermissionService.check_system_permission(
                    request.user, code
                )
                for code in permission_codes
            )
            if not has_permission:
                return StandardResponse(
                    message=f'缺少系统权限: {" 或 ".join(permission_codes)}',
                    code=403
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_project_permission(permission_code):
    """
    项目权限检查装饰器

    用于检查用户是否有指定的项目权限。
    需要视图函数接收 project_id 或 project_identifier 参数。

    用法:
        @api_view(['POST'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_project_permission('testcase_manage')
        def create_testcase(request, project_identifier):
            ...

    Args:
        permission_code: 权限代码 (如 'testcase_manage')

    Returns:
        装饰器函数
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            project_id = _resolve_project_id(kwargs)
            if not project_id:
                return StandardResponse(message='无法确定项目', code=400)

            # 检查权限
            if not has_project_permission(project_id, request.user, permission_code):
                return StandardResponse(message='无权限执行此操作', code=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_system_admin(view_func):
    """
    系统管理员权限检查装饰器

    用法:
        @api_view(['POST'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_system_admin
        def create_permission(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_system_admin(request.user):
            return StandardResponse(message='需要系统管理员权限', code=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_project_member(view_func):
    """
    项目成员权限检查装饰器

    检查用户是否是项目成员（任何角色）。

    用法:
        @api_view(['GET'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_project_member
        def get_project_details(request, project_identifier):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.core.permissions import ProjectPermissionService

        project_id = _resolve_project_id(kwargs)
        if not project_id:
            return StandardResponse(message='无法确定项目', code=400)

        # 系统管理员直接通过
        if is_system_admin(request.user):
            return view_func(request, *args, **kwargs)

        # 检查成员身份
        is_member, role, project = ProjectPermissionService.check_member(project_id, request.user)
        if not is_member:
            return StandardResponse(message='无权限访问此项目', code=403)

        return view_func(request, *args, **kwargs)
    return wrapper


def require_project_admin(view_func):
    """
    项目管理员权限检查装饰器

    检查用户是否是项目管理员或所有者。

    用法:
        @api_view(['PUT'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_project_admin
        def update_project_settings(request, project_identifier):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.core.permissions import ProjectPermissionService

        project_id = _resolve_project_id(kwargs)
        if not project_id:
            return StandardResponse(message='无法确定项目', code=400)

        # 系统管理员直接通过
        if is_system_admin(request.user):
            return view_func(request, *args, **kwargs)

        # 检查管理员权限
        is_admin, project = ProjectPermissionService.check_admin(project_id, request.user)
        if not is_admin:
            return StandardResponse(message='需要项目管理员权限', code=403)

        return view_func(request, *args, **kwargs)
    return wrapper
