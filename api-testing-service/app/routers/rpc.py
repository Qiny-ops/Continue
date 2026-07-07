#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 路由定义

RESTful API 接口
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.engine import ApiTestEngine
from app.execute.engine import TestExecutionEngine
from app.services.kb_client import KBClient
from app.services.llm_service import LLMService
from app.services.db_service import DBService
from app.schemas.rpc import (
    GetFlowParams,
    GenerateTestCaseParams,
    GetDependencyParams,
    FillDataParams,
    ExecuteTestCaseParams,
    ValidateTestCaseParams,
    LLMChatParams,
    HealthResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["api"])

# 全局服务实例
_kb_client: Optional[KBClient] = None
_llm_service: Optional[LLMService] = None
_db_service: Optional[DBService] = None
_engine: Optional[ApiTestEngine] = None


def init_services():
    """初始化服务"""
    global _kb_client, _llm_service, _db_service, _engine

    if _engine is None:
        _llm_service = LLMService()
        _kb_client = KBClient()
        _db_service = DBService()

        _engine = ApiTestEngine(
            kb_client=_kb_client,
            llm_service=_llm_service,
            db_service=_db_service
        )

        logger.info("服务初始化完成")

    return _engine


def get_execution_engine() -> TestExecutionEngine:
    """获取执行引擎"""
    global _kb_client, _llm_service

    if _kb_client is None or _llm_service is None:
        _llm_service = LLMService()
        _kb_client = KBClient()

    return TestExecutionEngine(kb_client=_kb_client, llm_service=_llm_service)


# ==================== 健康检查 ====================

@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version
    )


@router.get("/status")
async def status():
    """服务状态"""
    settings = get_settings()
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "endpoints": [
            "GET  /api/v1/health - 健康检查",
            "GET  /api/v1/status - 服务状态",
            "POST /api/v1/flow - 获取接口业务流（流式）",
            "POST /api/v1/testcase/generate - 生成测试用例（流式）",
            "POST /api/v1/dependency - 获取接口依赖（流式）",
            "POST /api/v1/testdata/fill - 填充测试数据（流式）",
            "POST /api/v1/testcase/execute - 执行测试用例（流式）",
            "POST /api/v1/testcase/validate - 校验测试用例（流式）",
            "POST /api/v1/llm/chat - LLM 对话（流式/同步）",
        ]
    }


# ==================== 接口业务流 ====================

@router.post("/flow")
async def get_flow(params: GetFlowParams):
    """
    获取接口业务流（流式）
    """
    init_services()

    async def generate():
        async for event in _engine.get_flow(
            kb_id=params.kb_id,
            query=params.query,
            kb_api_key=params.kb_api_key
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== 测试用例生成 ====================

@router.post("/testcase/generate")
async def generate_testcase(params: GenerateTestCaseParams):
    """
    生成接口测试用例（流式）
    """
    init_services()

    async def generate():
        async for event in _engine.generate_testcase(
            kb_id=params.kb_id,
            query=params.query,
            kb_api_key=params.kb_api_key,
            save_to_db=params.save_to_db,
            knowledge_id=params.knowledge_id
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== 接口依赖分析 ====================

@router.post("/dependency")
async def get_dependency(params: GetDependencyParams):
    """
    获取接口依赖（流式）
    """
    init_services()

    async def generate():
        async for event in _engine.get_api_dependency(
            case_id=params.case_id,
            api_name=params.api_name,
            precondition=params.precondition,
            testpoint=params.testpoint,
            expectation=params.expectation,
            kb_id=params.kb_id,
            kb_api_key=params.kb_api_key
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== 测试数据填充 ====================

@router.post("/testdata/fill")
async def fill_testdata(params: FillDataParams):
    """
    填充测试数据（流式）
    """
    init_services()
    settings = get_settings()

    # 使用传入的 base_url 或配置的默认值
    base_url = params.base_url or settings.api_base_url

    async def generate():
        async for event in _engine.fill_test_data(
            case_id=params.case_id,
            api_name=params.api_name,
            precondition=params.precondition,
            testpoint=params.testpoint,
            expectation=params.expectation,
            dependency=params.dependency,
            test_data=params.test_data,
            kb_id=params.kb_id,
            kb_api_key=params.kb_api_key,
            base_url=base_url
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== 测试用例执行 ====================

@router.post("/testcase/execute")
async def execute_testcase(params: ExecuteTestCaseParams):
    """
    执行测试用例（流式）
    """
    engine = get_execution_engine()
    settings = get_settings()

    # 使用传入的 base_url 或配置的默认值
    base_url = params.base_url or settings.api_base_url

    async def generate():
        async for event in engine.execute_testcase(
            case_id=params.case_id,
            api_name=params.api_name,
            precondition=params.precondition,
            testpoint=params.testpoint,
            expectation=params.expectation,
            run_list=params.run_list,
            test_data=params.test_data,
            base_url=base_url,
            kb_id=params.kb_id,
            kb_api_key=params.kb_api_key
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== 测试用例校验 ====================

@router.post("/testcase/validate")
async def validate_testcase(params: ValidateTestCaseParams):
    """
    校验测试用例（流式）
    """
    engine = get_execution_engine()

    async def generate():
        async for event in engine.validate_testcase(
            case_id=params.case_id,
            api_name=params.api_name,
            precondition=params.precondition,
            testpoint=params.testpoint,
            expectation=params.expectation,
            execution_results=params.execution_results,
            kb_id=params.kb_id,
            kb_api_key=params.kb_api_key
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# ==================== LLM 对话 ====================

@router.post("/llm/chat")
async def llm_chat(params: LLMChatParams):
    """
    LLM 对话（同步）
    """
    init_services()

    result = None
    async for event in _engine.llm_chat(
        query=params.query,
        system_message=params.system_message,
        stream=False
    ):
        if event.get("type") == "result":
            result = event.get("data")
        elif event.get("type") == "error":
            raise HTTPException(status_code=500, detail=event.get("data", {}).get("message"))

    return result


@router.post("/llm/chat/stream")
async def llm_chat_stream(params: LLMChatParams):
    """
    LLM 对话（流式）
    """
    init_services()

    async def generate():
        async for event in _engine.llm_chat(
            query=params.query,
            system_message=params.system_message,
            stream=True
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
