"""
验证器工具

提供常用的数据验证函数。
"""

import re
from typing import Tuple, Optional


class Validators:
    """验证器集合"""

    # 正则表达式模式
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    PASSWORD_MIN_LENGTH = 8

    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """验证邮箱格式"""
        if not email:
            return False, '邮箱不能为空'
        if not cls.EMAIL_PATTERN.match(email):
            return False, '邮箱格式不正确'
        return True, None

    @classmethod
    def validate_phone(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """验证手机号格式"""
        if not phone:
            return True, None  # 手机号可选
        if not cls.PHONE_PATTERN.match(phone):
            return False, '手机号格式不正确'
        return True, None

    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, Optional[str]]:
        """验证用户名格式"""
        if not username:
            return False, '用户名不能为空'
        if len(username) < 3:
            return False, '用户名至少3个字符'
        if len(username) > 20:
            return False, '用户名最多20个字符'
        if not cls.USERNAME_PATTERN.match(username):
            return False, '用户名只能包含字母、数字和下划线'
        return True, None

    # 常见弱密码黑名单（与 PasswordService 保持同步）
    _COMMON_PASSWORDS = [
        'password', 'Password1', 'Password123', 'Admin123', 'Qwer1234',
        'Abcd1234', 'Test1234', 'Welcome1', 'P@ssw0rd', 'Passw0rd'
    ]

    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, Optional[str]]:
        """验证密码强度（与 PasswordService.validate_strength 规则一致）"""
        if not password:
            return False, '密码不能为空'
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f'密码至少{cls.PASSWORD_MIN_LENGTH}个字符'
        if len(password) > 128:
            return False, '密码最多128个字符'
        if not re.search(r'[A-Z]', password):
            return False, '密码必须包含至少一个大写字母'
        if not re.search(r'[a-z]', password):
            return False, '密码必须包含至少一个小写字母'
        if not re.search(r'\d', password):
            return False, '密码必须包含至少一个数字'
        if password.lower() in [p.lower() for p in cls._COMMON_PASSWORDS]:
            return False, '密码过于简单，请使用更复杂的密码'
        return True, None

    @classmethod
    def validate_name(cls, name: str, field_name: str = '名称') -> Tuple[bool, Optional[str]]:
        """验证名称"""
        if not name:
            return False, f'{field_name}不能为空'
        if len(name) > 50:
            return False, f'{field_name}最多50个字符'
        return True, None

    @classmethod
    def validate_id(cls, id_value: str, field_name: str = 'ID') -> Tuple[bool, Optional[str]]:
        """验证ID"""
        if not id_value:
            return False, f'{field_name}不能为空'
        try:
            int(id_value)
        except (ValueError, TypeError):
            return False, f'{field_name}格式不正确'
        return True, None

    @classmethod
    def validate_page_params(cls, page: int, page_size: int, max_page_size: int = 100) -> Tuple[bool, Optional[str]]:
        """验证分页参数"""
        if page < 1:
            return False, '页码必须大于0'
        if page_size < 1:
            return False, '每页数量必须大于0'
        if page_size > max_page_size:
            return False, f'每页数量不能超过{max_page_size}'
        return True, None
