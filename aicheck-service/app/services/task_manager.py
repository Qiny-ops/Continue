# -*- coding: utf-8 -*-
"""
任务编排（移植自 checker/api/routes.py::_run_task，async 化）

流程：
  pending → running (拉代码) → (拉 diff) → 风险评估
  → 高风险：直接 conclusion=blocked，跳过用例
  → 中低风险：拉取用例 → 并发校验（实时写库）→ 全部通过则 passed，否则 failed
  → 上报 Commit Status
  → completed | failed
"""
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.task import (
    CheckResultItem, GateInfo, TaskReport, TriggerRequest,
)
from app.services.case_provider import load_file, load_inline, load_platform
from app.services.executor import TestExecutor
from app.services.gate import report_status
from app.services.git_handler import GitError, GitHandler
from app.services.risk_analyzer import RiskAnalyzer
from app.services.task_store import TaskStore

logger = logging.getLogger("TaskManager")

# 风险等级排序（用于比较）
_RISK_ORDER = {"高": 3, "中": 2, "低": 1, "未知": 0}


def _should_block_by_risk(level: str) -> bool:
    cur = _RISK_ORDER.get(level, 0)
    threshold = _RISK_ORDER.get(settings.risk_block_level, 3)
    return cur >= threshold and cur > 0


class TaskManager:
    def __init__(self, store: TaskStore):
        self.store = store
        self._git_locks: Dict[str, asyncio.Lock] = {}

    def _git_lock_for(self, project_name: str) -> asyncio.Lock:
        if project_name not in self._git_locks:
            self._git_locks[project_name] = asyncio.Lock()
        return self._git_locks[project_name]

    # ==================== 入口 ====================

    def create_task(self, req: TriggerRequest) -> TaskReport:
        task_id = str(uuid.uuid4())
        report = TaskReport(
            task_id=task_id,
            project_name=req.project_name,
            repository_url=req.repository_url,
            branch=req.branch or "",
            commit_sha=req.commit_sha or "",
            trigger_source=req.trigger_source,
            case_source=req.case_source,
            test_case_file=req.test_case_file,
            gate=req.gate.model_dump() if req.gate else None,
        )
        self.store.create(report)
        asyncio.create_task(self._run(report.task_id, req))
        return report

    # ==================== 编排 ====================

    async def _run(self, task_id: str, req: TriggerRequest):
        self.store.update(task_id, status="running", progress="开始执行")
        gate_info: Optional[Dict[str, Any]] = req.gate.model_dump() if req.gate else None

        # 任务开始即上报 pending
        if gate_info and gate_info.get("commit_sha"):
            await self._gate_report(task_id, gate_info, "pending", "任务开始")

        try:
            # 1. 拉代码
            self.store.update(task_id, progress="正在拉取代码...")
            git = GitHandler()
            async with self._git_lock_for(req.project_name):
                project_path = await git.clone_or_pull(
                    req.repository_url, req.project_name, branch=req.branch
                )
                if req.commit_sha:
                    try:
                        await git.checkout_commit(project_path, req.commit_sha)
                    except GitError as e:
                        logger.warning(f"checkout 失败（忽略，按当前 HEAD）: {e}")

            # 2. 拉 diff
            self.store.update(task_id, progress="获取代码变更...")
            before_sha = req.base_sha or req.commit_sha or None
            after_sha = req.commit_sha or None
            diff = await git.get_diff(
                project_path, before=before_sha, after=after_sha,
            )
            self.store.update(task_id, diff=diff)

            # 3. 风险评估
            self.store.update(task_id, progress="风险评估中...")
            analyzer = RiskAnalyzer()
            risk = await analyzer.assess(diff, project_path)
            self.store.update(task_id, risk=risk)
            logger.info(f"[{task_id}] 风险评估: {risk.get('level')}({risk.get('score')})")

            # 4. 风险等级阻断
            if _should_block_by_risk(risk.get("level", "未知")):
                conclusion = "blocked"
                summary = {"total": 0, "pass": 0, "fail": 0, "error": 0, "pass_rate": "0%"}
                self.store.update(
                    task_id,
                    progress=f"高风险阻断（{risk.get('level')}）",
                    summary=summary,
                    conclusion=conclusion,
                    status="completed",
                )
                if gate_info:
                    await self._gate_report(task_id, gate_info, "failure",
                                            f"高风险阻断: {risk.get('level')}")
                return

            # 5. 拉取用例
            self.store.update(task_id, progress="加载测试用例...")
            cases: List = await self._load_cases(req)
            if not cases:
                raise ValueError("未加载到任何测试用例")
            self.store.update(task_id, progress=f"已加载 {len(cases)} 个用例，开始校验")

            # 6. 并发校验
            executor = TestExecutor(
                on_result=lambda r: self._on_result(task_id, r)
            )
            results = await executor.execute_all(
                cases, project_path, diff_context=diff.get("full_diff", "")
            )

            # 7. 汇总
            pass_count = sum(1 for r in results if r.success)
            fail_count = sum(1 for r in results if r.result == "失败")
            error_count = sum(1 for r in results if r.result in ("异常", "解析失败", "解析错误", "未知"))
            total = len(results)
            pass_rate = f"{pass_count / total * 100:.1f}%" if total else "0%"
            summary = {
                "total": total, "pass": pass_count,
                "fail": fail_count, "error": error_count, "pass_rate": pass_rate,
            }
            conclusion = "passed" if (fail_count == 0 and error_count == 0 and total > 0) else "failed"
            self.store.update(
                task_id, summary=summary, conclusion=conclusion,
                status="completed", progress="全部完成",
            )
            if gate_info:
                if conclusion == "passed":
                    await self._gate_report(task_id, gate_info, "success", "所有用例通过")
                else:
                    await self._gate_report(task_id, gate_info, "failure",
                                            f"{fail_count + error_count} 条未通过")

        except Exception as e:
            logger.exception(f"[{task_id}] 任务失败: {e}")
            self.store.update(
                task_id, status="failed", error=str(e),
                progress=f"执行失败: {e}",
            )
            if gate_info:
                await self._gate_report(task_id, gate_info, "failure", f"任务失败: {e}")

    # ==================== 辅助 ====================

    async def _load_cases(self, req: TriggerRequest) -> List:
        if req.case_source == "inline":
            return await load_inline(req.test_cases)
        if req.case_source == "file":
            return await load_file(req.test_case_file)
        if req.case_source == "platform":
            return await load_platform(req.project_code)
        return []

    async def _on_result(self, task_id: str, result: CheckResultItem):
        # 实时写库
        self.store.append_result(task_id, result.model_dump())

    async def _gate_report(
        self, task_id: str, gate_info: Dict[str, Any],
        state: str, description: str = "",
    ):
        try:
            res = await report_status(
                provider=gate_info.get("provider", ""),
                repo_ref=gate_info.get("repo_ref", ""),
                commit_sha=gate_info.get("commit_sha", ""),
                state=state,
                task_id=task_id,
                description=description,
                token_override=gate_info.get("token", ""),
            )
            gate_info["state"] = state
            gate_info["last_response"] = res
            self.store.update(task_id, gate=gate_info)
        except Exception as e:
            logger.warning(f"门禁上报异常: {e}")
