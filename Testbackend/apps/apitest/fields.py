# -*- coding: utf-8 -*-
"""
对称加密模型字段（基于 cryptography.fernet.Fernet）

用于 ApiEnvironment 的认证凭据（auth_token / auth_username / auth_password），
保证落库为密文，读取时自动解密。序列化层仍额外脱敏，双重防护。

密钥来源（apps/apitest 的 settings.DB_FIELD_ENCRYPTION_KEY）：
- 若配置为合法的 Fernet key（44 字节 urlsafe base64），直接使用；
- 否则由该字符串（或 SECRET_KEY）经 SHA-256 确定性派生，保证无环境变量时也能启动（仅开发可用）。
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _build_fernet_key():
    """构造合法的 Fernet key：优先使用配置值，否则由字符串派生。"""
    raw = getattr(settings, 'DB_FIELD_ENCRYPTION_KEY', '') or settings.SECRET_KEY
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    # 若已是合法 Fernet key，直接使用
    try:
        Fernet(raw)
        return raw
    except Exception:
        pass
    # 否则由原始材料派生 32 字节 urlsafe base64 key
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_build_fernet_key())


def is_ciphertext(value):
    """判断数据库原始值是否已是密文（可成功解密）。"""
    if not value:
        return False
    if isinstance(value, str):
        value = value.encode('utf-8')
    try:
        _fernet.decrypt(value)
        return True
    except (InvalidToken, ValueError):
        return False


def encrypt_value(value):
    if value is None or value == '':
        return value
    if isinstance(value, str):
        value = value.encode('utf-8')
    return _fernet.encrypt(value).decode('utf-8')


def decrypt_value(value):
    if value is None or value == '':
        return value
    if isinstance(value, str):
        value = value.encode('utf-8')
    try:
        return _fernet.decrypt(value).decode('utf-8')
    except (InvalidToken, ValueError):
        # 兼容迁移前的明文历史数据
        return value.decode('utf-8') if isinstance(value, bytes) else value


class EncryptedFieldMixin:
    """在 DB 读写边界加解密，对 ORM / 序列化层透明。"""

    def get_prep_value(self, value):
        # 写入前加密（空值透传）
        if value is None or value == '':
            return value
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        # 读出时解密（兼容明文历史数据）
        return decrypt_value(value)

    def to_python(self, value):
        # DRF / 表单校验路径：已是明文则直接返回，密文则解密
        if value is None:
            return value
        return decrypt_value(value)


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    pass


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    pass
