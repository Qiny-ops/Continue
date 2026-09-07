#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 模型调用服务
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """LLM 服务"""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.model_base_url
        self.api_key = settings.model_api_key
        self.model = settings.model_name
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.top_p = settings.top_p
        self.presence_penalty = settings.presence_penalty
        self.timeout = 120.0

    def _build_body(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> Dict[str, Any]:
        """构建请求体"""
        return {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "stream": stream,
        }

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        同步调用 LLM

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]

        Returns:
            {"content": "LLM 回答内容", "usage": {...}, "finish_reason": "stop"}
        """
        url = f"{self.base_url}/chat/completions"
        body = self._build_body(messages, stream=False)
        body.update(kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=body)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            return {
                "content": content,
                "usage": result.get("usage", {}),
                "finish_reason": result["choices"][0].get("finish_reason"),
                "raw": result
            }

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 LLM

        Yields:
            回答内容片段
        """
        url = f"{self.base_url}/chat/completions"
        body = self._build_body(messages, stream=True)
        body.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=body
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        if line == "data: [DONE]":
                            break
                        if line.startswith("data: "):
                            try:
                                chunk = json.loads(line[6:])
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError):
                                continue