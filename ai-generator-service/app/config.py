#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理
使用 pydantic-settings 管理服务配置
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """服务配置"""

    # 模型 API 配置
    model_api_key: str = "EMPTY"
    model_base_url: str = "http://120.209.70.202:31389/v1"

    # 推理参数
    max_tokens: int = 81920
    temperature: float = 1.0
    top_p: float = 0.95
    presence_penalty: float = 1.5
    top_k: int = 20

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 2.0

    # 服务配置
    app_name: str = "AI Generator Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # Redis 配置（可选，用于分布式部署）
    redis_url: str = ""
    use_redis: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()