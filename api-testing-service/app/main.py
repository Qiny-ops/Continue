#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, Header

from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import router
from app.services.kb_client import KBClient
from app.services.llm_service import LLMService
from app.services.db_service import DBService
from app.engine import TestEngine
from app.utils.logger import get_logger

service_logger = get_logger("api-testing-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # Startup
    service_logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    service_logger.info(f"KB Service: {settings.kb_base_url}")

    kb_client = KBClient()
    llm_service = LLMService()
    db_service = DBService()
    app.state.engine = TestEngine(
        kb_client=kb_client,
        llm_service=llm_service,
        db_service=db_service
    )
    service_logger.info("服务初始化完成")

    yield

    # Shutdown
    service_logger.info(f"Shutting down {settings.app_name}")


# 获取配置
settings = get_settings()

# 创建应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="接口测试微服务，支持接口业务流分析、测试用例生成、依赖分析、数据填充、用例执行和结果校验",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 配置：由 settings.cors_allowed_origins 白名单驱动（去掉通配符，避免凭据泄露）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """API Key 鉴权依赖。

    仅当配置了 api_key 时才强制校验（空值 = 开发模式，不强制）。
    Django 侧调用本服务时需在请求头携带 X-API-Key。
    """
    if not settings.api_key:
        return  # 开发模式：未配置 key 时放行
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="缺少或非法的 X-API-Key")


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    service_logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    service_logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )

    return response


# 注册路由（对 /api/v1 全路由套用 API Key 鉴权依赖）
app.include_router(router, prefix="/api/v1", dependencies=[Depends(verify_api_key)])


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
