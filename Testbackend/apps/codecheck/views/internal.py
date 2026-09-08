# -*- coding: utf-8 -*-
"""
内部接口（供 aicheck-service 在 Webhook 触发时回调拉取平台用例）

鉴权：X-Internal-API-Key 与 settings.AICHECK_INTERNAL_API_KEY 一致
"""
import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.codecheck.services.codecheck_service import get_platform_cases

logger = logging.getLogger(__name__)


class InternalCasesView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        expected = getattr(settings, "AICHECK_INTERNAL_API_KEY", "")
        provided = request.headers.get("X-Internal-API-Key", "")
        if not expected or provided != expected:
            raise PermissionDenied("内部接口鉴权失败")
        project_code = request.query_params.get("project_code", "").strip()
        if not project_code:
            raise ValidationError("project_code 必填")
        data = get_platform_cases(project_code)
        return Response({"data": data, "total": len(data)})
