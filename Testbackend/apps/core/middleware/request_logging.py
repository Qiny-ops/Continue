"""
请求日志中间件

记录所有HTTP请求的日志信息。
"""

import time
import logging
from pathlib import Path


class RequestLoggingMiddleware:
    """请求日志中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        log_dir = Path(__file__).resolve().parent.parent.parent.parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(
                log_dir / 'request.log',
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        user_info = 'Anonymous'
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            user_info = f'{user.username}(id={user.id})'

        log_message = (
            f'[{request.method}] {request.path} '
            f'- Status: {response.status_code} '
            f'- Duration: {duration:.3f}s '
            f'- User: {user_info}'
        )
        self.logger.info(log_message)

        return response
