# -*- coding: utf-8 -*-
"""
AI Code Check Service 客户端

对齐 apps/webauto/clients/__init__.py 范式：
- base_url 取自 settings.AICHECK_SERVICE_URL
- X-API-Key 头（与微服务侧 API_KEY 对应；空=开发模式不强制）
- timeout 默认 300
"""
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class AiCheckServiceError(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AiCheckClient:
    """AI Code Check Service 客户端（同步）"""

    def __init__(self):
        self.base_url = getattr(
            settings, "AICHECK_SERVICE_URL", "http://localhost:8004"
        )
        self.timeout = float(getattr(settings, "AICHECK_SERVICE_TIMEOUT", 300))
        self.api_key = getattr(settings, "AICHECK_API_KEY", "")

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1{path}"

    # ==================== 同步接口 ====================

    def trigger(
        self,
        project_name: str,
        repository_url: str,
        test_cases: List[Dict[str, Any]],
        branch: str = "",
        commit_sha: str = "",
        base_sha: str = "",
        case_source: str = "inline",
        project_code: str = "",
        gate: Optional[Dict[str, Any]] = None,
        trigger_source: str = "manual",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "project_name": project_name,
            "repository_url": repository_url,
            "case_source": case_source,
            "trigger_source": trigger_source,
        }
        if branch:
            payload["branch"] = branch
        if commit_sha:
            payload["commit_sha"] = commit_sha
        if base_sha:
            payload["base_sha"] = base_sha
        if case_source == "inline":
            payload["test_cases"] = test_cases
        elif case_source == "platform":
            payload["project_code"] = project_code
        elif case_source == "file":
            payload["test_case_file"] = project_code  # filename 复用
        if gate:
            payload["gate"] = gate

        try:
            with httpx.Client(timeout=30) as client:
                r = client.post(self._url("/check/trigger"), json=payload, headers=self._headers())
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            raise AiCheckServiceError(
                f"trigger 失败: {e.response.status_code} {e.response.text[:200]}"
            )
        except Exception as e:
            raise AiCheckServiceError(f"trigger 异常: {e}")

    def get_task(self, task_id: str) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(self._url(f"/check/{task_id}"), headers=self._headers())
                if r.status_code == 404:
                    raise AiCheckServiceError("任务不存在", code="NOT_FOUND")
                r.raise_for_status()
                return r.json()
        except AiCheckServiceError:
            raise
        except Exception as e:
            raise AiCheckServiceError(f"get_task 异常: {e}")

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(self._url("/health"), headers=self._headers())
                return r.status_code == 200
        except Exception as e:
            logger.error(f"aicheck 健康检查失败: {e}")
            return False
