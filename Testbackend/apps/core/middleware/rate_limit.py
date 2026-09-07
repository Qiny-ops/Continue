"""
请求频率限制中间件

限制客户端请求频率，防止滥用。
包含针对登录接口的独立限流策略，防止暴力破解。
"""

import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings


class RateLimitMiddleware:
    """请求频率限制中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        # 开发环境也需合理限流，防止误配 DEBUG=True 时无有效防护
        if settings.DEBUG:
            self.rate_limit = 200  # 每分钟最多200次请求
            self.auth_rate_limit = 600  # 认证用户每分钟最多600次请求
        else:
            self.rate_limit = 60  # 每分钟最多60次请求
            self.auth_rate_limit = 300  # 认证用户每分钟最多300次请求

        self.window_seconds = 60
        # 登录失败限流（防止暴力破解）
        self.login_max_attempts = 20  # 每分钟最多20次登录尝试
        self.login_lockout_duration = 60  # 锁定1分钟
        self.login_tracking_window = 60  # 统计窗口60秒

        self.exempt_paths = [
            '/static/',
            '/media/',
            '/health/',
            '/admin/jsi18n/',
        ]

        # 登录相关路径（需要特殊限流）
        self.login_paths = [
            '/api/users/login/',
            '/api/users/register/',
        ]

    def __call__(self, request):
        if self._is_exempt(request.path):
            return self.get_response(request)

        # 登录接口特殊限流处理
        if request.path in self.login_paths and request.method == 'POST':
            return self._handle_login_rate_limit(request)

        # 认证用户限流
        # 注意：需要确保 AuthenticationMiddleware 已经处理过 request.user
        # JWT 认证通过 DRF 的 authentication_classes 处理，不在中间件层面
        # 所以这里主要检查 session 认证的用户
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            cache_key = f'rate_limit_user_{request.user.id}'
            request_count = cache.get(cache_key, 0)

            if request_count >= self.auth_rate_limit:
                return JsonResponse(
                    {'code': 429, 'message': '请求过于频繁，请稍后再试'},
                    status=429
                )

            cache.set(cache_key, request_count + 1, self.window_seconds)

        # 非认证用户或 API 请求（JWT 认证）
        # 对于 API 请求，使用 IP 限流，但阈值更宽松
        if request.path.startswith('/api/'):
            client_ip = self._get_client_ip(request)
            cache_key = f'rate_limit_api_{client_ip}'

            request_count = cache.get(cache_key, 0)

            # API 请求使用更高的限流阈值
            api_rate_limit = self.auth_rate_limit if settings.DEBUG else 200

            if request_count >= api_rate_limit:
                return JsonResponse(
                    {'code': 429, 'message': '请求过于频繁，请稍后再试'},
                    status=429
                )

            cache.set(cache_key, request_count + 1, self.window_seconds)

        return self.get_response(request)

    def _handle_login_rate_limit(self, request):
        """处理登录接口的限流（防止暴力破解）"""
        client_ip = self._get_client_ip(request)

        # 检查是否被锁定
        lockout_key = f'login_lockout_{client_ip}'
        lockout_until = cache.get(lockout_key)
        if lockout_until:
            remaining_time = int(lockout_until - time.time())
            if remaining_time > 0:
                return JsonResponse(
                    {
                        'code': 429,
                        'message': f'登录尝试过多，请等待 {remaining_time} 秒后再试',
                        'lockout_remaining': remaining_time
                    },
                    status=429
                )
            else:
                # 锁定已过期，清除锁定状态
                cache.delete(lockout_key)

        # 统计登录尝试次数
        attempts_key = f'login_attempts_{client_ip}'
        attempts = cache.get(attempts_key, 0)

        if attempts >= self.login_max_attempts:
            # 达到最大尝试次数，锁定账户
            cache.set(lockout_key, time.time() + self.login_lockout_duration, self.login_lockout_duration)
            # 清除尝试计数
            cache.delete(attempts_key)
            return JsonResponse(
                {
                    'code': 429,
                    'message': f'登录尝试过多，账户已被锁定 {self.login_lockout_duration // 60} 分钟',
                    'lockout_duration': self.login_lockout_duration
                },
                status=429
            )

        # 允许请求，增加尝试计数
        cache.set(attempts_key, attempts + 1, self.login_tracking_window)

        response = self.get_response(request)

        # 如果登录成功，清除尝试计数
        if response.status_code == 200:
            cache.delete(attempts_key)

        return response

    def _is_exempt(self, path):
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
