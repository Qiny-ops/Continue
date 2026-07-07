from django.urls import path
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

urlpatterns = [
    # ==================== 认证相关 ====================
    # 用户登录
    path('login/', login_view, name='login'),
    # 用户注册
    path('register/', register_view, name='register'),
    # 用户登出
    path('logout/', logout_view, name='logout'),
    # 刷新Token
    path('refresh-token/', refresh_token_view, name='refresh_token'),
    # 忘记密码
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    # 重置密码
    path('reset-password/<str:token>/', reset_password_view, name='reset_password'),

    # ==================== 用户信息管理 ====================
    # 获取用户列表
    path('', get_users_view, name='get_users'),
    # 搜索用户（项目添加成员用）
    path('search/', search_users_view, name='search_users'),
    # 获取单个用户
    path('<int:user_id>/', get_user_view, name='get_user'),
    # 更新用户
    path('<int:user_id>/update/', update_user_view, name='update_user'),
    # 删除用户
    path('<int:user_id>/delete/', delete_user_view, name='delete_user'),
    # 批量删除用户
    path('batch-delete/', batch_delete_users_view, name='batch_delete_users'),
    # 获取/更新当前用户信息
    path('profile/', profile_view, name='profile'),
    # 修改密码
    path('change-password/', change_password_view, name='change_password'),
    # 发送邮箱验证码
    path('send-email-code/', send_email_code_view, name='send_email_code'),
    # 更新邮箱
    path('update-email/', update_email_view, name='update_email'),
    # 上传头像
    path('upload-avatar/', upload_avatar_view, name='upload_avatar'),

    # ==================== 角色权限管理 ====================
    # 获取角色列表
    path('roles/', get_roles_view, name='get_roles'),
    # 创建角色
    path('roles/create/', create_role_view, name='create_role'),
    # 更新角色
    path('roles/<int:role_id>/update/', update_role_view, name='update_role'),
    # 删除角色
    path('roles/<int:role_id>/delete/', delete_role_view, name='delete_role'),
    # 获取角色权限
    path('roles/<int:role_id>/permissions/', get_role_permissions_view, name='get_role_permissions'),
    # 更新角色权限
    path('roles/<int:role_id>/permissions/update/', update_role_permissions_view, name='update_role_permissions'),
    # 获取系统权限列表
    path('system-permissions/', get_system_permissions_view, name='get_system_permissions'),
    # 获取权限列表
    path('permissions/', get_permissions_view, name='get_permissions'),
    # 创建权限
    path('permissions/create/', create_permission_view, name='create_permission'),
    # 更新权限
    path('permissions/<int:permission_id>/', update_permission_view, name='update_permission'),
    # 删除权限
    path('permissions/<int:permission_id>/delete/', delete_permission_view, name='delete_permission'),

    # ==================== 用户管理操作 ====================
    # 更新用户角色
    path('<int:user_id>/role/', update_user_role_view, name='update_user_role'),
    # 更新用户状态
    path('<int:user_id>/status/', update_user_status_view, name='update_user_status'),
    # 清理测试用户（API 测试用）
    path('cleanup-test-user/', cleanup_test_user_view, name='cleanup_test_user'),

    # ==================== 权限查询 ====================
    # 获取当前用户权限
    path('my-permissions/', get_my_permissions_view, name='get_my_permissions'),
    # 获取权限体系信息
    path('permission-info/', get_permission_info_view, name='get_permission_info'),
]
