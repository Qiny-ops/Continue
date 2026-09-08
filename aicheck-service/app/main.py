# -*- coding: utf-8 -*-
"""FastAPI 应用入口（对齐 api-testing-service 规范）"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health as health_router
from app.routers import tasks as tasks_router
from app.routers import webhook as webhook_router
from app.services.task_manager import TaskManager
from app.services.task_store import TaskStore
from app.utils.logger import get_logger

service_logger = get_logger("aicheck-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    service_logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    store = TaskStore()
    app.state.task_store = store
    app.state.task_manager = TaskManager(store)
    service_logger.info(
        f"aicheck 已就绪 | concurrency={settings.concurrency} "
        f"retries={settings.max_retries} timeout={settings.timeout}s"
    )
    yield
    service_logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 代码变更检查服务：拉取仓库 → 风险评估 → AI 用例校验 → 门禁上报",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    """API Key 鉴权：空 = 开发模式放行；非空时强制校验"""
    if not settings.api_key:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(401, "缺少或非法的 X-API-Key")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    cost = (time.time() - start) * 1000
    service_logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({cost:.0f}ms)"
    )
    return response


# /api/v1 统一挂鉴权（健康/任务/查询）
app.include_router(
    health_router.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)]
)
app.include_router(
    tasks_router.router, prefix="/api/v1", dependencies=[Depends(verify_api_key)]
)
# Webhook 单独 include，不挂 X-API-Key（走验签）
app.include_router(webhook_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
