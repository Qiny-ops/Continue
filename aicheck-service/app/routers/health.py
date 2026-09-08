# -*- coding: utf-8 -*-
"""健康检查"""
from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "concurrency": settings.concurrency,
        "max_retries": settings.max_retries,
        "timeout": settings.timeout,
    }
