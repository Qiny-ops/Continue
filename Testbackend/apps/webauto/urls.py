# -*- coding: utf-8 -*-
"""Web 自动化 URL 路由"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.webauto.views.web_automation import WebAutomationViewSet

router = DefaultRouter()
router.register(r'', WebAutomationViewSet, basename='web-auto')

urlpatterns = [
    path('', include(router.urls)),
]
