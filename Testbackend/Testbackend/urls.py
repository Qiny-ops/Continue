"""
URL configuration for Testbackend project.

API 路由结构：
====================

/api/users/          - 用户管理模块
    ├── login/                   - 用户登录
    ├── register/                - 用户注册
    ├── logout/                  - 用户登出
    ├── forgot-password/         - 忘记密码
    ├── reset-password/<token>/  - 重置密码
    ├── profile/                 - 用户信息
    ├── roles/                   - 角色管理
    ├── permissions/             - 权限管理
    └── <user_id>/...            - 用户操作

/api/projects/       - 项目管理模块
    ├── create/                  - 创建项目
    ├── search/                  - 搜索项目
    ├── stats/                   - 项目统计
    ├── favorites/               - 收藏列表
    └── <identifier>/...         - 项目操作（支持ID或code）

/api/testcase/       - 测试用例模块
    ├── repositories/            - 用例库管理
    ├── versions/                - 版本管理
    ├── modules/                 - 模块管理
    ├── cases/                   - 用例管理
    ├── reviews/                 - 评审管理
    └── executions/              - 执行记录

/api/knowledge/      - 知识库管理模块
    ├── create/                  - 创建知识库
    ├── copy/                    - 复制知识库
    ├── search/                  - 搜索知识
    └── <kb_id>/...              - 知识库操作
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ==================== Django Admin ====================
    path("admin/", admin.site.urls),

    # ==================== API 接口 ====================
    # 用户管理接口
    path("api/users/", include("apps.users.urls")),

    # 项目管理接口
    path("api/projects/", include("apps.projects.urls")),

    # 测试用例管理接口
    path("api/testcase/", include("apps.testcase.urls")),

    # 知识库管理接口
    path("api/knowledge/", include("apps.knowledge.urls")),

    # 接口测试管理接口
    path("api/apitest/", include("apps.apitest.urls")),

    # Web 自动化管理接口
    path("api/webauto/", include("apps.webauto.urls")),

    # 需求管理接口
    path("api/requirements/", include("apps.requirement.urls")),
]

# ==================== 开发环境配置 ====================
# 开发环境下提供 media 文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
