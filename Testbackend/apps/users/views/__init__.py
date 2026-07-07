"""
用户模块 - 视图层
"""

from .views import (
    login_view, register_view, logout_view, refresh_token_view,
    forgot_password_view, reset_password_view, profile_view,
    change_password_view, send_email_code_view, update_email_view,
    upload_avatar_view, get_users_view, search_users_view,
    get_user_view, update_user_view, delete_user_view, batch_delete_users_view,
    update_user_role_view, update_user_status_view,
    cleanup_test_user_view,
    get_roles_view, create_role_view, update_role_view, delete_role_view,
    get_role_permissions_view, update_role_permissions_view, get_system_permissions_view,
    get_permissions_view, create_permission_view,
    update_permission_view, delete_permission_view,
    get_my_permissions_view, get_permission_info_view
)

__all__ = [
    'login_view',
    'register_view',
    'logout_view',
    'refresh_token_view',
    'forgot_password_view',
    'reset_password_view',
    'profile_view',
    'change_password_view',
    'send_email_code_view',
    'update_email_view',
    'upload_avatar_view',
    'get_users_view',
    'search_users_view',
    'get_user_view',
    'update_user_view',
    'delete_user_view',
    'batch_delete_users_view',
    'update_user_role_view',
    'update_user_status_view',
    'cleanup_test_user_view',
    'get_roles_view',
    'create_role_view',
    'update_role_view',
    'delete_role_view',
    'get_role_permissions_view',
    'update_role_permissions_view',
    'get_system_permissions_view',
    'get_permissions_view',
    'create_permission_view',
    'update_permission_view',
    'delete_permission_view',
    'get_my_permissions_view',
    'get_permission_info_view',
]
