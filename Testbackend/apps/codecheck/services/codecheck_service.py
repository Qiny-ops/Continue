# -*- coding: utf-8 -*-
"""
代码检查 Service 层（Repository/Service/View 分层）

- trigger: 拉取平台默认版本用例 → 调微服务 → 创建 CodeCheckTask
- sync_task: 拉微服务最新报告回写 CodeCheckTask + results
- list_tasks: 列表查询
- retrieve_task: 详情查询（自动 sync）
- list_platform_cases: 微服务 Webhook 触发时拉用例（内部接口使用）
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils import timezone

from apps.codecheck.clients import AiCheckClient, AiCheckServiceError
from apps.codecheck.models import CodeCheckTask, CodeCheckResult
from apps.projects.models import Project
from apps.testcase.models import TestCaseRepository, TestCaseVersion, TestCase

logger = logging.getLogger(__name__)


# 风险等级 / 结论映射
_RISK_LEVEL_MAP = {
    "高": "高", "中": "中", "低": "低", "未知": "未知", "": "",
}

_CONCLUSION_MAP = {
    "passed": "passed",
    "blocked": "blocked",
    "failed": "failed",
    "completed": "",
}


# ==================== 用例拉取 ====================

def get_platform_cases(project_code: str) -> List[Dict[str, Any]]:
    """按 project_code 拉取默认库的活跃版本下的全部用例"""
    project = Project.objects.filter(code=project_code).first()
    if not project:
        return []
    repo = TestCaseRepository.objects.filter(project=project, is_default=True).first()
    if not repo:
        return []
    version = (
        TestCaseVersion.objects.filter(repository=repo, status="active")
        .order_by("-id").first()
    )
    if not version:
        return []
    cases = TestCase.objects.filter(version=version).order_by("id")
    return [
        {
            "case_no": f"TC{c.id:04d}",
            "testpoint": c.title or "",
            "steps": c.steps or "",
            "expectation": c.expected_result or "",
        }
        for c in cases
    ]


# ==================== 触发 ====================

@transaction.atomic
def trigger_task(
    project: Project,
    repository_url: str,
    branch: str = "",
    commit_sha: str = "",
    case_source: str = "platform",
    project_code: str = "",
    test_case_file: str = "",
    gate: Optional[Dict[str, Any]] = None,
    trigger_source: str = "manual",
    user=None,
) -> CodeCheckTask:
    """触发代码检查并创建任务记录

    case_source 决策：
      - platform: 从平台默认库拉用例，inline 传给微服务
      - inline  : 平台不做用例提供（基本不会用，保留兼容）
      - file    : 直接把文件名传微服务
    """
    client = AiCheckClient()
    cases_for_inline: List[Dict[str, Any]] = []
    if case_source == "platform":
        project_code = project_code or project.code
        cases_for_inline = get_platform_cases(project_code)
        if not cases_for_inline:
            raise ValueError(f"项目 {project_code} 未配置默认用例库/活跃版本/任何用例")
        case_source = "inline"  # 转 inline 传给微服务，避免 webhook 模式下再次回调
        trigger_payload_cases = cases_for_inline
    elif case_source == "inline":
        trigger_payload_cases = []  # 平台无内联用例，触发侧另传
    else:  # file
        trigger_payload_cases = []

    result = client.trigger(
        project_name=project.name,
        repository_url=repository_url,
        test_cases=trigger_payload_cases,
        branch=branch,
        commit_sha=commit_sha,
        case_source=case_source,
        project_code=project_code,
        gate=gate,
        trigger_source=trigger_source,
    )
    task = CodeCheckTask.objects.create(
        project=project,
        project_name=project.name,
        repository_url=repository_url,
        branch=branch or "",
        commit_sha=commit_sha or "",
        service_task_id=result.get("task_id", ""),
        trigger_source=trigger_source,
        case_source="platform" if (project_code or test_case_file == "") and case_source == "inline" else case_source,
        test_case_file=test_case_file,
        status="pending",
        progress="任务已派发到微服务",
        gate_provider=(gate or {}).get("provider", ""),
        created_by=user,
    )
    return task


# ==================== 回写 ====================

def sync_task(task: CodeCheckTask) -> CodeCheckTask:
    """从微服务拉取最新报告，写回 CodeCheckTask + 同步 results"""
    client = AiCheckClient()
    try:
        data = client.get_task(task.service_task_id)
    except AiCheckServiceError as e:
        logger.warning(f"sync 拉取失败: {e}")
        return task

    task.status = data.get("status", task.status) or task.status
    task.progress = data.get("progress", "") or ""
    task.conclusion = data.get("conclusion", "") or task.conclusion

    risk = data.get("risk") or {}
    task.risk_level = _RISK_LEVEL_MAP.get(risk.get("level", ""), "")
    try:
        task.risk_score = int(risk.get("score", 0) or 0)
    except (TypeError, ValueError):
        task.risk_score = 0
    task.risk_files = risk.get("high_risk_files", []) or []
    task.risk_reason = risk.get("reason", "") or ""
    task.diff_info = data.get("diff") or {}
    task.summary = data.get("summary") or {}
    task.error = data.get("error", "") or ""

    gate = data.get("gate") or {}
    task.gate_provider = gate.get("provider", "") or task.gate_provider
    task.gate_state = gate.get("state", "") or task.gate_state
    task.gate_response = gate.get("last_response", {}) or {}

    task.save()

    # 同步结果（仅在终态时全量替换）
    if task.status in ("completed", "failed"):
        new_results = data.get("results") or []
        existing = {r.case_no: r for r in task.results.all()}
        seen = set()
        for item in new_results:
            cn = item.get("case_no", "")
            seen.add(cn)
            obj = existing.get(cn)
            if obj is None:
                CodeCheckResult.objects.create(
                    task=task,
                    case_no=cn,
                    testpoint=item.get("testpoint", "") or "",
                    steps=item.get("steps", "") or "",
                    expectation=item.get("expectation", "") or "",
                    result=item.get("result", "未知") or "未知",
                    reason=item.get("reason", "") or "",
                    success=bool(item.get("success", False)),
                )
            else:
                obj.testpoint = item.get("testpoint", "") or obj.testpoint
                obj.result = item.get("result", obj.result) or obj.result
                obj.reason = item.get("reason", "") or obj.reason
                obj.success = bool(item.get("success", obj.success))
                obj.save()
        # 删除已不见的
        for cn, obj in existing.items():
            if cn not in seen:
                obj.delete()
    return task
