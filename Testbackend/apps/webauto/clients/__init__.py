# -*- coding: utf-8 -*-
"""
Web Automation Service 客户端

负责与 web-automation-service 微服务通信，支持 SSE 流式响应（对齐 apitest 客户端）。
"""

import json
import logging
from typing import Any, Dict, Generator, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class WebAutomationServiceError(Exception):
    """Web 自动化服务异常"""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class WebAutomationClient:
    """
    Web Automation Service 客户端

    支持流式调用，直接透传 SSE 响应。
    """

    def __init__(self):
        self.base_url = getattr(
            settings,
            'WEB_AUTOMATION_SERVICE_URL',
            'http://localhost:8003'
        )
        self.timeout = getattr(
            settings,
            'WEB_AUTOMATION_SERVICE_TIMEOUT',
            180.0
        )
        # 调用微服务时携带的 API Key（与微服务侧 API_KEY 对应；空=开发模式不强制）
        self.api_key = getattr(settings, 'WEB_AUTOMATION_API_KEY', '')

    def _api_key_headers(self) -> Dict[str, str]:
        if self.api_key:
            return {"X-API-Key": self.api_key}
        return {}

    # ==================== 流式接口 ====================

    def plan_stream(
        self,
        testcase: Dict[str, Any],
        start_url: str,
        site_hint: str = "",
        kb_id: str = "",
        kb_api_key: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """规划 action_list - 流式返回"""
        url = f"{self.base_url}/api/v1/webtest/plan"
        payload = {
            "testcase": testcase,
            "start_url": start_url,
            "site_hint": site_hint,
            "kb_id": kb_id,
            "kb_api_key": kb_api_key,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload, headers=self._api_key_headers()) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("Web Automation Service timeout: plan")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"Web Automation Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            # 对端（微服务）连接中断。多数情况是客户端已断开导致上游取消，属正常生命周期；
            # RemoteProtocolError（incomplete chunked read）更常见于断连，降级为 warning，避免误报。
            if isinstance(e, httpx.RemoteProtocolError):
                logger.warning(f"Web Automation Service 连接被对端中断（可能客户端已断开）: {e}")
            else:
                logger.error(f"Web Automation Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    def execute_stream(
        self,
        testcase: Dict[str, Any],
        start_url: str,
        action_list: Optional[list] = None,
        site_hint: str = "",
        kb_id: str = "",
        kb_api_key: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """执行 Web 自动化用例 - 流式返回"""
        url = f"{self.base_url}/api/v1/webtest/execute"
        payload = {
            "testcase": testcase,
            "start_url": start_url,
            "action_list": action_list,
            "site_hint": site_hint,
            "kb_id": kb_id,
            "kb_api_key": kb_api_key,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload, headers=self._api_key_headers()) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.TimeoutException:
            logger.error("Web Automation Service timeout: execute")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': '服务响应超时'}})}\n\n"
        except httpx.HTTPStatusError as e:
            logger.error(f"Web Automation Service error: {e.response.status_code}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'服务异常: {e.response.status_code}'}})}\n\n"
        except httpx.RequestError as e:
            # 对端（微服务）连接中断。多数情况是客户端已断开导致上游取消，属正常生命周期；
            # RemoteProtocolError（incomplete chunked read）更常见于断连，降级为 warning，避免误报。
            if isinstance(e, httpx.RemoteProtocolError):
                logger.warning(f"Web Automation Service 连接被对端中断（可能客户端已断开）: {e}")
            else:
                logger.error(f"Web Automation Service connection error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'连接失败: {str(e)}'}})}\n\n"

    # ==================== 同步接口 ====================

    def health_check(self) -> bool:
        """检查服务健康状态"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/api/v1/health",
                    headers=self._api_key_headers(),
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Web Automation Service health check failed: {e}")
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
