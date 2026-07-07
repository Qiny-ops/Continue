# -*- coding: utf-8 -*-
"""
接口测试 URL 路由

API 路由结构：
====================

/api/apitest/environments/     - 测试环境管理
    ├── /                       - 环境列表
    ├── /<id>/                  - 环境详情
    ├── /<id>/set_default/      - 设置默认环境
    └── /<id>/test_connection/  - 测试连接

/api/apitest/cases/            - 测试用例管理
    ├── /                       - 用例列表
    ├── /<id>/                  - 用例详情
    ├── /<id>/execute/          - 执行用例（流式）
    ├── /<id>/runs/             - 执行记录
    └── /generate_from_kb/      - 从知识库生成

/api/apitest/runs/             - 执行记录管理
    ├── /                       - 记录列表
    └── /<id>/                  - 记录详情
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.apitest.views import (
    ApiEnvironmentViewSet,
    ApiTestCaseViewSet,
    ApiTestRunViewSet,
)

router = DefaultRouter()
router.register(r'environments', ApiEnvironmentViewSet, basename='api-environment')
router.register(r'cases', ApiTestCaseViewSet, basename='api-testcase')
router.register(r'runs', ApiTestRunViewSet, basename='api-testrun')

urlpatterns = [
    path('', include(router.urls)),
]
