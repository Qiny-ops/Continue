#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推理引擎
业务逻辑层，处理推理和测试用例生成
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Tuple

from app.config import get_settings
from app.prompts import get_system_prompt, get_test_direction_prompt
from app.services.model_client import ModelClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InferenceEngine:
    """推理引擎"""

    def __init__(self):
        self.settings = get_settings()

    @staticmethod
    def _build_full_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """构建完整消息：system prompt + 用户消息。
        原来 infer_single / infer_stream / infer_batch 中各复制了一次。
        """
        full = [{"role": "system", "content": get_system_prompt()}]
        full.extend(messages)
        return full

    async def infer_single(
        self,
        messages: List[Dict[str, str]],
        extract_json: bool = True,
    ) -> Tuple[Any | None, str | None]:
        """
        单次推理

        Args:
            messages: 用户消息列表
            extract_json: 是否提取 JSON

        Returns:
            (结果, 错误信息)
        """
        # 构建完整消息：system + 用户消息
        full_messages = self._build_full_messages(messages)

        result, error = await ModelClient.infer(full_messages, extract_json=extract_json)

        if error:
            logger.error(f"单次推理失败: {error}")
            return None, error

        logger.info("单次推理完成")
        return result, None

    async def infer_stream(
        self,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """
        流式推理

        Args:
            messages: 用户消息列表

        Yields:
            流式内容片段
        """
        # 构建完整消息
        full_messages = self._build_full_messages(messages)

        logger.info("开始流式推理")
        try:
            async for chunk in ModelClient.infer_stream(full_messages):
                yield chunk
        except asyncio.CancelledError:
            logger.info("流式推理被取消（客户端断连）")
            raise

        logger.info("流式推理完成")

    async def infer_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        批量推理

        Args:
            items: 批量推理项列表，每项包含 messages

        Returns:
            批量推理结果列表
        """
        results = []

        for i, item in enumerate(items):
            messages = item.get("messages", [])
            full_messages = self._build_full_messages(messages)

            result, error = await ModelClient.infer(full_messages, extract_json=True)

            results.append({
                "index": i,
                "success": error is None,
                "result": result if error is None else None,
                "error": error,
            })

            logger.debug(f"批量推理项 {i + 1}/{len(items)} 完成")

        completed = sum(1 for r in results if r["success"])
        logger.info(f"批量推理完成: {completed}/{len(items)}")

        return results

    async def generate_testcases(
        self,
        module: str,
        func_point: str,
        test_directions: List[str],
        related_detail: str = "",
        temperature: float = None,
        max_concurrency: int = 10,
    ) -> Tuple[List[Dict[str, Any]] | None, str | None]:
        """
        生成测试用例（并行处理多个测试方向）

        Args:
            module: 模块名称
            func_point: 功能点
            test_directions: 测试方向列表
            related_detail: 关联需求详情
            temperature: 生成温度
            max_concurrency: 最大并发数（防止客户端传入 200 方向打满 API）

        Returns:
            (测试用例列表, 错误信息)
        """
        # 构建基础输入文本
        base_text = f"模块：{module}，功能点：{func_point}"
        if related_detail and related_detail != "无相关需求":
            base_text += f"\n关联需求：{related_detail}"
        else:
            base_text += "\n关联需求：无"

        # 并发信号量，限制同时调用 LLM API 的数量
        sem = asyncio.Semaphore(max_concurrency)

        async def generate_for_direction(direction: str) -> Tuple[str, List[Dict] | None, str | None]:
            """为单个测试方向生成用例"""
            async with sem:
                prompt = get_test_direction_prompt(direction)
                input_text = f"{base_text}\n{prompt}"

                messages = [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": input_text}
                ]

                actual_temp = temperature if temperature is not None else self.settings.temperature

                result, error = await ModelClient.infer(
                    messages,
                    extract_json=True,
                    temperature=actual_temp,
                )

                if error:
                    return direction, None, error

                # 确保结果是列表
                if isinstance(result, dict):
                    cases = [result]
                elif isinstance(result, list):
                    cases = result
                else:
                    return direction, None, "返回格式错误"

                return direction, cases, None

        # 并行执行所有测试方向，单方向异常不丢全批
        tasks = [generate_for_direction(d) for d in test_directions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集所有用例（解包 gather 结果，跳异常与失败方向）
        all_cases = []

        for result in results:
            if isinstance(result, BaseException):
                logger.warning(f"生成方向异常被 gather 隔离: {result}")
                continue

            direction, cases, error = result
            if error:
                logger.warning(f"测试方向 {direction} 生成失败: {error}")
                continue

            if cases:
                for case in cases:
                    try:
                        all_cases.append({
                            "title": case.get("title") or case.get("testpoint") or case.get("name", ""),
                            "steps": case.get("steps") or case.get("test_steps") or case.get("description", ""),
                            "expected_result": case.get("expected_result") or case.get("expectation") or case.get("expected", ""),
                            "priority": case.get("priority", "中"),
                            "test_type": direction,
                        })
                    except Exception as e:
                        logger.warning(f"解析用例失败: {e}")
                        continue

        if not all_cases:
            logger.error("未生成任何用例")
            return None, "未生成任何用例"

        logger.info(f"生成测试用例完成: {len(all_cases)} 条")
        return all_cases, None
