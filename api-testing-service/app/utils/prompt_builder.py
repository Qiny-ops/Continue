#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词构建器

集中管理所有 prompt 模板的变量替换逻辑。
"""

import json
from typing import Any, Dict, Optional

from app.prompts import (
    get_generate_testcase_prompt,
    get_dependency_prompt,
    get_fill_data_prompt,
    get_validate_prompt,
    get_failure_analysis_prompt,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """提示词构建器，统一处理模板变量替换"""

    @staticmethod
    def build(template: str, variables: Dict[str, Any]) -> str:
        """
        替换模板中的 {{variable}} 占位符。

        自动将 dict/list 类型序列化为 JSON 字符串。
        """
        prompt = template
        for key, val in variables.items():
            placeholder = "{{" + key + "}}"
            if isinstance(val, (dict, list)):
                val = json.dumps(val, ensure_ascii=False)
            else:
                val = str(val)
            prompt = prompt.replace(placeholder, val)
        return prompt

    @staticmethod
    def build_flow_query(query: str, extra_requirement: Optional[str] = None) -> str:
        """构建业务流查询"""
        return query

    @staticmethod
    def build_testcase_query(
        query: str = "对文档中的接口设计接口测试用例",
        extra_requirement: Optional[str] = None
    ) -> str:
        """构建测试用例生成查询"""
        template = get_generate_testcase_prompt()
        if extra_requirement:
            return template + "\n\n额外要求：" + extra_requirement
        if query and query != "对文档中的接口设计接口测试用例":
            return template + "\n\n额外要求：" + query
        return template

    @staticmethod
    def build_dependency_prompt(
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
    ) -> str:
        """构建依赖分析提示词"""
        return PromptBuilder.build(get_dependency_prompt(), {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
        })

    @staticmethod
    def build_fill_data_prompt(
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        dependency: Dict[str, Any],
        test_data: Dict[str, Any],
        base_url: str,
    ) -> str:
        """构建数据填充提示词"""
        return PromptBuilder.build(get_fill_data_prompt(), {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "dependency_json": dependency,
            "test_data": test_data,
            "base_url": base_url,
        })

    @staticmethod
    def build_validate_prompt(
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        execution_results: list,
    ) -> str:
        """构建校验提示词"""
        return PromptBuilder.build(get_validate_prompt(), {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "execution_results": execution_results,
        })

    @staticmethod
    def build_failure_analysis_prompt(
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        execution_results: list,
        validation_result: str,
    ) -> str:
        """构建失败分析提示词"""
        return PromptBuilder.build(get_failure_analysis_prompt(), {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "execution_results": execution_results,
            "validation_result": validation_result,
        })
