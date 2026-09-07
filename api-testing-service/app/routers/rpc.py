#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 路由定义

RESTful API 接口
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
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
from app.utils.sse import sse_response

logger = get_logger(__name__)

router = APIRouter(tags=["api"])


def _get_engine(request: Request):
    """从 app.state 获取引擎实例"""
    return request.app.state.engine


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
async def get_flow(params: GetFlowParams, request: Request):
    """获取接口业务流（流式）"""
    engine = _get_engine(request)
    return sse_response(engine.get_flow(
        kb_id=params.kb_id,
        query=params.query,
        kb_api_key=params.kb_api_key
    ))


# ==================== 测试用例生成 ====================

@router.post("/testcase/generate")
async def generate_testcase(params: GenerateTestCaseParams, request: Request):
    """生成接口测试用例（流式）"""
    engine = _get_engine(request)
    return sse_response(engine.generate_testcase(
        kb_id=params.kb_id,
        query=params.query,
        kb_api_key=params.kb_api_key,
        save_to_db=params.save_to_db,
        knowledge_id=params.knowledge_id
    ))


# ==================== 接口依赖分析 ====================

@router.post("/dependency")
async def get_dependency(params: GetDependencyParams, request: Request):
    """获取接口依赖（流式）"""
    engine = _get_engine(request)
    return sse_response(engine.get_api_dependency(
        case_id=params.case_id,
        api_name=params.api_name,
        precondition=params.precondition,
        testpoint=params.testpoint,
        expectation=params.expectation,
        kb_id=params.kb_id,
        kb_api_key=params.kb_api_key
    ))


# ==================== 测试数据填充 ====================

@router.post("/testdata/fill")
async def fill_testdata(params: FillDataParams, request: Request):
    """填充测试数据（流式）"""
    engine = _get_engine(request)
    settings = get_settings()
    base_url = params.base_url or settings.api_base_url

    return sse_response(engine.fill_test_data(
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
    ))


# ==================== 测试用例执行 ====================

@router.post("/testcase/execute")
async def execute_testcase(params: ExecuteTestCaseParams, request: Request):
    """执行测试用例（流式）"""
    engine = _get_engine(request)
    settings = get_settings()
    base_url = params.base_url or settings.api_base_url

    return sse_response(engine.execute_testcase(
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
    ))


# ==================== 测试用例校验 ====================

@router.post("/testcase/validate")
async def validate_testcase(params: ValidateTestCaseParams, request: Request):
    """校验测试用例（流式）"""
    engine = _get_engine(request)
    return sse_response(engine.validate_testcase(
        case_id=params.case_id,
        api_name=params.api_name,
        precondition=params.precondition,
        testpoint=params.testpoint,
        expectation=params.expectation,
        execution_results=params.execution_results,
        kb_id=params.kb_id,
        kb_api_key=params.kb_api_key
    ))


# ==================== LLM 对话 ====================

@router.post("/llm/chat")
async def llm_chat(params: LLMChatParams, request: Request):
    """LLM 对话（同步）"""
    engine = _get_engine(request)

    result = None
    async for event in engine.llm_chat(
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
async def llm_chat_stream(params: LLMChatParams, request: Request):
    """LLM 对话（流式）"""
    engine = _get_engine(request)
    return sse_response(engine.llm_chat(
        query=params.query,
        system_message=params.system_message,
        stream=True
    ))
