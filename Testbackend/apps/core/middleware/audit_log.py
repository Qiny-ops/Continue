"""
审计日志中间件

记录敏感操作的审计日志。
"""

import json
import logging
from pathlib import Path


class AuditLogMiddleware:
    """审计日志中间件"""

    SENSITIVE_PATHS = [
        '/api/admin/',
        '/api/projects/',
        '/api/users/',
        '/api/permissions/',
        '/api/members/',
        '/api/roles/',
    ]

    SENSITIVE_METHODS = ['DELETE', 'PUT', 'PATCH']

    SENSITIVE_KEYWORDS = [
        'permission',
        'role',
        'member',
        'status',
        'activate',
        'deactivate',
        'delete',
        'remove',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        log_dir = Path(__file__).resolve().parent.parent.parent.parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('audit_logger')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(
                log_dir / 'audit.log',
                encoding='utf-8'
            )
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def __call__(self, request):
        response = self.get_response(request)
        self._log_if_sensitive(request, response)
        return response

    def _log_if_sensitive(self, request, response):
        if not self._is_sensitive_operation(request):
            return

        user_info = self._get_user_info(request)
        client_ip = self._get_client_ip(request)
        request_body = self._get_request_body(request)

        log_data = {
            'user': user_info,
            'ip': client_ip,
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET) if request.GET else None,
            'request_body': request_body,
            'status_code': response.status_code,
            'operation_type': self._get_operation_type(request),
        }

        log_message = (
            f"用户: {user_info} | "
            f"IP: {client_ip} | "
            f"方法: {request.method} | "
            f"路径: {request.path} | "
            f"操作类型: {log_data['operation_type']} | "
            f"状态码: {response.status_code}"
        )

        if request_body:
            log_message += f" | 请求体: {request_body}"

        if response.status_code >= 400:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def _is_sensitive_operation(self, request):
        if request.method in self.SENSITIVE_METHODS:
            for sensitive_path in self.SENSITIVE_PATHS:
                if request.path.startswith(sensitive_path):
                    return True

        path_lower = request.path.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in path_lower:
                if request.method in self.SENSITIVE_METHODS:
                    return True

        if request.method == 'DELETE':
            return True

        return False

    def _get_user_info(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"{request.user.username}(id={request.user.id})"
        return 'Anonymous'

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _get_request_body(self, request):
        try:
            # 对于 DRF 请求，尝试从 request.data 获取
            if hasattr(request, 'data') and request.data:
                body = dict(request.data) if isinstance(request.data, dict) else request.data
                sensitive_fields = ['password', 'token', 'secret', 'key']
                for field in sensitive_fields:
                    if field in body:
                        body[field] = '******'
                return body
            # 尝试从 request.body 获取
            if request.body:
                body = json.loads(request.body.decode('utf-8'))
                sensitive_fields = ['password', 'token', 'secret', 'key']
                for field in sensitive_fields:
                    if field in body:
                        body[field] = '******'
                return body
        except json.JSONDecodeError:
            return None
        except UnicodeDecodeError:
            return None
        except Exception as e:
            self.logger.debug(f"Error parsing request body: {e}")
            return None

    def _get_operation_type(self, request):
        method = request.method
        path = request.path.lower()

        if method == 'DELETE':
            if 'member' in path:
                return '成员删除'
            elif 'project' in path:
                return '项目删除'
            elif 'user' in path:
                return '用户删除'
            elif 'permission' in path or 'role' in path:
                return '权限删除'
            return '数据删除'

        elif method in ['PUT', 'PATCH']:
            if 'permission' in path or 'role' in path:
                return '权限变更'
            elif 'member' in path:
                return '成员管理'
            elif 'status' in path or 'activate' in path or 'deactivate' in path:
                return '状态变更'
            elif 'user' in path:
                return '用户信息修改'
            elif 'project' in path:
                return '项目修改'
            return '数据修改'

        return '敏感操作'
