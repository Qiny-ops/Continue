"""
请求体大小限制中间件

限制请求体大小，防止大文件攻击。
"""

from django.conf import settings
from django.http import JsonResponse


class RequestBodyLimitMiddleware:
    """请求体大小限制中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_size = getattr(settings, 'MAX_REQUEST_BODY_SIZE', 10 * 1024 * 1024)
        self.exempt_paths = [
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        if self._is_exempt(request.path):
            return self.get_response(request)

        if request.method in ('POST', 'PUT', 'PATCH'):
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length:
                try:
                    length = int(content_length)
                    if length > self.max_size:
                        return JsonResponse(
                            {'code': 413, 'message': f'请求体大小超过限制，最大允许 {self._format_size(self.max_size)}'},
                            status=413
                        )
                except ValueError:
                    pass

        return self.get_response(request)

    def _is_exempt(self, path):
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _format_size(self, size_bytes):
        if size_bytes >= 1024 * 1024:
            return f'{size_bytes // (1024 * 1024)}MB'
        elif size_bytes >= 1024:
            return f'{size_bytes // 1024}KB'
        return f'{size_bytes}B'
