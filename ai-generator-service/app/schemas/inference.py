#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
请求/响应数据模型
"""

from typing import Any

from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息模型"""

    role: str = Field(..., description="消息角色: user/assistant")
    content: str = Field(..., description="消息内容")


class InferRequest(BaseModel):
    """单次推理请求"""

    messages: list[Message] = Field(..., description="消息列表（仅 user/assistant）")


class InferResponse(BaseModel):
    """推理响应"""

    success: bool = Field(..., description="是否成功")
    result: Any | None = Field(None, description="推理结果")
    raw_content: str | None = Field(None, description="原始返回内容（JSON 解析失败时）")
    error: str | None = Field(None, description="错误信息")


class BatchItem(BaseModel):
    """批量推理项"""

    messages: list[Message] = Field(..., description="消息列表（仅 user/assistant）")


class BatchRequest(BaseModel):
    """批量推理请求"""

    items: list[BatchItem] = Field(..., description="批量推理项列表")


class BatchResult(BaseModel):
    """单个批量推理结果"""

    index: int = Field(..., description="项索引")
    success: bool = Field(..., description="是否成功")
    result: Any | None = Field(None, description="推理结果")
    error: str | None = Field(None, description="错误信息")


class BatchResponse(BaseModel):
    """批量推理响应"""

    total: int = Field(..., description="总数量")
    completed: int = Field(..., description="完成数量")
    results: list[BatchResult] = Field(..., description="结果列表")


class AsyncBatchResponse(BaseModel):
    """异步批量推理响应"""

    task_id: str = Field(..., description="任务 ID")
    message: str = Field("任务已创建，请通过 task_id 查询结果")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""

    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="任务状态: pending/processing/completed/failed")
    total: int = Field(..., description="总数量")
    completed: int = Field(..., description="完成数量")
    results: list[BatchResult] | None = Field(None, description="结果列表（完成后）")
    error: str | None = Field(None, description="错误信息（失败时）")
    created_at: float = Field(..., description="创建时间戳")
    updated_at: float = Field(..., description="更新时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field("ok", description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")


class TestCaseGenerateRequest(BaseModel):
    """测试用例生成请求（一次请求处理多个测试方向）"""

    module: str = Field(..., description="模块名称")
    func_point: str = Field(..., description="功能点")
    related_detail: str = Field("", description="关联需求详情")
    test_directions: list[str] = Field(
        default=["功能点测试", "业务逻辑测试", "其他测试"],
        description="测试方向列表"
    )
    temperature: float | None = Field(None, description="生成温度（可选，用于重试时降低随机性）")


class TestCaseGenerateResult(BaseModel):
    """单个测试用例"""

    title: str = Field(..., description="用例标题")
    steps: str = Field(..., description="测试步骤")
    expected_result: str = Field(..., description="预期结果")
    priority: str = Field(default="p2", description="优先级")
    test_type: str = Field(..., description="测试类型")


class TestCaseGenerateResponse(BaseModel):
    """测试用例生成响应"""

    success: bool = Field(..., description="是否成功")
    cases: list[TestCaseGenerateResult] | None = Field(None, description="生成的用例列表")
    error: str | None = Field(None, description="错误信息")