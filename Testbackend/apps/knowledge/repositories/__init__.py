"""
知识库模块 - 数据访问层

封装 WeKnora 外部服务的 API 调用，作为数据访问层。
"""

from .weknora_repository import WeKnoraRepository, weknora_repository

__all__ = [
    'WeKnoraRepository',
    'weknora_repository',
]
