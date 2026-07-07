"""
项目模块 - 视图层
"""

from .views import (
    get_projects_view, get_project_view, create_project_view,
    update_project_view, delete_project_view, search_projects_view,
    get_project_stats_view, toggle_favorite_view, set_favorite_view,
    get_favorite_projects_view, get_project_members_view, add_project_member_view,
    update_project_member_view, remove_project_member_view, batch_update_members_view,
    get_project_roles_view, update_project_role_view, create_project_role_view, get_permissions_view,
    get_my_permissions_view,
    get_project_knowledge_base_view, link_knowledge_base_view, unlink_knowledge_base_view,
    create_project_knowledge_base_view,
    get_dashboard_stats_view, get_recent_projects_view, get_todos_view,
    update_visit_time_view, get_project_activities_view
)

__all__ = [
    'get_projects_view',
    'get_project_view',
    'create_project_view',
    'update_project_view',
    'delete_project_view',
    'search_projects_view',
    'get_project_stats_view',
    'toggle_favorite_view',
    'set_favorite_view',
    'get_favorite_projects_view',
    'get_project_members_view',
    'add_project_member_view',
    'update_project_member_view',
    'remove_project_member_view',
    'batch_update_members_view',
    'get_project_roles_view',
    'update_project_role_view',
    'create_project_role_view',
    'get_permissions_view',
    'get_my_permissions_view',
    'get_project_knowledge_base_view',
    'link_knowledge_base_view',
    'unlink_knowledge_base_view',
    'create_project_knowledge_base_view',
    'get_dashboard_stats_view',
    'get_recent_projects_view',
    'get_todos_view',
    'update_visit_time_view',
    'get_project_activities_view',
]
