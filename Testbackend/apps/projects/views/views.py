"""
项目管理视图模块

视图层只负责：
1. 接收请求参数
2. 调用 Service 层处理业务逻辑
3. 返回响应
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.core.response import StandardResponse
from apps.core.utils.helpers import safe_int
from apps.core.decorators import (
    require_project_member,
    require_project_admin,
    require_project_permission
)
from apps.users.authentication import JWTAuthentication
from apps.projects.services import ProjectService, ProjectMemberService, ProjectRoleService
from apps.projects.repositories import ProjectRepository, ProjectMemberRepository


logger = logging.getLogger(__name__)


# ==================== 项目管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_projects_view(request):
    """获取项目列表"""
    result = ProjectService.get_project_list(
        user=request.user,
        filters={
            'status': request.GET.get('status'),
            'type': request.GET.get('type'),
            'keyword': request.GET.get('keyword'),
            'is_favorite': request.GET.get('isFavorite')
        },
        page=safe_int(request.GET.get('page', 1), default=1),
        limit=safe_int(request.GET.get('limit', 10), default=10)
    )
    return StandardResponse(data=result, message='获取成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_view(request, project_identifier):
    """获取项目详情（失败时由 DRF 异常处理器统一返回错误响应）"""
    project_data = ProjectService.get_project(project_identifier, request.user)
    return StandardResponse(data=project_data, message='获取成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_project_view(request):
    """创建项目"""
    project = ProjectService.create_project(request.user, request.data)
    project_data = ProjectService.build_project_data(project, False)
    return StandardResponse(data=project_data, message='创建成功')


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_permission('project_manage')
def update_project_view(request, project_identifier):
    """更新项目"""
    project = ProjectService.update_project(project_identifier, request.user, request.data)
    project_data, _ = ProjectService.get_project(project_identifier, request.user)
    return StandardResponse(data=project_data, message='更新成功')


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_admin
def delete_project_view(request, project_identifier):
    """删除项目"""
    success = ProjectService.delete_project(project_identifier, request.user)
    return StandardResponse(message='删除成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search_projects_view(request):
    """搜索项目"""
    keyword = request.GET.get('q', '')
    results = ProjectService.search_projects(request.user, keyword)
    return StandardResponse(data={'results': results}, message='搜索成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_stats_view(request):
    """获取项目统计"""
    stats = ProjectService.get_project_stats(request.user)
    return StandardResponse(data=stats, message='获取成功')


# ==================== 工作台 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_dashboard_stats_view(request):
    """获取工作台统计"""
    stats = ProjectService.get_project_stats(request.user)
    return StandardResponse(data=stats, message='获取成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_recent_projects_view(request):
    """获取最近访问的项目"""
    limit = safe_int(request.GET.get('limit', 6), default=6)
    projects = ProjectService.get_recent_projects(request.user, limit)
    return StandardResponse(data=projects, message='获取成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_todos_view(request):
    """获取待办事项"""
    todos = ProjectService.get_todos(request.user)
    return StandardResponse(data=todos, message='获取成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_visit_time_view(request, project_identifier):
    """更新项目访问时间"""
    success = ProjectService.update_visit_time(project_identifier, request.user)
    return StandardResponse(message='更新成功')


# ==================== 收藏管理 ====================

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def toggle_favorite_view(request, project_identifier):
    """切换收藏状态"""
    is_favorite = ProjectMemberService.toggle_favorite(project_identifier, request.user)
    message = '收藏成功' if is_favorite else '取消收藏成功'
    return StandardResponse(data={'isFavorite': is_favorite}, message=message)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def set_favorite_view(request, project_identifier):
    """设置收藏状态"""
    is_favorite = request.data.get('isFavorite', True)
    result = ProjectMemberService.set_favorite(project_identifier, request.user, is_favorite)
    message = '收藏成功' if is_favorite else '取消收藏成功'
    return StandardResponse(data={'isFavorite': result}, message=message)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_favorite_projects_view(request):
    """获取收藏的项目"""
    projects = ProjectMemberService.get_favorite_projects(request.user)
    return StandardResponse(data={'projects': projects, 'total': len(projects)}, message='获取成功')


# ==================== 成员管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_members_view(request, project_identifier):
    """获取项目成员列表"""
    members_data = ProjectMemberService.get_members(project_identifier, request.user)
    return StandardResponse(data={'members': members_data}, message='获取成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_permission('member_manage')
def add_project_member_view(request, project_identifier):
    """添加项目成员"""
    member_data = ProjectMemberService.add_member(
        project_identifier=project_identifier,
        operator=request.user,
        user_id=request.data.get('userId'),
        role=request.data.get('role', 'viewer'),
        status=request.data.get('status', 'active')
    )
    return StandardResponse(data=member_data, message='添加成功')


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_permission('member_manage')
def update_project_member_view(request, project_identifier, member_id):
    """更新成员信息"""
    member_data = ProjectMemberService.update_member(
        project_identifier=project_identifier,
        operator=request.user,
        member_id=member_id,
        data=request.data
    )
    return StandardResponse(data=member_data, message='更新成功')


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_permission('member_manage')
def remove_project_member_view(request, project_identifier, member_id):
    """移除成员"""
    success = ProjectMemberService.remove_member(
        project_identifier=project_identifier,
        operator=request.user,
        member_id=member_id
    )
    return StandardResponse(message='移除成功')


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_permission('member_manage')
def batch_update_members_view(request, project_identifier):
    """批量更新成员"""
    # 支持两种参数名：member_ids (推荐) 和 memberIds (兼容)
    member_ids = request.data.get('member_ids', request.data.get('memberIds', []))
    updated_count = ProjectMemberService.batch_update_members(
        project_identifier=project_identifier,
        operator=request.user,
        member_ids=member_ids,
        data=request.data
    )
    return StandardResponse(data={'updatedCount': updated_count}, message=f'成功更新 {updated_count} 个成员')


# ==================== 角色权限管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_roles_view(request, project_identifier):
    """获取项目角色列表"""
    roles_data = ProjectRoleService.get_project_roles(project_identifier, request.user)
    return StandardResponse(data=roles_data, message='获取成功')


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_admin
def update_project_role_view(request, project_identifier, role_key):
    """更新角色权限"""
    import logging
    logger = logging.getLogger(__name__)

    permissions = request.data.get('permissions', [])
    logger.info(f"update_project_role_view: project={project_identifier}, role_key={role_key}, permissions={permissions}")

    success = ProjectRoleService.update_role_permissions(
        project_identifier=project_identifier,
        operator=request.user,
        role_key=role_key,
        permissions=permissions
    )
    return StandardResponse(data={'key': role_key, 'permissions': permissions}, message='权限更新成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_admin
def create_project_role_view(request, project_identifier):
    """创建自定义项目角色"""
    import logging
    logger = logging.getLogger(__name__)

    role_data = ProjectRoleService.create_project_role(
        project_identifier=project_identifier,
        operator=request.user,
        data=request.data
    )
    return StandardResponse(data=role_data, message='角色创建成功')


# ==================== 权限列表 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_permissions_view(request):
    """获取权限列表"""
    from apps.core.permissions import get_all_permissions, get_permission_groups
    permissions = get_all_permissions()
    groups = get_permission_groups()
    return StandardResponse(data={'permissions': permissions, 'groups': groups}, message='获取成功')


# ==================== 项目动态 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_activities_view(request, project_identifier):
    """获取项目动态"""
    limit = int(request.query_params.get('limit', 10))
    activities, _ = ProjectMemberService.get_project_activities(
        project_identifier=project_identifier,
        user=request.user,
        limit=limit
    )
    return StandardResponse(data={'activities': activities}, message='获取成功')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_my_permissions_view(request, project_identifier):
    """获取当前用户在项目中的权限"""
    from apps.core.permissions import (
        is_system_admin, get_user_project_permissions, ProjectPermissionService
    )

    project = ProjectRepository.get_by_identifier(project_identifier)
    if not project:
        return StandardResponse(message='项目不存在', code=404)

    # 检查成员身份
    is_member, role, _ = ProjectMemberRepository.is_project_member(project.id, request.user)

    # 系统管理员或非成员的处理
    if is_system_admin(request.user):
        from apps.core.permissions import PROJECT_PERMISSIONS
        return StandardResponse(data={
            'role': 'admin',
            'permissions': list(PROJECT_PERMISSIONS.keys()),
            'isOwner': False,
            'isAdmin': True,
            'isSystemAdmin': True
        }, message='获取成功')

    if not is_member:
        return StandardResponse(message='无权限访问此项目', code=403)

    # 获取权限列表
    permissions = get_user_project_permissions(project.id, request.user)

    # 判断是否是项目所有者或管理员
    is_owner = project.owner and project.owner.id == request.user.id
    is_admin = role in ['owner', 'admin']

    return StandardResponse(data={
        'role': role,
        'permissions': permissions,
        'isOwner': is_owner,
        'isAdmin': is_admin,
        'isSystemAdmin': False
    }, message='获取成功')


# ==================== 知识库管理 ====================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_knowledge_base_view(request, project_identifier):
    """获取项目关联的知识库信息"""
    kb_data = ProjectService.get_project_knowledge_base(project_identifier, request.user)
    if kb_data is None:
        return StandardResponse(data=None, message='项目未关联知识库')
    return StandardResponse(data=kb_data, message='获取成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def link_knowledge_base_view(request, project_identifier):
    """关联知识库到项目"""
    kb_id = request.data.get('knowledgeBaseId')
    kb_name = request.data.get('knowledgeBaseName')
    result = ProjectService.link_knowledge_base(project_identifier, request.user, kb_id, kb_name)
    return StandardResponse(data=result, message='关联成功')


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def unlink_knowledge_base_view(request, project_identifier):
    """解除知识库关联"""
    success = ProjectService.unlink_knowledge_base(project_identifier, request.user)
    return StandardResponse(message='解除关联成功')


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_project_knowledge_base_view(request, project_identifier):
    """为项目创建并关联知识库"""
    kb_name = request.data.get('name')
    kb_description = request.data.get('description')
    result = ProjectService.create_project_knowledge_base(
        project_identifier, request.user, kb_name, kb_description
    )
    return StandardResponse(data=result, message='知识库创建并关联成功')
