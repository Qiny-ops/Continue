#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理
使用 pydantic-settings 管理服务配置
"""

from typing import Optional, Dict
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """服务配置"""

    # 服务配置
    app_name: str = "API Testing Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # 模型 API 配置
    model_api_key: str = "EMPTY"
    model_base_url: str = "http://localhost:8000/v1"
    model_name: str = "default"

    # 推理参数
    max_tokens: int = 81920
    temperature: float = 1.0
    top_p: float = 0.95
    presence_penalty: float = 1.5
    top_k: int = 20

    # 重试配置
    max_retries: int = 3
    retry_delay: float = 2.0

    # 知识库服务配置（WeKnora）
    kb_base_url: str = "http://localhost:3000/api/v1"
    kb_id: str = ""
    kb_api_key: str = ""

    # Agent 配置
    kb_agent_id: str = "builtin-smart-reasoning"
    kb_temperature: float = 0.3
    kb_max_tokens: int = 8192

    # 数据库配置
    db_enabled: bool = False
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "test"

    # API 测试执行配置
    api_base_url: str = "http://127.0.0.1:8000"  # 被 API 的默认基座 URL

    # 测试账号配置
    # 管理员账号（用于需要管理员权限的测试）
    admin_username: str = ""
    admin_password: str = ""

    # 其他预设测试账号（可选）
    test_accounts: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
