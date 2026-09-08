# -*- coding: utf-8 -*-
"""任务触发/查询 API"""
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.schemas.task import (
    TaskListResponse, TaskReport, TaskSummary, TriggerRequest, TriggerResponse,
)

router = APIRouter(tags=["tasks"])


@router.post("/check/trigger", response_model=TriggerResponse, status_code=202)
async def trigger(req: TriggerRequest, request: Request):
    mgr = request.app.state.task_manager
    if req.case_source == "inline" and not req.test_cases:
        raise HTTPException(400, "case_source=inline 时 test_cases 必填")
    if req.case_source == "file" and not req.test_case_file:
        raise HTTPException(400, "case_source=file 时 test_case_file 必填")
    if req.case_source == "platform" and not req.project_code:
        raise HTTPException(400, "case_source=platform 时 project_code 必填")
    if not req.project_name or not req.repository_url:
        raise HTTPException(400, "project_name / repository_url 必填")
    report = mgr.create_task(req)
    return TriggerResponse(
        task_id=report.task_id, status="pending",
        message="任务已创建，请使用 GET /api/v1/check/{task_id} 查询进度",
    )


@router.get("/checks", response_model=TaskListResponse)
async def list_tasks(request: Request):
    mgr = request.app.state.task_manager
    summaries: List[TaskSummary] = []
    for r in mgr.store.list():
        risk = r.risk or {}
        summaries.append(TaskSummary(
            task_id=r.task_id, project_name=r.project_name,
            status=r.status, progress=r.progress, conclusion=r.conclusion,
            risk_level=risk.get("level", ""), created_at=r.created_at,
        ))
    return TaskListResponse(tasks=summaries)


@router.get("/check/{task_id}", response_model=TaskReport)
async def get_task(task_id: str, request: Request):
    mgr = request.app.state.task_manager
    report = mgr.store.get(task_id)
    if not report:
        raise HTTPException(404, f"任务不存在: {task_id}")
    return report
