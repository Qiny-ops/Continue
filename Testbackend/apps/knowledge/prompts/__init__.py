#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库提示词模板管理
"""

import os
from functools import lru_cache


PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))


@lru_cache
def load_prompt(filename: str) -> str:
    """加载提示词模板文件"""
    filepath = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"提示词文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def get_batch_requirement_query(func_points_text: str, total_count: int) -> str:
    """
    获取批量需求查询提示词

    Args:
        func_points_text: 功能点列表文本（每行一个）
        total_count: 功能点总数

    Returns:
        格式化后的提示词
    """
    template = load_prompt("batch_requirement_query.txt")
    return template.replace("{{func_points_text}}", func_points_text).replace("{{total_count}}", str(total_count))


def get_single_requirement_query(func_point: str) -> str:
    """
    获取单条需求查询提示词

    Args:
        func_point: 单个功能点名称

    Returns:
        格式化后的提示词
    """
    template = load_prompt("single_requirement_query.txt")
    return template.replace("{{func_point}}", func_point)