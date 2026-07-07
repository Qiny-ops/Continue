# -*- coding: utf-8 -*-
"""
接口测试微服务客户端

负责与 api-testing-service 微服务通信，支持 SSE 流式响应
"""

import json
import logging
from typing import Any, Dict, Generator, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class ApiTestingServiceError(Exception):
    """接口测试服务异常"""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ApiTestingClient:
    """
    API Testing Service 客户端

    支持流式调用，直接透传 SSE 响应
    """

    def __init__(self):
        self.base_url = getattr(
            settings,
            'API_TESTING_SERVICE_URL',
            'http://localhost:8002'
        )
        self.timeout = getattr(
            settings,
            'API_TESTING_SERVICE_TIMEOUT',
            120.0
        )
        self.kb_api_key = getattr(settings, 'WEKNORA_API_KEY', '')

    # ==================== 流式接口 ====================

    def get_flow_stream(
        self,
        kb_id: str,
        query: str,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        获取接口业务流 - 流式返回

        Args:
            kb_id: 知识库 ID
            query: 查询问题
            kb_api_key: 知识库 API Key

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/flow"
        payload = {
            "kb_id": kb_id,
            "query": query,
            "kb_api_key": kb_api_key or self.kb_api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: get_flow")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def generate_testcase_stream(
        self,
        kb_id: str,
        knowledge_ids: Optional[list] = None,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        生成接口测试用例 - 流式返回

        Args:
            kb_id: 知识库 ID
            knowledge_ids: 知识文档 ID 列表（可选，取第一个传给微服务）
            kb_api_key: 知识库 API Key

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/testcase/generate"
        payload = {
            "kb_id": kb_id,
            "kb_api_key": kb_api_key or self.kb_api_key,
            "save_to_db": False,  # 不在微服务存库，由 Django 处理
        }

        # 如果指定了知识文档 ID，取第一个传给微服务（微服务只支持单个 knowledge_id）
        if knowledge_ids and len(knowledge_ids) > 0:
            payload["knowledge_id"] = knowledge_ids[0]

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: generate_testcase")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def get_dependency_stream(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        获取接口依赖关系 - 流式返回

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/dependency"
        payload = {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "kb_id": kb_id,
            "kb_api_key": kb_api_key or self.kb_api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: get_dependency")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def fill_testdata_stream(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        dependency: Dict[str, Any],
        test_data: Dict[str, Any],
        kb_id: str,
        base_url: str,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        填充测试数据 - 流式返回

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/testdata/fill"
        payload = {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "dependency": dependency,
            "test_data": test_data,
            "kb_id": kb_id,
            "base_url": base_url,
            "kb_api_key": kb_api_key or self.kb_api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: fill_testdata")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def execute_testcase_stream(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        run_list: list,
        test_data: Dict[str, Any],
        kb_id: str,
        base_url: str,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        执行测试用例 - 流式返回

        Args:
            case_id: 用例 ID
            api_name: 接口名称
            precondition: 前置条件
            testpoint: 测试点
            expectation: 预期结果
            run_list: 接口执行列表
            test_data: 测试数据
            kb_id: 知识库 ID
            base_url: 基础 URL
            kb_api_key: 知识库 API Key

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/testcase/execute"
        payload = {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "run_list": run_list,
            "test_data": test_data,
            "kb_id": kb_id,
            "base_url": base_url,
            "kb_api_key": kb_api_key or self.kb_api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: execute_testcase")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def validate_testcase_stream(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        execution_results: list,
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        校验测试用例 - 流式返回

        Yields:
            SSE 格式的数据行
        """
        url = f"{self.base_url}/api/v1/testcase/validate"
        payload = {
            "case_id": case_id,
            "api_name": api_name,
            "precondition": precondition,
            "testpoint": testpoint,
            "expectation": expectation,
            "execution_results": execution_results,
            "kb_id": kb_id,
            "kb_api_key": kb_api_key or self.kb_api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("API Testing Service timeout: validate_testcase")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"API Testing Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            logger.error(f"API Testing Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    # ==================== 同步接口 ====================

    def health_check(self) -> bool:
        """检查服务健康状态"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.base_url}/api/v1/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"API Testing Service health check failed: {e}")
            return False

    def get_service_info(self) -> Optional[Dict[str, Any]]:
        """获取服务信息"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.base_url}/")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get service info error: {e}")
            return None
