# -*- coding: utf-8 -*-
"""
Webhook 验签与解析（GitHub / GitLab）
"""
import hashlib
import hmac
import json
from typing import Any, Dict, Optional, Tuple

from app.config import settings


# ==================== 验签 ====================

def verify_github_signature(secret: str, signature_header: str, body: bytes) -> bool:
    if not secret or not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def verify_gitlab_token(token: str, header_value: str) -> bool:
    if not token or not header_value:
        return False
    return hmac.compare_digest(token, header_value)


# ==================== Payload 解析 ====================

def parse_github_push(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ref = payload.get("ref") or ""
    branch = ref.split("/")[-1] if ref.startswith("refs/heads/") else ""
    if not branch:
        return None
    repo = (payload.get("repository") or {}).get("full_name", "")
    clone_url = (payload.get("repository") or {}).get("clone_url", "")
    return {
        "repo_ref": repo,
        "branch": branch,
        "before": payload.get("before", ""),
        "after": payload.get("after", ""),
        "repository_url": clone_url,
    }


def parse_gitlab_push(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ref = payload.get("ref") or ""
    branch = ref.split("/")[-1] if ref.startswith("refs/heads/") else ""
    if not branch:
        return None
    proj = payload.get("project") or {}
    repo_ref = str(proj.get("id", ""))
    return {
        "repo_ref": repo_ref,
        "branch": branch,
        "before": payload.get("before", ""),
        "after": payload.get("after") or payload.get("checkout_sha", ""),
        "repository_url": proj.get("git_http_url") or proj.get("http_url") or "",
    }


# ==================== 分支/仓库过滤 ====================

def match_repo(repo_ref: str) -> Optional[Dict[str, Any]]:
    """返回该 repo 的配置项；空表示未配置"""
    cfg = settings.webhook_repo_map.get(repo_ref)
    return cfg if isinstance(cfg, dict) else None


def is_branch_allowed(repo_cfg: Optional[Dict[str, Any]], branch: str) -> bool:
    if not repo_cfg:
        # 未配置该 repo：检查全局 watch_branches
        if not settings.watch_branch_list:
            return False
        return branch in settings.watch_branch_list

    branches = repo_cfg.get("branches") or []
    if isinstance(branches, str):
        branches = [b.strip() for b in branches.split(",") if b.strip()]
    if branches:
        return branch in branches
    # 仓库配置了但无 branches：回退到全局
    return branch in settings.watch_branch_list if settings.watch_branch_list else False
