"""
用户认证视图模块

视图层只负责：
1. 接收请求参数
2. 调用 Service 层处理业务逻辑
3. 返回响应
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.core.response import StandardResponse
from apps.core.permissions import is_system_admin, IsInternalServiceOrAuthenticated
from apps.core.utils.helpers import safe_int
from apps.core.decorators import (
    require_system_admin,
    require_system_permission,
    require_any_system_permission
)
from apps.users.authentication import JWTAuthentication, InternalServiceAuthentication
from apps.users.models import User
from apps.users.services import (
    AuthService, UserService, PasswordService,
    EmailService, RoleService, PermissionService, UserServiceExtended
)

logger = logging.getLogger(__name__)


# ==================== 认证相关 ====================

@api_view(['POST'])
def login_view(request):
    """用户登录"""
    result, error = AuthService.login(
        username=request.data.get('username'),
        password=request.data.get('password'),
        request=request
    )

    if error:
        code = 401 if '密码' in error or '账号' in error else 400
        return StandardResponse(message=error, code=code)

    user = result['user']

    # 获取用户系统权限
    from apps.core.permission_service import UnifiedPermissionService
    system_permissions = UnifiedPermissionService.get_user_system_permissions(user)

    return StandardResponse(data={
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'avatar': user.avatar or '',
        'title': user.title or '',
        'system_role': user.system_role.code if user.system_role else None,
        'system_permissions': system_permissions,
        'token': result['token']
    }, message='登录成功')


@api_view(['POST'])
def register_view(request):
    """用户注册"""
    try:
        user = UserService.create_user(
            username=request.data.get('username'),
            email=request.data.get('email'),
            password=request.data.get('password'),
            name=request.data.get('name'),
            phone=request.data.get('phone', '')
        )
    except Exception as e:
        return StandardResponse(message=str(e), code=400)

    return StandardResponse(data={
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'email': user.email
    }, message='注册成功', code=201)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header[7:]  # 切掉 "Bearer "
            if token:
                AuthService.logout(token, request.user)
        except Exception as e:
            logger.warning(f"登出处理失败: {e}")
            return StandardResponse(message='登出处理失败', code=500)

    return StandardResponse(message='登出成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """刷新Token"""
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header:
        return StandardResponse(message='缺少认证token', code=401)

    try:
        token = auth_header.split(' ')[1]
    except IndexError:
        return StandardResponse(message='认证token格式错误', code=401)

    new_token, error = AuthService.refresh_token(token)
    if error:
        return StandardResponse(message=error, code=401)

    return StandardResponse(data={'token': new_token}, message='Token刷新成功')


@api_view(['POST'])
def forgot_password_view(request):
    """忘记密码 - 发送重置邮件"""
    try:
        UserServiceExtended.send_password_reset_email(request.data.get('email'))
        return StandardResponse(message='重置密码链接已发送到您的邮箱')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['POST'])
def reset_password_view(request, user_id, token):
    """重置密码 — 使用加密签名 token 验证"""
    try:
        UserServiceExtended.reset_password(user_id, token, request.data.get('new_password'))
        return StandardResponse(message='密码重置成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


# ==================== 用户资料 ====================

@api_view(['GET', 'PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """获取/更新用户资料"""
    user = request.user

    if request.method == 'GET':
        # 获取用户系统权限
        from apps.core.permission_service import UnifiedPermissionService
        system_permissions = UnifiedPermissionService.get_user_system_permissions(user)

        return StandardResponse(data={
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar,
            'title': user.title or '',
            'system_role': user.system_role.code if user.system_role else None,
            'system_role_name': user.system_role.name if user.system_role else None,
            'system_permissions': system_permissions,
            'status': user.status,
            'created_at': user.created_at.isoformat(),
            'last_login_time': user.last_login_time.isoformat() if user.last_login_time else None,
            'last_login_ip': user.last_login_ip if hasattr(user, 'last_login_ip') else ''
        }, message='获取成功')

    elif request.method == 'PUT':
        try:
            user = UserService.update_user(user, request.data)
        except Exception as e:
            return StandardResponse(message=str(e), code=400)

        return StandardResponse(data={
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar
        }, message='更新成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """修改密码"""
    try:
        PasswordService.change_password(
            user=request.user,
            old_password=request.data.get('old_password'),
            new_password=request.data.get('new_password')
        )
        return StandardResponse(message='密码修改成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_email_code_view(request):
    """发送邮箱验证码"""
    try:
        EmailService.send_verification_code(
            email=request.data.get('email'),
            purpose=request.data.get('purpose', 'update_email')
        )
        return StandardResponse(message='验证码已发送')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_email_view(request):
    """更新邮箱"""
    try:
        UserServiceExtended.update_email(
            user=request.user,
            new_email=request.data.get('email'),
            code=request.data.get('code')
        )
        return StandardResponse(message='邮箱更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def upload_avatar_view(request):
    """上传头像"""
    if 'avatar' not in request.FILES:
        return StandardResponse(message='请选择要上传的头像', code=400)

    try:
        avatar_path = UserServiceExtended.upload_avatar(
            user=request.user,
            avatar_file=request.FILES['avatar']
        )
        return StandardResponse(data={'avatar': avatar_path}, message='头像上传成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


# ==================== 用户管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_users_view(request):
    """获取用户列表

    安全说明：非管理员用户只能看到基本字段，敏感信息（邮箱、手机、登录时间）被隐藏。
    """
    page = safe_int(request.GET.get('page', 1), default=1)
    limit = safe_int(request.GET.get('limit', 20), default=20)

    result = UserService.get_users_list(
        filters={
            'keyword': request.GET.get('keyword', ''),
            'status': request.GET.get('status', ''),
            'role': request.GET.get('role', '')
        },
        page=page,
        limit=limit
    )

    # 判断是否为管理员
    is_admin = is_system_admin(request.user)

    users_data = []
    for user in result['users']:
        # 基础字段（所有用户可见）
        user_data = {
            'id': user.id,
            'username': user.username,
            'name': user.name or user.username,
            'avatar': user.avatar,
            'status': user.status,
            'system_role': user.system_role.code if user.system_role else None,
            'system_role_name': user.system_role.name if user.system_role else None,
        }

        # 敏感字段（仅管理员可见）
        if is_admin:
            user_data.update({
                'email': user.email,
                'phone': user.phone,
                'created_at': user.created_at.isoformat(),
                'last_login_time': user.last_login_time.isoformat() if user.last_login_time else None
            })

        users_data.append(user_data)

    return StandardResponse(data={'users': users_data, 'total': result['total']}, message='获取成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search_users_view(request):
    """搜索用户"""
    users = UserServiceExtended.search_users(
        keyword=request.GET.get('keyword', ''),
        limit=safe_int(request.GET.get('limit', 20), default=20)
    )
    return StandardResponse(data=users, message='获取成功')


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_permission('user_manage')
def update_user_role_view(request, user_id):
    """更新用户角色"""
    try:
        UserServiceExtended.update_user_role(
            user_id=user_id,
            role_code=request.data.get('role'),
            operator=request.user
        )
        return StandardResponse(message='角色更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_permission('user_manage')
def update_user_status_view(request, user_id):
    """更新用户状态"""
    try:
        UserServiceExtended.update_user_status(
            user_id=user_id,
            status=request.data.get('status'),
            operator=request.user
        )
        return StandardResponse(message='状态更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


# ==================== 角色管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_any_system_permission('role_view', 'role_manage', 'user_manage')
def get_roles_view(request):
    """获取角色列表"""
    from apps.core.permissions import SYSTEM_ROLE_DEFAULTS

    roles = RoleService.get_roles_with_user_count()

    roles_data = []
    for role in roles:
        # 获取权限：如果数据库中有则使用，否则使用默认值
        permissions = role.permissions
        if not permissions and role.code in SYSTEM_ROLE_DEFAULTS:
            permissions = SYSTEM_ROLE_DEFAULTS[role.code]

        roles_data.append({
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'type': role.type,
            'status': role.status,
            'description': role.description,
            'user_count': role.user_count,
            'is_system': role.type == 'system',
            'permissions': permissions or []
        })

    return StandardResponse(data={'roles': roles_data}, message='获取成功')


# ==================== 权限管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_permissions_view(request):
    """获取权限列表（直接从核心权限模块获取）"""
    from apps.core.permissions import get_all_permissions, get_permission_groups
    return StandardResponse(data={
        'permissions': get_all_permissions(),
        'groups': get_permission_groups(),
    }, message='获取成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def create_permission_view(request):
    """创建权限"""
    try:
        permission = PermissionService.create_permission(
            name=request.data.get('name'),
            code=request.data.get('code'),
            type=request.data.get('type', 'project'),
            description=request.data.get('description', ''),
            operator=request.user
        )
        return StandardResponse(data={
            'id': permission.id,
            'name': permission.name,
            'code': permission.code,
            'type': permission.type,
            'description': permission.description
        }, message='创建成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def update_permission_view(request, permission_id):
    """更新权限"""
    try:
        permission = PermissionService.update_permission(
            permission_id=permission_id,
            data=request.data,
            operator=request.user
        )
        return StandardResponse(data={
            'id': permission.id,
            'name': permission.name,
            'code': permission.code,
            'type': permission.type,
            'description': permission.description,
            'status': permission.status
        }, message='更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['DELETE'])
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def delete_permission_view(request, permission_id):
    """删除权限"""
    try:
        PermissionService.delete_permission(
            permission_id=permission_id,
            operator=request.user
        )
        return StandardResponse(message='删除成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


# ==================== 用户详情管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_any_system_permission('user_view', 'user_manage')
def get_user_view(request, user_id):
    """获取单个用户详情"""
    try:
        user = UserService.get_user_by_id(user_id)
        return StandardResponse(data={
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar,
            'status': user.status,
            'system_role': user.system_role.code if user.system_role else None,
            'system_role_name': user.system_role.name if user.system_role else None,
            'created_at': user.created_at.isoformat(),
            'last_login_time': user.last_login_time.isoformat() if user.last_login_time else None
        }, message='获取成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=404)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_user_view(request, user_id):
    """更新用户信息"""
    if not is_system_admin(request.user) and request.user.id != user_id:
        return StandardResponse(message='无权限更新此用户', code=403)

    try:
        user = UserService.get_user_by_id(user_id)
        allowed_fields = ['name', 'phone']
        update_data = {}
        for field in allowed_fields:
            if field in request.data:
                update_data[field] = request.data[field]

        if update_data:
            UserService.update_user(user, update_data)

        return StandardResponse(data={
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar,
            'status': user.status,
            'system_role': user.system_role.code if user.system_role else None,
            'system_role_name': user.system_role.name if user.system_role else None,
        }, message='更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def delete_user_view(request, user_id):
    """删除用户

    业务逻辑：
    1. 只有管理员可以删除用户
    2. 不能删除自己
    3. 如果用户有关联数据，需要指定 transfer_to 参数转移数据
    """
    if request.user.id == user_id:
        return StandardResponse(message='不能删除自己', code=400)

    # 获取数据转移目标用户ID（可选）
    transfer_to_user_id = request.query_params.get('transfer_to')

    try:
        deleted_username = UserServiceExtended.delete_user(
            user_id=user_id,
            operator=request.user,
            transfer_to_user_id=transfer_to_user_id
        )
        return StandardResponse(message=f'用户 {deleted_username} 已删除')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def batch_delete_users_view(request):
    """批量删除用户

    请求体：
    {
        "user_ids": [1, 2, 3]
    }

    返回：
    {
        "deleted_count": 2,
        "failed_users": [{"id": 3, "username": "test", "reason": "有关联数据"}]
    }
    """
    user_ids = request.data.get('user_ids', [])

    if not user_ids or not isinstance(user_ids, list):
        return StandardResponse(message='请提供要删除的用户ID列表', code=400)

    try:
        deleted_count, failed_users = UserServiceExtended.batch_delete_users(
            user_ids=user_ids,
            operator=request.user
        )
        return StandardResponse(data={
            'deleted_count': deleted_count,
            'failed_users': failed_users
        }, message=f'成功删除 {deleted_count} 个用户')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication, InternalServiceAuthentication])
@permission_classes([IsInternalServiceOrAuthenticated])
def cleanup_test_user_view(request):
    """清理测试用户

    仅删除以 test_ 开头的用户名，用于 API 测试后清理测试账号。
    支持 JWT 认证或内部服务认证（X-Internal-API-Key 请求头）。
    """
    username = request.query_params.get('username')

    if not username:
        return StandardResponse(message='请提供用户名', code=400)

    # 安全检查：只能删除以 test_ 开头的用户名
    if not username.startswith('test_'):
        return StandardResponse(message='只能删除测试账号（用户名以 test_ 开头）', code=403)

    # 时间戳格式的安全检查：test_YYYYMMDD_HHMMSS_xxxx
    import re
    if not re.match(r'test_\d{8}_\d{6}_[a-z0-9]{12}$', username):
        return StandardResponse(message='用户名格式不符合测试账号规范', code=400)

    try:
        user = User.objects.get(username=username)

        # 再次确认用户名符合测试账号格式
        if not user.username.startswith('test_'):
            return StandardResponse(message='该用户不是测试账号', code=403)

        user_id = user.id
        user.delete()

        logger.info(f"清理测试账号: {username} (ID: {user_id})")
        return StandardResponse(message=f'测试用户 {username} 已删除')

    except User.DoesNotExist:
        # 用户不存在也算清理成功
        return StandardResponse(message=f'用户 {username} 不存在')


# ==================== 角色管理 ====================

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def create_role_view(request):
    """创建角色"""

    try:
        role = RoleService.create_role(
            name=request.data.get('name'),
            code=request.data.get('code'),
            description=request.data.get('description', ''),
            role_type=request.data.get('type', 'default')
        )
        return StandardResponse(data={
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'type': role.type,
            'description': role.description,
            'status': role.status
        }, message='创建成功', code=201)
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def update_role_view(request, role_id):
    """更新角色"""

    try:
        role = RoleService.update_role(
            role_id=role_id,
            data=request.data
        )
        return StandardResponse(data={
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'type': role.type,
            'description': role.description,
            'status': role.status
        }, message='更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_admin
def delete_role_view(request, role_id):
    """删除角色"""

    try:
        RoleService.delete_role(role_id)
        return StandardResponse(message='角色已删除')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_any_system_permission('role_view', 'role_manage')
def get_role_permissions_view(request, role_id):
    """获取角色权限"""

    try:
        permissions = RoleService.get_role_permissions(role_id)
        return StandardResponse(data={'permissions': permissions})
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_system_permission('role_manage')
def update_role_permissions_view(request, role_id):
    """更新角色权限"""

    try:
        permissions = request.data.get('permissions', [])
        updated_permissions = RoleService.update_role_permissions(role_id, permissions)
        return StandardResponse(data={'permissions': updated_permissions}, message='权限更新成功')
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_any_system_permission('role_view', 'role_manage')
def get_system_permissions_view(request):
    """获取系统权限列表"""

    try:
        permissions = RoleService.get_system_permissions()
        return StandardResponse(data={'permissions': permissions})
    except Exception as e:
        return StandardResponse(message=str(e), code=400)


# ==================== 权限查询 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_my_permissions_view(request):
    """获取当前用户的所有权限

    查询参数：
    - project: 项目ID（可选），如果提供则返回项目权限

    返回：
    - system: 系统权限列表
    - project: 项目权限列表（如果提供了 project 参数）
    """
    from apps.core.permission_service import UnifiedPermissionService

    project_id = request.query_params.get('project')

    try:
        permissions = UnifiedPermissionService.get_user_all_permissions(
            request.user, project_id if project_id else None
        )
        return StandardResponse(data=permissions)
    except Exception as e:
        logger.error(f"获取用户权限失败: {e}")
        return StandardResponse(message=str(e), code=400)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_permission_info_view(request):
    """获取权限体系信息

    返回所有系统权限和项目权限的定义
    """
    from apps.core.permission_service import UnifiedPermissionService

    try:
        info = UnifiedPermissionService.get_permission_info()
        return StandardResponse(data=info)
    except Exception as e:
        logger.error(f"获取权限信息失败: {e}")
        return StandardResponse(message=str(e), code=400)
