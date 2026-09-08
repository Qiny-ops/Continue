# -*- coding: utf-8 -*-
"""
Pydantic 配置（对齐 ai-generator-service 规范）
"""
import json
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Code Check Service"
    app_version: str = "1.0.0"
    debug: bool = False

    # ---- 安全 ----
    # API_KEY: 任务/查询类路由强制校验；为空 = 开发模式放行
    api_key: str = ""
    # INTERNAL_API_KEY: 仅 Django 内部用例接口使用
    internal_api_key: str = ""

    # ---- 端口/并发/重试/超时（课程要求） ----
    host: str = "0.0.0.0"
    port: int = 8004
    concurrency: int = Field(default=3, ge=1)
    max_retries: int = Field(default=3, ge=0)
    timeout: int = Field(default=300, ge=1)
    request_interval: float = Field(default=1.0, ge=0.0, description="模型请求间最小间隔（秒）")

    # ---- 文件路径 ----
    workspaces_dir: str = "./workspaces"
    test_cases_dir: str = "./test_cases"
    data_dir: str = "./data"
    allowed_root_paths: List[str] = Field(default_factory=list)

    # ---- Webhook ----
    # 全局监听分支（逗号分隔）；空表示依赖 webhook_repos 逐仓配置
    watch_branches: str = ""
    # JSON 字符串：{repo_full_name: {branches, case_source, project_code, gate:{provider,token}}}
    webhook_repos: str = ""
    github_webhook_secret: str = ""
    gitlab_webhook_token: str = ""

    # ---- Git 平台调用（Commit Status 上报） ----
    gitlab_base_url: str = "https://gitlab.com"
    # 全局 status token（按仓库覆盖）
    github_status_token: str = ""
    gitlab_status_token: str = ""

    # ---- 平台（Django） ----
    django_base_url: str = "http://localhost:8000"
    frontend_report_base_url: str = "http://localhost:5173"

    # ---- 风险策略 ----
    # 风险等级 ≥ 该值直接阻断；可选 "高"/"中"/"低"
    risk_block_level: str = "高"

    # ---- CORS ----
    cors_allowed_origins: List[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def watch_branch_list(self) -> List[str]:
        return [b.strip() for b in self.watch_branches.split(",") if b.strip()]

    @property
    def webhook_repo_map(self) -> dict:
        if not self.webhook_repos.strip():
            return {}
        try:
            return json.loads(self.webhook_repos)
        except json.JSONDecodeError:
            return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
