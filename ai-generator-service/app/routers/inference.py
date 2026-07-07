#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推理 API 路由
"""

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.engine import InferenceEngine
from app.schemas.inference import (
    AsyncBatchResponse,
    BatchRequest,
    BatchResponse,
    BatchResult,
    HealthResponse,
    InferRequest,
    InferResponse,
    TaskStatusResponse,
    TestCaseGenerateRequest,
    TestCaseGenerateResponse,
    TestCaseGenerateResult,
)
from app.services.model_client import ModelClient
from app.services.task_store import TaskStatus, TaskStore
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1", tags=["inference"])
logger = get_logger(__name__)

# 初始化引擎
engine = InferenceEngine()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    settings = get_settings()
    logger.debug("健康检查请求")
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.post("/reset")
async def reset_model_cache():
    """重置模型缓存（用于模型变更后刷新）"""
    logger.info("重置模型缓存")
    ModelClient.reset()
    model_id = await ModelClient.get_model_id()
    logger.info(f"模型已重置，当前模型: {model_id}")
    return {"success": True, "model_id": model_id}


@router.post("/infer", response_model=InferResponse)
async def infer(request: InferRequest):
    """
    单次推理

    同步返回推理结果，自动提取并解析 JSON
    system 消息由服务端硬编码，用户只需传入 user/assistant 消息
    """
    logger.info(f"单次推理请求，消息数: {len(request.messages)}")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    result, error = await engine.infer_single(messages, extract_json=True)

    if error:
        return InferResponse(success=False, result=None, error=error)

    # 如果返回的是字符串（JSON 解析失败但原始内容存在）
    if isinstance(result, str):
        return InferResponse(success=True, result=None, raw_content=result, error=None)

    return InferResponse(success=True, result=result, error=None)


@router.post("/infer/stream")
async def infer_stream(request: InferRequest):
    """
    流式推理

    通过 Server-Sent Events 流式返回推理内容
    system 消息由服务端硬编码
    """
    logger.info(f"流式推理请求，消息数: {len(request.messages)}")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def generate():
        async for chunk in engine.infer_stream(messages):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/batch", response_model=BatchResponse)
async def batch_infer(request: BatchRequest):
    """
    同步批量推理

    等待所有推理完成后返回结果，自动提取并解析 JSON
    system 消息由服务端硬编码
    """
    logger.info(f"同步批量推理请求，数量: {len(request.items)}")

    items = [{"messages": [{"role": m.role, "content": m.content} for m in item.messages]} for item in request.items]
    results = await engine.infer_batch(items)

    batch_results = [
        BatchResult(
            index=r["index"],
            success=r["success"],
            result=r["result"],
            error=r["error"],
        )
        for r in results
    ]

    completed = sum(1 for r in batch_results if r.success)

    return BatchResponse(
        total=len(request.items),
        completed=completed,
        results=batch_results,
    )


@router.post("/batch/async", response_model=AsyncBatchResponse)
async def async_batch_infer(request: BatchRequest):
    """
    异步批量推理

    创建后台任务，立即返回 task_id
    通过 GET /batch/{task_id} 查询结果
    """
    logger.info(f"异步批量推理请求，数量: {len(request.items)}")

    task_id = await TaskStore.create_task(total=len(request.items))
    asyncio.create_task(_process_batch(task_id, request))

    logger.info(f"创建异步任务: {task_id}")
    return AsyncBatchResponse(task_id=task_id)


@router.get("/batch/{task_id}", response_model=TaskStatusResponse)
async def get_batch_status(task_id: str):
    """查询异步批量推理任务状态"""
    logger.debug(f"查询任务状态: {task_id}")

    task = await TaskStore.get_task(task_id)

    if not task:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        total=task.total,
        completed=task.completed,
        results=task.results if task.status == TaskStatus.COMPLETED else None,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def _process_batch(task_id: str, request: BatchRequest):
    """后台处理批量推理任务"""
    logger.info(f"开始处理批量任务: {task_id}")
    await TaskStore.update_task(task_id, status=TaskStatus.PROCESSING)

    results = []

    try:
        for i, item in enumerate(request.items):
            messages = [{"role": m.role, "content": m.content} for m in item.messages]
            result, error = await engine.infer_single(messages, extract_json=True)

            results.append({
                "index": i,
                "success": error is None,
                "result": result if error is None else None,
                "error": error,
            })

            await TaskStore.update_task(task_id, completed=i + 1, results=results)

        await TaskStore.update_task(task_id, status=TaskStatus.COMPLETED, results=results)
        logger.info(f"批量任务完成: {task_id}")

    except Exception as e:
        logger.error(f"批量任务失败: {task_id} - {str(e)}")
        await TaskStore.update_task(task_id, status=TaskStatus.FAILED, error=str(e))


@router.post("/testcase/generate", response_model=TestCaseGenerateResponse)
async def generate_test_cases(request: TestCaseGenerateRequest):
    """
    测试用例生成接口

    一次请求处理多个测试方向，内部并行调用模型，返回合并后的用例列表
    """
    logger.info(f"测试用例生成请求: 模块={request.module}, 功能点={request.func_point}, 方向={request.test_directions}")

    cases, error = await engine.generate_testcases(
        module=request.module,
        func_point=request.func_point,
        test_directions=request.test_directions,
        related_detail=request.related_detail or "",
        temperature=request.temperature,
    )

    if error:
        return TestCaseGenerateResponse(success=False, cases=None, error=error)

    # 转换为响应格式
    test_cases = [
        TestCaseGenerateResult(
            title=c["title"],
            steps=c["steps"],
            expected_result=c["expected_result"],
            priority=c["priority"],
            test_type=c["test_type"],
        )
        for c in cases
    ]

    logger.info(f"测试用例生成成功: {len(test_cases)} 条")
    return TestCaseGenerateResponse(success=True, cases=test_cases, error=None)
