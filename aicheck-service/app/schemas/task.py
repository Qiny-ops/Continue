# -*- coding: utf-8 -*-
"""
任务相关 Pydantic Schema

用例/结果统一为 case_no/testpoint/steps/expectation；case_provider 负责从
Excel/Inline/Platform 三态归一化。
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ==================== 用例与结果 ====================

class TestCaseItem(BaseModel):
    case_no: str = ""
    testpoint: str = ""
    steps: str = ""
    expectation: str = ""


class CheckResultItem(BaseModel):
    case_no: str = ""
    testpoint: str = ""
    result: str = ""  # "通过" | "失败" | "异常" | "解析失败"
    reason: str = ""
    success: bool = False
    # 当次用例原文快照：用例后续被修改时，历史报告仍有据可查
    steps: str = ""
    expectation: str = ""
    # 结构化失败信息：供审计报告直接引用「为什么失败」
    failure_type: str = ""    # 功能未实现 / 实现与预期不符 / ... / 校验执行异常
    failure_reason: str = ""  # 一句话失败原因
    evidence: str = ""        # 证据位置，如 src/views/Login.vue:119


class DiffInfo(BaseModel):
    changed_files: List[str] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    full_diff: str = ""
    commit_before: str = ""
    commit_after: str = ""
    summary: str = ""


class RiskInfo(BaseModel):
    level: str = "未知"  # "高" | "中" | "低" | "未知"
    score: int = 0
    high_risk_files: List[str] = Field(default_factory=list)
    reason: str = ""


class SummaryInfo(BaseModel):
    total: int = 0
    pass_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    pass_rate: str = "0%"


class GateInfo(BaseModel):
    provider: str = ""  # "github" | "gitlab" | ""
    repo_ref: str = ""
    commit_sha: str = ""
    state: str = "pending"  # pending | success | failure


# ==================== 触发请求 ====================

class GateRequest(BaseModel):
    provider: Literal["github", "gitlab"]
    repo_ref: str = Field("", description="GitHub: owner/repo；GitLab: project_id 数字")
    commit_sha: str = ""
    token: str = ""  # 覆盖全局；为空时取 settings 默认


class TriggerRequest(BaseModel):
    project_name: str
    repository_url: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    base_sha: Optional[str] = None  # 留空时与 commit_sha 相同（无 diff）

    # 三种用例来源，三选一（由 case_source 决定）
    case_source: Literal["inline", "file", "platform"] = "inline"
    test_cases: List[TestCaseItem] = Field(default_factory=list)
    test_case_file: str = ""
    project_code: str = ""  # case_source=platform 时使用

    # 可选：触发后上报 Commit Status
    gate: Optional[GateRequest] = None

    # 来源标记（用于审计）
    trigger_source: Literal["manual", "webhook"] = "manual"


# ==================== 任务报告 ====================

class TaskReport(BaseModel):
    task_id: str
    project_name: str = ""
    repository_url: str = ""
    branch: str = ""
    commit_sha: str = ""

    status: str = "pending"  # pending | running | completed | failed
    progress: str = ""

    trigger_source: str = "manual"
    case_source: str = "inline"
    test_case_file: str = ""

    # 结果数据
    diff: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None

    # 终态结论与门禁
    conclusion: str = ""  # passed | blocked | failed
    gate: Optional[Dict[str, Any]] = None

    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


# ==================== 列表 ====================

class TaskSummary(BaseModel):
    task_id: str
    project_name: str
    status: str
    progress: str = ""
    conclusion: str = ""
    risk_level: str = ""
    created_at: str = ""


class TaskListResponse(BaseModel):
    tasks: List[TaskSummary]


class TriggerResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = ""


class WebhookResponse(BaseModel):
    ignored: bool = False
    reason: str = ""
    task_id: str = ""
