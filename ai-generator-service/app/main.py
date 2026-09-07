#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""

import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import inference
from app.services.task_store import TaskStore
from app.utils.logger import get_logger

# 模块级 logger，保留原名称
service_logger = get_logger("ai-generator-service")

# 获取配置
settings = get_settings()

# 创建应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 模型推理微服务，支持单次推理、流式推理和批量推理",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置：由 settings.cors_allowed_origins 白名单驱动（去掉通配符，避免凭据泄露）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 记录请求
    service_logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # 记录响应
    process_time = time.time() - start_time
    service_logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )

    return response


# 注册路由
app.include_router(inference.router)

# TaskStore 定期清理配置
_CLEANUP_INTERVAL = 600  # 每 10 分钟清理一次已完成/失败任务（保留时长 1 小时）
_CLEANUP_TASK: asyncio.Task | None = None


async def _periodic_cleanup():
    """后台定期清理 TaskStore 中已完成的旧任务"""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL)
        try:
            cleared = await TaskStore.clear_completed(max_age=3600)
            if cleared > 0:
                service_logger.debug(f"TaskStore 清理: {cleared} 个过期任务")
        except Exception:
            service_logger.exception("TaskStore 定期清理异常")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global _CLEANUP_TASK
    service_logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    service_logger.info(f"Model API: {settings.model_base_url}")

    # 启动时清理上一次运行的残留任务（所有状态的任务都可能已失效）
    try:
        all_tasks = await TaskStore.list_tasks()
        for task in all_tasks:
            await TaskStore.delete_task(task.task_id)
        if all_tasks:
            service_logger.info(f"启动清理: 删除 {len(all_tasks)} 个残留任务")
    except Exception:
        service_logger.exception("启动清理 TaskStore 失败")

    # 启动后台定期清理任务
    _CLEANUP_TASK = asyncio.create_task(_periodic_cleanup())


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global _CLEANUP_TASK
    service_logger.info(f"Shutting down {settings.app_name}")

    if _CLEANUP_TASK and not _CLEANUP_TASK.done():
        _CLEANUP_TASK.cancel()
        try:
            await _CLEANUP_TASK
        except asyncio.CancelledError:
            pass


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }