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

import ipaddress
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 禁止访问的受限主机（SSRF 防护：云元数据、链路本地等）
_BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata", "localhost.localstack.cloud"}


def _validate_target_url(url: str, block_private: bool) -> Optional[str]:
    """校验目标 URL 是否允许访问。返回 None 表示允许，否则返回错误原因。

    重点拦截云元数据地址与非 http(s) 协议，避免凭据泄露；本服务用于执行接口测试，
    默认允许访问内网测试服务器（block_private=False），如需更严格隔离可开启
    block_private_targets 配置。
    """
    if not url:
        return "目标 URL 为空"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return f"不支持的协议: {parsed.scheme}"
    host = (parsed.hostname or "").lower()
    if not host:
        return "缺少主机名"
    if host in _BLOCKED_HOSTS:
        return f"禁止访问受限地址: {host}"
    try:
        ip = ipaddress.ip_address(host)
        # 注意：回环地址(127.0.0.1 / localhost)默认放行——本服务正是用来对本地/内网
        # 测试服务器发起请求（默认 api_base_url=http://127.0.0.1:8000）。最关键的云元数据
        # 169.254.169.254 属于链路本地段，已被下方 is_link_local 拦截。
        if ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return f"禁止访问受限 IP: {host}"
        if block_private and ip.is_private:
            return f"禁止访问私网 IP: {host}（如需测试内网请关闭 block_private_targets）"
    except ValueError:
        # 域名：无法在不做 DNS 解析的情况下判定私网，依赖 API Key 鉴权与网络隔离
        pass
    return None


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
        self.base_url = base_url
        self.execution_history: List[ExecutionResult] = []
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（长生命周期）"""
        if self._client is None or self._client.is_closed:
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
        """执行单个接口"""
        start_time = time.time()

        # 构造完整 URL
        api_url = api_info.get("api_url", "")
        if not api_url.startswith("http"):
            api_url = self.base_url + api_url

        # SSRF 防护：拦截非 http(s)、云元数据、受限 IP 等目标地址
        settings = get_settings()
        validation_err = _validate_target_url(api_url, settings.block_private_targets)
        if validation_err:
            logger.warning(f"拒绝访问目标地址: {api_url} - {validation_err}")
            duration_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                run_num=api_info.get("run_num", 0),
                api_name=api_info.get("api_name", ""),
                api_url=api_url,
                method=api_info.get("method", "GET").upper(),
                request={
                    "method": api_info.get("method", "GET").upper(),
                    "url": api_url,
                    "body": api_info.get("request_body", {}),
                    "params": api_info.get("params", api_info.get("query_params", {})),
                    "headers": api_info.get("headers", {}),
                },
                response=None,
                status_code=None,
                expected_status=api_info.get("expected_status"),
                success=False,
                duration_ms=duration_ms,
                error=validation_err,
            )

        method = api_info.get("method", "GET").upper()
        request_body = api_info.get("request_body", {})
        headers = api_info.get("headers", {})
        params = api_info.get("params", api_info.get("query_params", {}))

        request_data = {
            "method": method,
            "url": api_url,
            "body": request_body,
            "params": params,
            "headers": headers
        }

        logger.info(f"执行请求: {method} {api_url}")
        logger.debug(f"请求详情: headers={headers}, body={request_body}, params={params}")

        try:
            client = await self._get_client()

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

            duration_ms = int((time.time() - start_time) * 1000)

            try:
                response_body = response.json()
            except Exception:
                response_body = {"text": response.text}

            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "cookies": dict(response.cookies),
                "body": response_body
            }

            expected_status = api_info.get("expected_status")
            if expected_status is not None:
                success = self._match_status(expected_status, response.status_code)
            else:
                success = 200 <= response.status_code < 300

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
                extract_vars=api_info.get("extract_vars")
            )

        self.execution_history.append(result)
        logger.info(f"执行接口: {result.api_name}, 状态: {result.success}, 耗时: {result.duration_ms}ms")

        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """获取执行历史（用于 AI 分析）"""
        return [
            {
                "run_num": r.run_num,
                "api_name": r.api_name,
                "api_url": r.api_url,
                "method": r.method,
                "request": r.request,
                "response": r.response,
                "status_code": r.status_code,
                "expected_status": r.expected_status,
                "success": r.success,
                "duration_ms": r.duration_ms,
                "error": r.error,
            }
            for r in self.execution_history
        ]

    def clear_history(self):
        """清空执行历史"""
        self.execution_history = []

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
