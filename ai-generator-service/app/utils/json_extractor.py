#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 响应 JSON 解析工具

多策略重试解析：
- <thought>/<think>/<thinking> 标签处理
- markdown 代码块提取
- 类型自动转换（dict <-> list）
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def _strip_thinking_tags(content: str) -> str:
    """移除 LLM 思考标签（</thought>/</think>/</thinking>），提取其后的正文内容"""
    for tag in ("</thought>", "</think>", "</thinking>"):
        match = re.search(rf'{re.escape(tag)}\s*(.*?)$', content, re.DOTALL)
        if match:
            return match.group(1)
    return content


def _extract_json_block(content: str) -> str:
    """从 LLM 响应中提取 JSON 内容（支持 markdown 代码块）"""
    content = content.strip()

    # 优先匹配 ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if match:
        return match.group(1).strip()

    # 尝试匹配普通 ``` ... ```
    match = re.search(r'```\s*([\s\S]*?)\s*```', content)
    if match:
        return match.group(1).strip()

    return content


def _extract_json_object(content: str) -> str:
    """提取内容中第一个完整的 JSON 对象 {...}"""
    start = content.find('{')
    end = content.rfind('}') + 1
    if start != -1 and end > start:
        return content[start:end]
    return content


def _extract_json_array(content: str) -> str:
    """提取内容中第一个完整的 JSON 数组 [...]"""
    start = content.find('[')
    end = content.rfind(']') + 1
    if start != -1 and end > start:
        return content[start:end]
    return content


def parse_llm_json(
    content: str,
    expected_type: type = dict,
    max_retries: int = 3
) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    解析 LLM 返回的 JSON，支持多策略重试和多种格式。

    Args:
        content: LLM 原始响应文本
        expected_type: 期望的 JSON 类型（dict 或 list）
        max_retries: 最大重试次数（逐步尝试更激进的提取策略）

    Returns:
        解析后的 JSON 对象，失败返回 None
    """
    if not content:
        return None

    # 预处理：移除 thinking 标签
    text = _strip_thinking_tags(content).strip()

    for attempt in range(max_retries):
        try:
            if attempt == 0:
                # 第一次：提取 markdown 代码块
                text = _extract_json_block(text)
            elif attempt == 1:
                # 第二次：尝试直接提取 JSON 结构
                if expected_type is dict:
                    text = _extract_json_object(text)
                else:
                    text = _extract_json_array(text)
            # 第三次：用上一次的结果直接尝试

            result = json.loads(text)

            if isinstance(result, expected_type):
                logger.info(f"JSON 解析成功 (尝试 {attempt + 1}/{max_retries})")
                return result

            # 类型不匹配但可转换
            if isinstance(result, dict) and expected_type is list:
                return [result]
            if isinstance(result, list) and expected_type is dict and len(result) > 0:
                return result[0]

            raise json.JSONDecodeError(
                f"解析结果不是 {expected_type.__name__} 类型", text, 0
            )

        except json.JSONDecodeError as e:
            logger.warning(f"解析 JSON 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                if expected_type is dict:
                    text = _extract_json_object(text)
                else:
                    text = _extract_json_array(text)
                continue
            logger.error(f"解析 JSON 失败，已重试 {max_retries} 次，内容预览: {text[:200]}")
            return None

    return None


def parse_json_safe(content: str) -> tuple[Optional[Any], Optional[str]]:
    """安全解析 JSON，返回 (data, error) 元组"""
    if not content:
        return None, "内容为空"
    try:
        return json.loads(content), None
    except json.JSONDecodeError as e:
        return None, f"JSON 解析错误：{str(e)}"


def extract_and_parse(content: str) -> tuple[Optional[Any], Optional[str]]:
    """从 LLM 内容中提取并解析 JSON"""
    result = parse_llm_json(content, expected_type=dict)
    if result is not None:
        return result, None
    # fallback: 尝试解析为 list
    result = parse_llm_json(content, expected_type=list)
    if result is not None:
        return result, None
    return None, "无法提取 JSON 内容"
