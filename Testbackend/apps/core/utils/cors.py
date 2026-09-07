"""CORS 安全辅助。

集中处理跨域来源校验，避免在各视图中手写 `Access-Control-Allow-Origin`
并直接回显客户端请求头里的 Origin（Origin 反射漏洞）。
"""
from django.conf import settings


def get_safe_cors_origin(request):
    """返回安全的 CORS 来源。

    仅当请求 Origin 在 `settings.CORS_ALLOWED_ORIGINS` 白名单内时才原样返回，
    否则返回空字符串（浏览器会因缺少 ACAO 头而拒绝），绝不回显任意来源。
    """
    if request is None:
        return ""

    origin = request.META.get("HTTP_ORIGIN")
    allowed = set(getattr(settings, "CORS_ALLOWED_ORIGINS", []))
    if origin and origin in allowed:
        return origin
    return ""
