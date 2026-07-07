"""
知识库模块 - 视图层
"""

from .knowledge_base_views import (
    list_knowledge_bases_view,
    create_knowledge_base_view,
    get_knowledge_base_view,
    update_knowledge_base_view,
    delete_knowledge_base_view,
    copy_knowledge_base_view,
    get_copy_progress_view,
    pin_knowledge_base_view,
    hybrid_search_view,
)

from .knowledge_views import (
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
)

from .agent_views import (
    create_session_view,
    agent_chat_view,
    extract_requirements_view,
    generate_test_cases_from_knowledge_view,
)

__all__ = [
    # Knowledge base management
    'list_knowledge_bases_view',
    'create_knowledge_base_view',
    'get_knowledge_base_view',
    'update_knowledge_base_view',
    'delete_knowledge_base_view',
    'copy_knowledge_base_view',
    'get_copy_progress_view',
    'pin_knowledge_base_view',
    'hybrid_search_view',
    # Knowledge document management
    'list_knowledge_view',
    'upload_file_knowledge_view',
    'create_url_knowledge_view',
    'create_manual_knowledge_view',
    'get_knowledge_view',
    'update_knowledge_view',
    'update_manual_knowledge_view',
    'delete_knowledge_view',
    'download_knowledge_view',
    'reparse_knowledge_view',
    'search_knowledge_view',
    'move_knowledge_view',
    'get_move_progress_view',
    'preview_knowledge_view',
    'get_knowledge_content_view',
    # Agent management
    'create_session_view',
    'agent_chat_view',
    'extract_requirements_view',
    'generate_test_cases_from_knowledge_view',
]
