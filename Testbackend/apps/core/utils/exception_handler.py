"""
自定义 DRF 异常处理器

确保所有响应都包含 CORS 头
"""
from django.conf import settings
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    自定义异常处理器

    在 DRF 默认异常处理的基础上，添加 CORS 头
    """
    # 调用 DRF 默认异常处理器
    response = exception_handler(exc, context)

    if response is not None:
        # 添加 CORS 头
        request = context.get('request')
        if request:
            origin = request.META.get('HTTP_ORIGIN', '*')
        else:
            origin = '*'

        # 检查 origin 是否在允许列表中
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if origin in allowed_origins or origin == '*':
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response
