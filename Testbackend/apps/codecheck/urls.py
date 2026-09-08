# -*- coding: utf-8 -*-
"""代码检查 URL 路由"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.codecheck.views.tasks import CodeCheckTaskViewSet
from apps.codecheck.views.internal import InternalCasesView

router = DefaultRouter()
router.register(r"", CodeCheckTaskViewSet, basename="code-check")

urlpatterns = [
    # 任务 CRUD（手动触发/查询）
    path("", include(router.urls)),
    # 内部接口（供微服务在 Webhook 触发时拉用例）
    path("internal/cases/", InternalCasesView.as_view(), name="codecheck-internal-cases"),
]
