from django.urls import path, include
from rest_framework.routers import DefaultRouter
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

urlpatterns = [
    # ==================== 项目基础操作 ====================
    path('', get_projects_view, name='get_projects'),
    path('create/', create_project_view, name='create_project'),
    path('search/', search_projects_view, name='search_projects'),
    path('stats/', get_project_stats_view, name='get_project_stats'),
    path('permissions/', get_permissions_view, name='get_permissions'),

    # ==================== 工作台 ====================
    path('dashboard/stats/', get_dashboard_stats_view, name='get_dashboard_stats'),
    path('dashboard/recent-projects/', get_recent_projects_view, name='get_recent_projects'),
    path('dashboard/todos/', get_todos_view, name='get_todos'),

    # ==================== 项目收藏管理 ====================
    path('favorites/', get_favorite_projects_view, name='get_favorite_projects'),

    # ==================== 项目详情操作 ====================
    path('<str:project_identifier>/', get_project_view, name='get_project'),
    path('<str:project_identifier>/update/', update_project_view, name='update_project'),
    path('<str:project_identifier>/delete/', delete_project_view, name='delete_project'),
    path('<str:project_identifier>/visit/', update_visit_time_view, name='update_visit_time'),
    path('<str:project_identifier>/activities/', get_project_activities_view, name='get_project_activities'),

    # ==================== 项目收藏操作 ====================
    path('<str:project_identifier>/favorite/', toggle_favorite_view, name='toggle_favorite'),
    path('<str:project_identifier>/favorite/set/', set_favorite_view, name='set_favorite'),

    # ==================== 项目成员管理 ====================
    path('<str:project_identifier>/members/', get_project_members_view, name='get_project_members'),
    path('<str:project_identifier>/members/add/', add_project_member_view, name='add_project_member'),
    path('<str:project_identifier>/members/batch/', batch_update_members_view, name='batch_update_members'),
    path('<str:project_identifier>/members/<int:member_id>/', update_project_member_view, name='update_project_member'),
    path('<str:project_identifier>/members/<int:member_id>/delete/', remove_project_member_view, name='remove_project_member'),

    # ==================== 项目角色管理 ====================
    path('<str:project_identifier>/roles/', get_project_roles_view, name='get_project_roles'),
    path('<str:project_identifier>/roles/create/', create_project_role_view, name='create_project_role'),
    path('<str:project_identifier>/roles/<str:role_key>/', update_project_role_view, name='update_project_role'),

    # ==================== 项目权限查询 ====================
    path('<str:project_identifier>/my-permissions/', get_my_permissions_view, name='get_my_permissions'),

    # ==================== 项目知识库管理 ====================
    path('<str:project_identifier>/knowledge-base/', get_project_knowledge_base_view, name='get_project_knowledge_base'),
    path('<str:project_identifier>/knowledge-base/link/', link_knowledge_base_view, name='link_knowledge_base'),
    path('<str:project_identifier>/knowledge-base/unlink/', unlink_knowledge_base_view, name='unlink_knowledge_base'),
    path('<str:project_identifier>/knowledge-base/create/', create_project_knowledge_base_view, name='create_project_knowledge_base'),
]