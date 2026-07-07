#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库服务客户端 - WeKnora RESTful API

支持 WeKnora 知识库服务的 RESTful API 调用。
"""

import json
from typing import Any, Dict, Optional

import httpx

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KBError(Exception):
    """知识库服务调用错误"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class KBClient:
    """知识库服务客户端（WeKnora RESTful API）"""

    def __init__(self, base_url: Optional[str] = None, kb_api_key: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.kb_base_url
        self.api_key = kb_api_key or settings.kb_api_key
        self.agent_id = settings.kb_agent_id
        self.temperature = settings.kb_temperature
        self.max_tokens = settings.kb_max_tokens
        self.timeout = 120.0

    def _get_headers(self, kb_api_key: Optional[str] = None) -> Dict[str, str]:
        """获取请求头（WeKnora 使用 X-API-Key）"""
        api_key = kb_api_key or self.api_key
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        return headers

    async def create_session(
        self,
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建知识库会话

        WeKnora API: POST /sessions
        """
        logger.info(f"创建会话: kb_id={kb_id}")

        url = f"{self.base_url}/sessions"
        payload = {"knowledge_base_id": kb_id}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers=self._get_headers(kb_api_key)
            )

            result = response.json()

            if not result.get("success", False):
                error = result.get("error", "Unknown error")
                logger.error(f"创建会话失败: {error}")
                raise KBError(code=-1, message=str(error))

            data = result.get("data", {})
            session_id = data.get("id")
            logger.info(f"会话创建成功: session_id={session_id}")

            return {"id": session_id, "data": data}

    async def destroy_session(
        self,
        session_id: str,
        kb_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        销毁知识库会话

        WeKnora API: DELETE /sessions/{session_id}
        """
        logger.info(f"销毁会话: session_id={session_id}")

        url = f"{self.base_url}/sessions/{session_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                url,
                headers=self._get_headers(kb_api_key)
            )

            result = response.json()
            logger.info(f"会话已销毁: session_id={session_id}")

            return result

    async def chat_stream(
        self,
        query: str,
        session_id: str,
        kb_id: str,
        kb_api_key: Optional[str] = None,
        knowledge_id: Optional[str] = None
    ):
        """
        调用 Agent 对话流式问答

        WeKnora API: POST /agent-chat/{session_id}

        Args:
            query: 查询内容
            session_id: 会话 ID
            kb_id: 知识库 ID
            kb_api_key: API Key
            knowledge_id: 指定的知识文档 ID

        Yields:
            统一格式事件: {"type": "chunk", "data": {"content": "..."}}
        """
        url = f"{self.base_url}/agent-chat/{session_id}"
        headers = self._get_headers(kb_api_key)

        # 构建 mentioned_items，如果指定了文件则只包含该文件
        mentioned_items = []
        if knowledge_id:
            mentioned_items.append({
                'id': knowledge_id,
                'name': f"File-{knowledge_id[-8:]}",
                'type': 'file'
            })
        else:
            mentioned_items.append({
                'id': kb_id,
                'name': f"KB-{kb_id[-8:]}",
                'type': 'kb',
                'kb_type': 'document'
            })

        payload = {
            "query": query,
            "agent_enabled": True,
            "web_search_enabled": False,
            # 如果指定了文件，不传递知识库 ID，避免检索整个知识库
            "knowledge_base_ids": [] if knowledge_id else [kb_id],
            "knowledge_ids": [knowledge_id] if knowledge_id else [],
            "mentioned_items": mentioned_items,
            "agent_id": self.agent_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        logger.info(f"开始调用 agent-chat: session_id={session_id}, knowledge_id={knowledge_id}, mentioned_items={mentioned_items}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers
            ) as response:
                # 检查响应状态
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"agent-chat 请求失败: status={response.status_code}, body={error_body.decode()}")
                    yield {
                        "type": "error",
                        "data": {"message": f"知识库服务返回错误: {response.status_code}"}
                    }
                    return

                async for line in response.aiter_lines():
                    logger.info(f"收到 SSE 行: {line[:200] if line else 'empty'}...")
                    if line and line.startswith("data:"):
                        try:
                            # 解析 SSE 数据
                            data = json.loads(line[5:].strip())

                            # 转换为统一格式
                            response_type = data.get("response_type")
                            logger.info(f"响应类型: {response_type}")

                            if response_type == "answer":
                                content = data.get("content", "")
                                if content:
                                    yield {
                                        "type": "chunk",
                                        "data": {"content": content}
                                    }

                            elif response_type == "thinking":
                                content = data.get("content", "")
                                if content:
                                    yield {
                                        "type": "thinking",
                                        "data": {"content": content}
                                    }

                            elif response_type == "reference":
                                items = data.get("items", [])
                                if items:
                                    yield {
                                        "type": "reference",
                                        "data": {"items": items}
                                    }

                            elif response_type == "error":
                                message = data.get("message", "Unknown error")
                                yield {
                                    "type": "error",
                                    "data": {"message": message}
                                }

                        except json.JSONDecodeError:
                            continue

        logger.info(f"agent-chat 完成: session_id={session_id}")
