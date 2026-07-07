#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESTful API 数据模型
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==================== 响应模型 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str


# ==================== 业务请求模型 ====================

class GetFlowParams(BaseModel):
    """获取接口业务流参数"""
    kb_id: str = Field(..., description="知识库 ID")
    query: str = Field(default="请分析这个接口的业务流", description="查询问题")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")


class GenerateTestCaseParams(BaseModel):
    """生成测试用例参数"""
    kb_id: str = Field(..., description="知识库 ID")
    query: str = Field(default="对文档中的接口设计接口测试用例", description="查询问题")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")
    save_to_db: bool = Field(default=False, description="是否保存到数据库")
    knowledge_id: Optional[str] = Field(default=None, description="知识库 ID（用于关联文档）")


class GetDependencyParams(BaseModel):
    """获取接口依赖参数"""
    case_id: str = Field(..., description="用例 ID")
    api_name: str = Field(..., description="接口名称")
    precondition: str = Field(default="", description="前置条件")
    testpoint: str = Field(..., description="测试点")
    expectation: str = Field(..., description="预期结果")
    kb_id: str = Field(..., description="知识库 ID")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")


class FillDataParams(BaseModel):
    """填充测试数据参数"""
    case_id: str = Field(..., description="用例 ID")
    api_name: str = Field(..., description="接口名称")
    precondition: str = Field(default="", description="前置条件")
    testpoint: str = Field(..., description="测试点")
    expectation: str = Field(..., description="预期结果")
    dependency: Dict[str, Any] = Field(..., description="依赖关系 JSON")
    test_data: Dict[str, Any] = Field(..., description="测试数据")
    kb_id: str = Field(..., description="知识库 ID")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")
    base_url: Optional[str] = Field(default=None, description="被 API 的基座 URL，不传则使用配置默认值")


class ExecuteTestCaseParams(BaseModel):
    """执行测试用例参数"""
    case_id: str = Field(..., description="用例 ID")
    api_name: str = Field(..., description="接口名称")
    precondition: str = Field(default="", description="前置条件")
    testpoint: str = Field(..., description="测试点")
    expectation: str = Field(..., description="预期结果")
    run_list: List[Dict[str, Any]] = Field(..., description="接口执行列表")
    test_data: Dict[str, Any] = Field(default={}, description="测试数据")
    kb_id: str = Field(..., description="知识库 ID")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")
    base_url: Optional[str] = Field(default=None, description="被 API 的基座 URL，不传则使用配置默认值")


class ValidateTestCaseParams(BaseModel):
    """校验测试用例参数"""
    case_id: str = Field(..., description="用例 ID")
    api_name: str = Field(..., description="接口名称")
    precondition: str = Field(default="", description="前置条件")
    testpoint: str = Field(..., description="测试点")
    expectation: str = Field(..., description="预期结果")
    execution_results: List[Dict[str, Any]] = Field(..., description="执行结果列表")
    kb_id: str = Field(..., description="知识库 ID")
    kb_api_key: Optional[str] = Field(default=None, description="知识库 API 密钥")


class LLMChatParams(BaseModel):
    """LLM 对话参数"""
    query: str = Field(..., description="用户问题")
    system_message: Optional[str] = Field(default=None, description="系统提示词")