#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 提取工具
从 AI 返回的内容中提取和解析 JSON
"""

import json
import re
from typing import Any, Tuple


def extract_json_from_content(content: str) -> str | None:
    """
    从 AI 返回的内容中提取 JSON 字符串

    Args:
        content: AI 返回的原始内容

    Returns:
        提取出的 JSON 字符串，或原始内容
    """
    if not content:
        return None

    # 处理 <thought> 标签
    think_match = re.search(r"</thought>\s*(.*?)$", content, re.DOTALL)
    if think_match:
        content = think_match.group(1)

    # 处理 <think> 标签
    think_match = re.search(r"</think>\s*(.*?)$", content, re.DOTALL)
    if think_match:
        content = think_match.group(1)

    # 处理 <thinking> 标签
    think_match = re.search(r"</thinking>\s*(.*?)$", content, re.DOTALL)
    if think_match:
        content = think_match.group(1)

    # 处理模型返回的thinking格式（如 "Thinking Process:" 开头的内容）
    # 查找 JSON 数组或对象的开始位置
    json_start = re.search(r'[\[{]', content)
    if json_start:
        # 从第一个 [ 或 { 开始截取
        content = content[json_start.start():]

    # 尝试提取 ```json ... ``` 或 ``` ... ``` 代码块
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return match.group(1)

    # 尝试匹配 JSON 数组格式
    json_match = re.search(r"\[\s*\{.*?\}\s*\]", content, re.DOTALL)
    if json_match:
        return json_match.group(0)

    # 尝试匹配 JSON 对象格式
    json_match = re.search(r"\{\s*.*?\s*\}", content, re.DOTALL)
    if json_match:
        return json_match.group(0)

    return content.strip()


def parse_json_safe(content: str) -> Tuple[Any | None, str | None]:
    """
    安全地解析 JSON

    Args:
        content: JSON 字符串

    Returns:
        (解析后的数据, 错误信息)
    """
    if not content:
        return None, "内容为空"

    try:
        data = json.loads(content)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON 解析错误：{str(e)}"


def extract_and_parse(content: str) -> Tuple[Any | None, str | None]:
    """
    从内容中提取并解析 JSON

    Args:
        content: AI 返回的原始内容

    Returns:
        (解析后的数据, 错误信息)
    """
    json_str = extract_json_from_content(content)
    if json_str is None:
        return None, "无法提取 JSON 内容"

    return parse_json_safe(json_str)