#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型客户端
异步调用本地模型进行推理
"""

import asyncio
import time
from typing import Any, AsyncGenerator, Tuple

from openai import AsyncOpenAI

from app.config import get_settings
from app.utils.json_extractor import extract_and_parse


class ModelClient:
    """异步模型客户端"""

    _instance: AsyncOpenAI | None = None
    _model_id: str | None = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """获取 OpenAI 异步客户端单例"""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = AsyncOpenAI(
                api_key=settings.model_api_key,
                base_url=settings.model_base_url,
            )
        return cls._instance

    @classmethod
    async def get_model_id(cls) -> str:
        """获取可用模型 ID"""
        if cls._model_id is None:
            client = cls.get_client()
            models = await client.models.list()
            if models.data:
                cls._model_id = models.data[0].id
        return cls._model_id or ""

    @classmethod
    async def infer(
        cls,
        messages: list[dict],
        extract_json: bool = True,
        temperature: float = None,
    ) -> Tuple[Any | None, str | None]:
        """
        执行推理（非流式）

        Args:
            messages: 消息列表
            extract_json: 是否自动提取并解析 JSON
            temperature: 生成温度（可选，覆盖默认值）

        Returns:
            (结果, 错误信息)
        """
        settings = get_settings()
        client = cls.get_client()
        model_id = await cls.get_model_id()

        if not model_id:
            return None, "未获取到可用模型"

        # 使用传入的temperature或默认值
        actual_temperature = temperature if temperature is not None else settings.temperature

        for attempt in range(settings.max_retries):
            try:
                response = await client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    max_tokens=settings.max_tokens,
                    temperature=actual_temperature,
                    top_p=settings.top_p,
                    presence_penalty=settings.presence_penalty,
                    extra_body={"top_k": settings.top_k},
                    stream=False,
                )

                content = response.choices[0].message.content or ""

                if extract_json:
                    return extract_and_parse(content)
                return content, None

            except Exception as e:
                error_msg = f"API 调用失败 (尝试 {attempt + 1}/{settings.max_retries}): {str(e)}"
                if attempt < settings.max_retries - 1:
                    await asyncio.sleep(settings.retry_delay)
                else:
                    return None, error_msg

        return None, "达到最大重试次数"

    @classmethod
    async def infer_stream(
        cls,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        """
        执行流式推理

        Args:
            messages: 消息列表

        Yields:
            流式返回的内容片段
        """
        settings = get_settings()
        client = cls.get_client()
        model_id = await cls.get_model_id()

        if not model_id:
            yield f"[错误] 未获取到可用模型"
            return

        try:
            stream = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                top_p=settings.top_p,
                presence_penalty=settings.presence_penalty,
                extra_body={"top_k": settings.top_k},
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"[错误] API 调用失败: {str(e)}"

    @classmethod
    def reset(cls):
        """重置客户端（用于配置变更时）"""
        cls._instance = None
        cls._model_id = None