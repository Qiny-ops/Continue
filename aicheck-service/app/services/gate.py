# -*- coding: utf-8 -*-
"""
Git 门禁：上报 Commit Status

- GitHub: POST /repos/{owner}/{repo}/statuses/{sha}
- GitLab: POST /projects/{id}/statuses/{sha}
- 上报失败仅记日志，不阻断任务主流程
"""
import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger("Gate")

GITHUB_API = "https://api.github.com"


def _resolve_token(provider: str, override: str = "") -> str:
    if override:
        return override
    if provider == "github":
        return settings.github_status_token
    if provider == "gitlab":
        return settings.gitlab_status_token
    return ""


def _target_url(task_id: str) -> str:
    base = settings.frontend_report_base_url.rstrip("/")
    return f"{base}/codecheck/{task_id}"


async def report_status(
    provider: str,
    repo_ref: str,
    commit_sha: str,
    state: str,
    task_id: str,
    description: str = "",
    token_override: str = "",
) -> Dict[str, Any]:
    """state: pending | success | failure | error"""
    if not provider or provider not in ("github", "gitlab"):
        return {"ok": False, "reason": f"未支持的 provider: {provider}"}
    if not repo_ref or not commit_sha:
        return {"ok": False, "reason": "repo_ref/commit_sha 必填"}

    token = _resolve_token(provider, token_override)
    if not token:
        return {"ok": False, "reason": f"{provider} status token 未配置"}

    headers = {"Accept": "application/vnd.github+json"}
    body: Dict[str, Any] = {
        "state": state,
        "context": "aicheck/code-gate",
        "target_url": _target_url(task_id),
        "description": (description or state)[:140],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if provider == "github":
                url = f"{GITHUB_API}/repos/{repo_ref}/statuses/{commit_sha}"
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.post(url, json=body, headers=headers)
            else:  # gitlab
                url = f"{settings.gitlab_base_url.rstrip('/')}/api/v4/projects/{repo_ref}/statuses/{commit_sha}"
                headers["PRIVATE-TOKEN"] = token
                resp = await client.post(url, json=body, headers=headers)
            return {
                "ok": resp.status_code in (200, 201),
                "status_code": resp.status_code,
                "text": resp.text[:300],
            }
    except Exception as e:
        logger.warning(f"Commit Status 上报失败: {e}")
        return {"ok": False, "reason": str(e)}
