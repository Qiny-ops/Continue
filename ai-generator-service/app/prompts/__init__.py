#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词模板管理
"""

import os
from functools import lru_cache
from typing import Dict


PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))


@lru_cache
def load_prompt(filename: str) -> str:
    """加载提示词模板文件"""
    filepath = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"提示词文件不存在: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


@lru_cache
def load_test_directions() -> Dict[str, str]:
    """加载测试方向提示词映射"""
    content = load_prompt("test_directions.txt")
    directions = {}

    for line in content.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            directions[key.strip()] = value.strip()

    return directions


def get_system_prompt() -> str:
    """获取系统提示词"""
    return load_prompt("testcase_generate.txt")


def get_test_direction_prompt(direction: str) -> str:
    """获取指定测试方向的提示词"""
    directions = load_test_directions()
    return directions.get(direction, directions.get("功能点测试", ""))
