# -*- coding: utf-8 -*-
"""
任务持久化（SQLite 轻量存储）

- 内存 dict 缓存 + SQLite 持久化（防进程重启丢失）
- 每次状态/进度/结果变化都立即写库（课程要求实时落库）
- 启动时将所有 running 状态标记为 failed（异常中断可重新触发）
"""
import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.task import TaskReport


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class TaskStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(settings.data_dir, "aicheck.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        self._cache: Dict[str, TaskReport] = {}
        self._load_cache()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self):
        with self._lock, self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    status TEXT,
                    progress TEXT,
                    updated_at TEXT,
                    payload TEXT
                )
                """
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            c.commit()

    def _load_cache(self):
        with self._lock, self._conn() as c:
            rows = c.execute("SELECT payload FROM tasks").fetchall()
        for r in rows:
            try:
                data = json.loads(r["payload"])
                report = TaskReport.model_validate(data)
                # 启动时把残留 running 标记为 failed
                if report.status == "running":
                    report.status = "failed"
                    report.error = (report.error or "") + " [重启中断]"
                    report.updated_at = _now()
                    self._upsert(report)
                self._cache[report.task_id] = report
            except Exception:
                continue

    def _upsert(self, report: TaskReport):
        report.updated_at = _now()
        payload = report.model_dump_json()
        with self._lock, self._conn() as c:
            c.execute(
                """
                INSERT INTO tasks (task_id, status, progress, updated_at, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status=excluded.status,
                    progress=excluded.progress,
                    updated_at=excluded.updated_at,
                    payload=excluded.payload
                """,
                (report.task_id, report.status, report.progress, report.updated_at, payload),
            )
            c.commit()

    def create(self, report: TaskReport) -> TaskReport:
        report.status = "pending"
        report.progress = "任务已创建，等待执行"
        report.created_at = _now()
        report.updated_at = report.created_at
        self._cache[report.task_id] = report
        self._upsert(report)
        return report

    def update(self, task_id: str, **fields: Any) -> Optional[TaskReport]:
        report = self._cache.get(task_id)
        if not report:
            return None
        for k, v in fields.items():
            if v is not None or k in ("progress", "error", "status"):
                setattr(report, k, v)
        self._upsert(report)
        return report

    def append_result(self, task_id: str, result_dict: Dict[str, Any]) -> Optional[TaskReport]:
        report = self._cache.get(task_id)
        if not report:
            return None
        report.results.append(result_dict)  # type: ignore[arg-type]
        self._upsert(report)
        return report

    def get(self, task_id: str) -> Optional[TaskReport]:
        return self._cache.get(task_id)

    def list(self) -> List[TaskReport]:
        items = list(self._cache.values())
        order = {"running": 0, "pending": 1, "completed": 2, "failed": 3}
        # 先按 created_at desc（保留每组内最新优先），再按状态优先级（保持稳定排序）
        items.sort(key=lambda r: r.created_at or "", reverse=True)
        items.sort(key=lambda r: order.get(r.status, 99))
        return items
