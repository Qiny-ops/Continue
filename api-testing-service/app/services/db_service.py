#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务模块（异步包装）

使用 asyncio.to_thread 将同步 pymysql 调用包装为异步，
避免阻塞事件循环，同时不引入额外依赖。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import pymysql

from app.config import get_settings

logger = logging.getLogger(__name__)


class DBService:
    """数据库服务（异步包装）"""

    def __init__(self):
        settings = get_settings()
        self.enabled = settings.db_enabled
        self.config = {
            "host": settings.db_host,
            "port": settings.db_port,
            "user": settings.db_user,
            "password": settings.db_password,
            "database": settings.db_name,
            "charset": "utf8mb4",
            "autocommit": True,
            "connect_timeout": 10,
            "read_timeout": 30,
            "write_timeout": 30
        }

    def _get_connection(self) -> pymysql.Connection:
        """获取新的数据库连接（每次调用创建新连接，避免跨线程共享导致协议错乱）"""
        return pymysql.connect(**self.config)

    async def close(self):
        """关闭连接（每次操作已独立管理连接生命周期，此处无需操作）"""
        pass

    async def save_test_cases(
        self,
        test_cases: List[Dict[str, Any]],
        document_id: Optional[int] = None,
        knowledge_id: Optional[str] = None
    ) -> int:
        """保存测试用例到数据库"""
        if not self.enabled:
            return 0

        def _save():
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                count = 0
                for case in test_cases:
                    try:
                        sql = """
                            INSERT INTO api_test_case
                            (case_id, api_name, precondition, testpoint, expectation, document_id, knowledge_id, last_run_status, priority, last_run_result, create_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                        cursor.execute(sql, (
                            case.get("id", str(count + 1)),
                            case.get("apiname", ""),
                            case.get("precondition", ""),
                            case.get("testpoint", ""),
                            case.get("expectation", ""),
                            document_id,
                            knowledge_id,
                            "pending",
                            "中",
                            ""
                        ))
                        count += 1
                    except Exception as e:
                        logger.error(f"保存测试用例失败：{case}, 错误：{e}")
                        continue
                cursor.close()
                return count
            finally:
                conn.close()

        return await asyncio.to_thread(_save)

    async def get_document_by_knowledge_id(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """根据 knowledge_id 获取文档"""
        if not self.enabled:
            return None

        def _get():
            conn = self._get_connection()
            try:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                sql = "SELECT * FROM api_document WHERE knowledge_id = %s ORDER BY id DESC LIMIT 1"
                cursor.execute(sql, (knowledge_id,))
                result = cursor.fetchone()
                cursor.close()
                return result
            finally:
                conn.close()

        return await asyncio.to_thread(_get)
