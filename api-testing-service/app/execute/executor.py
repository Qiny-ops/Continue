#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 测试执行器 - 通用执行框架

支持：
- HTTP/HTTPS 协议
- GET/POST/PUT/DELETE 等方法
- Session/Cookie 自动管理
- 实时执行结果返回
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """接口执行结果"""
    run_num: int
    api_name: str
    api_url: str
    method: str
    request: Dict[str, Any]
    response: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    expected_status: Optional[Any] = None
    success: bool = False
    duration_ms: int = 0
    error: Optional[str] = None
    extract_vars: Optional[Dict[str, str]] = None


class ApiTestExecutor:
    """API 测试执行器"""

    def __init__(self, base_url: str = ""):
        """
        初始化执行器

        Args:
            base_url: 基座 URL，如 http://127.0.0.1:8000
        """
        self.base_url = base_url
        self.execution_history: List[ExecutionResult] = []
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @staticmethod
    def _match_status(expected: Any, actual: int) -> bool:
        """
        判断实际状态码是否匹配预期

        规则：
        - 精确匹配：expected=200, actual=200 → True
        - 错误场景同类匹配：expected=401, actual=403 → True（都是4XX）
        - 通配符匹配：expected="4XX", actual=403 → True
        - 范围匹配：expected="400-499", actual=403 → True
        - 正常场景不匹配：expected=200, actual=401 → False
        """
        if isinstance(expected, int):
            if 400 <= expected < 600:
                # 错误场景：同类匹配（4xx匹配4xx，5xx匹配5xx）
                return (expected // 100) == (actual // 100)
            return expected == actual

        if isinstance(expected, str):
            upper = expected.upper()
            if upper.endswith("XX"):
                try:
                    base = int(upper[0]) * 100
                    return base <= actual < base + 100
                except ValueError:
                    return False
            if "-" in expected:
                try:
                    parts = expected.split("-")
                    return int(parts[0]) <= actual <= int(parts[1])
                except (ValueError, IndexError):
                    return False
            try:
                exp_int = int(expected)
                if 400 <= exp_int < 600:
                    return (exp_int // 100) == (actual // 100)
                return exp_int == actual
            except ValueError:
                return False

        return False

    async def execute_api(self, api_info: Dict[str, Any]) -> ExecutionResult:
        """
        执行单个接口

        Args:
            api_info: 接口信息，包含 api_url, method, request_body 等

        Returns:
            执行结果
        """
        start_time = time.time()

        # 构造完整 URL
        api_url = api_info.get("api_url", "")
        if not api_url.startswith("http"):
            api_url = self.base_url + api_url

        # 注意：不再去掉 /api 前缀，保持原始路径

        method = api_info.get("method", "GET").upper()
        request_body = api_info.get("request_body", {})
        headers = api_info.get("headers", {})
        params = api_info.get("params", api_info.get("query_params", {}))

        # 准备请求
        request_data = {
            "method": method,
            "url": api_url,
            "body": request_body,
            "params": params,
            "headers": headers
        }

        # 记录请求详情
        logger.info(f"执行请求: {method} {api_url}")
        logger.info(f"expected_status: {api_info.get('expected_status')}, 类型: {type(api_info.get('expected_status'))}")
        logger.debug(f"请求详情: headers={headers}, body={request_body}, params={params}")

        try:
            client = await self._get_client()

            # 发送请求
            if method == "GET":
                response = await client.get(api_url, params=params, headers=headers)
            elif method == "POST":
                content_type = headers.get("Content-Type", "")
                if "application/json" in content_type:
                    response = await client.post(api_url, json=request_body, params=params, headers=headers)
                else:
                    response = await client.post(api_url, data=request_body, params=params, headers=headers)
            elif method == "PUT":
                response = await client.put(api_url, json=request_body, params=params, headers=headers)
            elif method == "DELETE":
                response = await client.delete(api_url, params=params, headers=headers)
            else:
                response = await client.request(method, api_url, json=request_body, params=params, headers=headers)

            # 解析响应
            duration_ms = int((time.time() - start_time) * 1000)

            try:
                response_body = response.json()
            except:
                response_body = {"text": response.text}

            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "cookies": dict(response.cookies),
                "body": response_body
            }

            # 判断是否成功：基于 expected_status 或默认 HTTP 2xx
            expected_status = api_info.get("expected_status")
            if expected_status is not None:
                success = self._match_status(expected_status, response.status_code)
            else:
                success = 200 <= response.status_code < 300

            # 记录响应信息
            if not success:
                logger.warning(f"接口未达预期: {method} {api_url}, 状态码: {response.status_code}, 预期: {expected_status or '2xx'}")

            result = ExecutionResult(
                run_num=api_info.get("run_num", 0),
                api_name=api_info.get("api_name", ""),
                api_url=api_url,
                method=method,
                request=request_data,
                response=response_data,
                status_code=response.status_code,
                expected_status=api_info.get("expected_status"),
                success=success,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            result = ExecutionResult(
                run_num=api_info.get("run_num", 0),
                api_name=api_info.get("api_name", ""),
                api_url=api_url,
                method=method,
                request=request_data,
                response=None,
                status_code=None,
                expected_status=api_info.get("expected_status"),
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                extract_vars=api_info.get("extract_vars")  # 保存原始的 extract_vars
            )

        # 记录执行历史
        self.execution_history.append(result)
        logger.info(f"执行接口: {result.api_name}, 状态: {result.success}, 耗时: {result.duration_ms}ms")

        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """获取执行历史（用于 AI 分析）"""
        history = []
        for result in self.execution_history:
            history.append({
                "run_num": result.run_num,
                "api_name": result.api_name,
                "api_url": result.api_url,
                "method": result.method,
                "request": result.request,
                "response": result.response,
                "status_code": result.status_code,
                "expected_status": result.expected_status,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "error": result.error,
            })
        return history

    def clear_history(self):
        """清空执行历史"""
        self.execution_history = []

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
