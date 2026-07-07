"""
知识库管理 URL 路由
"""

from django.urls import path
from apps.knowledge.views import (
    # Knowledge base management
    list_knowledge_bases_view,
    create_knowledge_base_view,
    get_knowledge_base_view,
    update_knowledge_base_view,
    delete_knowledge_base_view,
    copy_knowledge_base_view,
    get_copy_progress_view,
    pin_knowledge_base_view,
    hybrid_search_view,
    # Knowledge document management
    list_knowledge_view,
    upload_file_knowledge_view,
    create_url_knowledge_view,
    create_manual_knowledge_view,
    get_knowledge_view,
    update_knowledge_view,
    update_manual_knowledge_view,
    delete_knowledge_view,
    download_knowledge_view,
    reparse_knowledge_view,
    search_knowledge_view,
    move_knowledge_view,
    get_move_progress_view,
    preview_knowledge_view,
    get_knowledge_content_view,
    # Agent management
    create_session_view,
    agent_chat_view,
    extract_requirements_view,
    generate_test_cases_from_knowledge_view,
)

urlpatterns = [
    # ==================== 知识库管理 ====================
    path('', list_knowledge_bases_view, name='list_knowledge_bases'),
    path('create/', create_knowledge_base_view, name='create_knowledge_base'),
    path('copy/', copy_knowledge_base_view, name='copy_knowledge_base'),
    path('copy/progress/<str:task_id>/', get_copy_progress_view, name='get_copy_progress'),
    path('search/', search_knowledge_view, name='search_knowledge'),

    # ==================== 知识库详情操作 ====================
    path('<str:kb_id>/', get_knowledge_base_view, name='get_knowledge_base'),
    path('<str:kb_id>/update/', update_knowledge_base_view, name='update_knowledge_base'),
    path('<str:kb_id>/delete/', delete_knowledge_base_view, name='delete_knowledge_base'),
    path('<str:kb_id>/pin/', pin_knowledge_base_view, name='pin_knowledge_base'),
    path('<str:kb_id>/search/', hybrid_search_view, name='hybrid_search'),

    # ==================== 知识文档管理 ====================
    path('<str:kb_id>/knowledge/', list_knowledge_view, name='list_knowledge'),
    path('<str:kb_id>/knowledge/file/', upload_file_knowledge_view, name='upload_file_knowledge'),
    path('<str:kb_id>/knowledge/url/', create_url_knowledge_view, name='create_url_knowledge'),
    path('<str:kb_id>/knowledge/manual/', create_manual_knowledge_view, name='create_manual_knowledge'),

    # ==================== 知识详情操作 ====================
    path('knowledge/<str:knowledge_id>/', get_knowledge_view, name='get_knowledge'),
    path('knowledge/<str:knowledge_id>/update/', update_knowledge_view, name='update_knowledge'),
    path('knowledge/<str:knowledge_id>/delete/', delete_knowledge_view, name='delete_knowledge'),
    path('knowledge/<str:knowledge_id>/download/', download_knowledge_view, name='download_knowledge'),
    path('knowledge/<str:knowledge_id>/reparse/', reparse_knowledge_view, name='reparse_knowledge'),
    path('knowledge/<str:knowledge_id>/preview/', preview_knowledge_view, name='preview_knowledge'),
    path('knowledge/<str:knowledge_id>/content/', get_knowledge_content_view, name='get_knowledge_content'),
    path('knowledge/manual/<str:knowledge_id>/update/', update_manual_knowledge_view, name='update_manual_knowledge'),

    # ==================== 知识迁移 ====================
    path('knowledge/move/', move_knowledge_view, name='move_knowledge'),
    path('knowledge/move/progress/<str:task_id>/', get_move_progress_view, name='get_move_progress'),

    # ==================== Agent 会话管理 ====================
    path('sessions/', create_session_view, name='create_session'),
    path('sessions/<str:session_id>/chat/', agent_chat_view, name='agent_chat'),
    path('extract/', extract_requirements_view, name='extract_requirements'),
    path('generate-testcases/', generate_test_cases_from_knowledge_view, name='generate_test_cases_from_knowledge'),
]
