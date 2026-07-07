#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import inference
from app.utils.logger import get_logger, service_logger

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

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    service_logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    service_logger.info(f"Model API: {settings.model_base_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    service_logger.info(f"Shutting down {settings.app_name}")


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