#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库会话生命周期管理

统一管理 create_session → chat → destroy_session 的 try/finally 模式。
"""

from typing import Any, Dict, Optional

from app.services.kb_client import KBClient, KBError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KBSession:
    """知识库会话上下文管理器"""

    def __init__(self, kb_client: KBClient, kb_id: str, kb_api_key: Optional[str] = None):
        self.kb_client = kb_client
        self.kb_id = kb_id
        self.kb_api_key = kb_api_key
        self.session_id: Optional[str] = None

    async def __aenter__(self) -> "KBSession":
        session_result = await self.kb_client.create_session(self.kb_id, self.kb_api_key)
        self.session_id = session_result.get("id")
        if not self.session_id:
            raise KBError(code=-1, message="创建会话失败")
        logger.info(f"会话创建成功：session_id={self.session_id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session_id:
            try:
                await self.kb_client.destroy_session(self.session_id, self.kb_api_key)
                logger.info(f"会话已销毁：session_id={self.session_id}")
            except Exception as e:
                logger.error(f"销毁会话失败：{e}")
        return False

    async def chat_stream(self, query: str, knowledge_id: Optional[str] = None, temperature: Optional[float] = None):
        """调用 kb.chat 流式问答"""
        async for event in self.kb_client.chat_stream(
            query=query,
            session_id=self.session_id,
            kb_id=self.kb_id,
            kb_api_key=self.kb_api_key,
            knowledge_id=knowledge_id,
            temperature=temperature
        ):
            yield event
