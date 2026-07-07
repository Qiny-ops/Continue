"""
Service 基类

提供业务逻辑层的抽象基类。
所有具体的 Service 类应继承此基类。
"""

from typing import Tuple, Any


class BaseService:
    """
    Service 基类

    业务逻辑层，负责处理复杂的业务规则和流程。
    Service 调用 Repository 进行数据操作，但不直接访问数据库。

    使用示例:
        class UserService(BaseService):
            repository = UserRepository

            def register(self, username, email, password):
                # 业务逻辑：验证、创建用户、发送邮件等
                if self.repository.exists({'username': username}):
                    return None, '用户名已存在'

                user = self.repository.create(
                    username=username,
                    email=email,
                    password=password
                )
                return user, None
    """

    repository = None  # 子类可指定关联的 Repository

    @classmethod
    def success(cls, data: Any = None, message: str = None) -> Tuple[Any, str]:
        """返回成功结果"""
        return data, message

    @classmethod
    def error(cls, message: str) -> Tuple[Any, str]:
        """返回错误结果"""
        return None, message