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


def get_generate_testcase_prompt() -> str:
    """获取测试用例生成提示词"""
    return load_prompt("generate_testcase.txt")


def get_dependency_prompt() -> str:
    """获取依赖分析提示词"""
    return load_prompt("get_dependency.txt")


def get_fill_data_prompt() -> str:
    """获取数据填充提示词"""
    return load_prompt("fill_test_data.txt")


def get_validate_prompt() -> str:
    """获取结果校验提示词"""
    return load_prompt("validate_testcase.txt")


def get_failure_analysis_prompt() -> str:
    """获取失败分析提示词"""
    return load_prompt("failure_analysis.txt")
