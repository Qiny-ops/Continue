"""
自定义 DRF 异常处理器

统一处理所有业务异常与 CORS 头追加。
将原来散落在各视图中的 `if '不存在' in error: code=404 else...` 中文子串判码逻辑
全部收口到此处：service 层抛出 BaseAPIException → handler 自动映射 HTTP 状态码。
"""
import logging

from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.response import Response

from apps.core.exceptions import BaseAPIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器

    优先级：
    1. 业务异常（BaseAPIException）→ 返回统一 {error, code, data} 响应体
    2. DRF 标准异常（ValidationError/PermissionDenied 等）→ DRF 默认处理
    3. 未处理异常 → 500，打日志
    """

    # ---- 1. 业务异常 ----
    if isinstance(exc, BaseAPIException):
        from apps.core.response import StandardResponse
        response = StandardResponse(
            data=exc.data,
            message=exc.message,
            code=exc.status,
            status=exc.status,
        )
        _add_cors_headers(response, context)
        return response

    # ---- 2. DRF 标准异常 ----
    response = exception_handler(exc, context)

    if response is not None:
        _add_cors_headers(response, context)
        return response

    # ---- 3. 未预期异常 ----
    logger.error(
        '未处理的异常: %s', str(exc),
        exc_info=True,
        extra={'view': context.get('view', None)},
    )
    # 返回通用 500，避免 Django DEBUG 页面在生产泄露堆栈
    return Response(
        {'error': '服务器内部错误', 'code': 500},
        status=500,
    )


def _add_cors_headers(response, context):
    """为响应追加 CORS 白名单头（仅允许已配置的来源）"""
    from apps.core.utils.cors import get_safe_cors_origin

    request = context.get('request')
    origin = get_safe_cors_origin(request) if request else ''

    if origin:
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
