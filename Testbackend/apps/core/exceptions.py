"""
自定义异常类
提供统一的异常处理机制
"""

from rest_framework import status


class BaseAPIException(Exception):
    """API异常基类"""

    default_message = '操作失败'
    default_code = 400
    default_status = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None, status_code=None, data=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status = status_code or self.default_status
        self.data = data or {}
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """验证错误"""

    default_message = '数据验证失败'
    default_code = 400


class AuthenticationError(BaseAPIException):
    """认证错误"""

    default_message = '认证失败'
    default_code = 401
    default_status = status.HTTP_401_UNAUTHORIZED


class PermissionDenied(BaseAPIException):
    """权限拒绝"""

    default_message = '无权限访问'
    default_code = 403
    default_status = status.HTTP_403_FORBIDDEN


class NotFoundError(BaseAPIException):
    """资源不存在"""

    default_message = '资源不存在'
    default_code = 404
    default_status = status.HTTP_404_NOT_FOUND


class DatabaseError(BaseAPIException):
    """数据库错误"""

    default_message = '数据库操作失败'
    default_code = 500
    default_status = status.HTTP_500_INTERNAL_SERVER_ERROR


class BusinessError(BaseAPIException):
    """业务逻辑错误"""

    default_message = '业务处理失败'
    default_code = 400


class RateLimitError(BaseAPIException):
    """请求频率限制"""

    default_message = '请求过于频繁'
    default_code = 429
    default_status = status.HTTP_429_TOO_MANY_REQUESTS


class ServiceError(BaseAPIException):
    """服务层错误

    用于服务层统一抛出的异常，包含业务错误信息
    """

    default_message = '服务处理失败'
    default_code = 400
