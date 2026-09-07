#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSE 流式响应工具

统一 SSE 事件格式化和 StreamingResponse 构造（与 web-automation-service 同约定）。
"""

import json
from typing import Any, AsyncGenerator, Dict

from fastapi.responses import StreamingResponse


def format_sse_event(event: Dict[str, Any]) -> str:
    """将事件字典格式化为 SSE data 行"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def create_sse_stream(source: AsyncGenerator) -> AsyncGenerator:
    """将 async generator 的事件包装为 SSE 格式（服务原始实现，保持原状）。"""
    async for event in source:
        yield format_sse_event(event)


def sse_response(source: AsyncGenerator) -> StreamingResponse:
    """创建 SSE StreamingResponse"""
    return StreamingResponse(
        create_sse_stream(source),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
