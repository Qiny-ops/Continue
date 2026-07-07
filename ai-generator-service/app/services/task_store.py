#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步任务存储
用于管理批量推理任务的状态
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """任务数据"""

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    total: int = 0
    completed: int = 0
    results: list[dict] = field(default_factory=list)
    error: str | None = None


class TaskStore:
    """任务存储（内存实现）"""

    _instance: dict[str, Task] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def create_task(cls, total: int = 0) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, total=total)

        async with cls._lock:
            cls._instance[task_id] = task

        return task_id

    @classmethod
    async def get_task(cls, task_id: str) -> Task | None:
        """获取任务"""
        async with cls._lock:
            return cls._instance.get(task_id)

    @classmethod
    async def update_task(
        cls,
        task_id: str,
        status: TaskStatus | None = None,
        completed: int | None = None,
        results: list[dict] | None = None,
        error: str | None = None,
    ) -> bool:
        """更新任务状态"""
        async with cls._lock:
            task = cls._instance.get(task_id)
            if not task:
                return False

            if status:
                task.status = status
            if completed is not None:
                task.completed = completed
            if results is not None:
                task.results = results
            if error is not None:
                task.error = error

            task.updated_at = time.time()
            return True

    @classmethod
    async def delete_task(cls, task_id: str) -> bool:
        """删除任务"""
        async with cls._lock:
            if task_id in cls._instance:
                del cls._instance[task_id]
                return True
            return False

    @classmethod
    async def list_tasks(cls) -> list[Task]:
        """列出所有任务"""
        async with cls._lock:
            return list(cls._instance.values())

    @classmethod
    async def clear_completed(cls, max_age: float = 3600) -> int:
        """清理已完成的旧任务"""
        now = time.time()
        cleared = 0

        async with cls._lock:
            to_delete = [
                task_id
                for task_id, task in cls._instance.items()
                if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                and now - task.updated_at > max_age
            ]
            for task_id in to_delete:
                del cls._instance[task_id]
                cleared += 1

        return cleared