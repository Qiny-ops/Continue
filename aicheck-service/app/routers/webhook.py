# -*- coding: utf-8 -*-
"""Webhook 路由（不带 X-API-Key 鉴权，走验签）"""
import json
import logging

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import settings
from app.schemas.task import TriggerRequest, WebhookResponse
from app.services.webhook_service import (
    is_branch_allowed, match_repo, parse_github_push, parse_gitlab_push,
    verify_github_signature, verify_gitlab_token,
)

logger = logging.getLogger("Webhook")
router = APIRouter(tags=["webhook"])


@router.post("/webhook/github", response_model=WebhookResponse, status_code=202)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    if x_github_event != "push":
        return WebhookResponse(ignored=True, reason=f"ignored event: {x_github_event}")

    body = await request.body()
    if not verify_github_signature(settings.github_webhook_secret, x_hub_signature_256 or "", body):
        raise HTTPException(401, "GitHub 签名校验失败")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "payload 非 JSON")

    info = parse_github_push(payload)
    if not info:
        return WebhookResponse(ignored=True, reason="payload 缺少必要字段")

    return await _dispatch(
        request, info, default_gate={"provider": "github", "repo_ref": info["repo_ref"]}
    )


@router.post("/webhook/gitlab", response_model=WebhookResponse, status_code=202)
async def gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(None, alias="X-Gitlab-Event"),
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token"),
):
    if x_gitlab_event and x_gitlab_event != "Push Hook":
        return WebhookResponse(ignored=True, reason=f"ignored event: {x_gitlab_event}")
    if not verify_gitlab_token(settings.gitlab_webhook_token, x_gitlab_token or ""):
        raise HTTPException(401, "GitLab Token 校验失败")

    body = await request.body()
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "payload 非 JSON")
    if payload.get("object_kind") != "push":
        return WebhookResponse(ignored=True, reason="object_kind != push")

    info = parse_gitlab_push(payload)
    if not info:
        return WebhookResponse(ignored=True, reason="payload 缺少必要字段")

    return await _dispatch(
        request, info, default_gate={"provider": "gitlab", "repo_ref": info["repo_ref"]}
    )


async def _dispatch(request: Request, info: dict, default_gate: dict) -> WebhookResponse:
    repo_cfg = match_repo(info["repo_ref"])
    if not is_branch_allowed(repo_cfg, info["branch"]):
        return WebhookResponse(
            ignored=True,
            reason=f"分支 {info['branch']} 不在监听范围（repo={info['repo_ref']}）",
        )

    # 用例来源默认 inline（repo_cfg 可覆盖）
    case_source = (repo_cfg or {}).get("case_source", "platform")
    project_code = (repo_cfg or {}).get("project_code", "")
    case_source = case_source if case_source in ("inline", "file", "platform") else "platform"

    if case_source == "platform" and not project_code:
        return WebhookResponse(
            ignored=True,
            reason="Webhook repo 配置缺少 project_code（platform 模式必填）",
        )

    gate_cfg = (repo_cfg or {}).get("gate") or {}
    gate_info = {
        "provider": gate_cfg.get("provider") or default_gate["provider"],
        "repo_ref": gate_cfg.get("repo_ref") or default_gate["repo_ref"],
        "commit_sha": info.get("after") or "",
        "token": gate_cfg.get("token", ""),
    }

    req = TriggerRequest(
        project_name=info["repo_ref"].replace("/", "_"),
        repository_url=info["repository_url"],
        branch=info["branch"],
        commit_sha=info.get("after") or "",
        case_source=case_source,
        project_code=project_code,
        test_case_file=(repo_cfg or {}).get("test_case_file", ""),
        gate=__import__("app.schemas.task", fromlist=["GateRequest"]).GateRequest(**gate_info)
        if gate_info["provider"] in ("github", "gitlab")
        else None,
        trigger_source="webhook",
    )
    mgr = request.app.state.task_manager
    report = mgr.create_task(req)
    return WebhookResponse(task_id=report.task_id, ignored=False, reason="task created")
