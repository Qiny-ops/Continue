#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理

模型 API / 推理参数 / 重试 / 服务元信息 / CORS 全量定义于本文件，
服务间零共享依赖，可独立演进。
"""
from functools import lru_cache
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API Testing Service 配置"""

    # ---- 模型 API 配置 ----
    model_api_key: str = "EMPTY"
    # 模型服务地址：禁止硬编码内网 IP，统一由环境变量 MODEL_BASE_URL 注入
    model_base_url: str = "http://localhost:8000/v1"

    # ---- 推理参数（带范围约束，避免非法值破坏 JSON 稳定性） ----
    max_tokens: int = Field(default=81920, gt=0)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    presence_penalty: float = Field(default=1.5, ge=-2.0, le=2.0)
    top_k: int = Field(default=20, ge=1)

    # ---- 重试配置 ----
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=2.0, ge=0.0)

    # ---- 服务元信息 ----
    app_name: str = "API Testing Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # ---- 安全配置（CORS） ----
    cors_allowed_origins: List[str] = Field(default_factory=list)

    # ---- 模型名称 ----
    model_name: str = "default"

    # ---- 知识库服务配置（WeKnora） ----
    kb_base_url: str = "http://localhost:3000/api/v1"
    kb_id: str = ""
    kb_api_key: str = ""

    # ---- Agent 配置 ----
    kb_agent_id: str = "builtin-smart-reasoning"
    kb_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    kb_max_tokens: int = Field(default=8192, gt=0)

    # ---- 数据库配置 ----
    db_enabled: bool = False
    db_host: str = "localhost"
    db_port: int = Field(default=3306, gt=0)
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "test"

    # ---- API 测试执行配置 ----
    api_base_url: str = "http://127.0.0.1:8000"

    # ---- 安全配置 ----
    api_key: str = ""
    internal_api_key: str = ""
    block_private_targets: bool = False

    # ---- 测试账号配置 ----
    admin_username: str = ""
    admin_password: str = ""

    # ---- 其他预设测试账号（可选） ----
    test_accounts: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
