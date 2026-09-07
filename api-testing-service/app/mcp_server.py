#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Testing MCP Server

将 API Testing 功能暴露为 MCP Tools，供 SkillFramework 调用。

使用方式：
    python -m app.mcp_server
"""

import asyncio
import json
import logging
import os
import re
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from app.config import get_settings
from app.services.kb_client import KBClient
from app.services.llm_service import LLMService
from app.services.db_service import DBService
from app.engine import TestEngine

# 配置日志 - MCP Server 使用 stdio 通信，日志输出到 stderr 会干扰通信
debug_mode = os.environ.get('API_TESTING_DEBUG', 'false').lower() == 'true'

if debug_mode:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stderr
    )
else:
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        stream=sys.stderr
    )

logger = logging.getLogger("apitest-mcp")


class ApiTestMcpServer:
    """API Testing MCP Server"""

    # ---- 公共响应格式（所有工具统一返回 JSON） ----

    @staticmethod
    def _error(message: str) -> str:
        """统一错误响应"""
        return json.dumps({"success": False, "error": message}, ensure_ascii=False)

    @staticmethod
    def _ok(**fields) -> str:
        """统一成功响应（content 为必填展示文本，其余为结构化字段）"""
        return json.dumps({"success": True, **fields}, ensure_ascii=False)

    async def _collect_stream(self, engine_method, **kwargs):
        """通用流式事件收集，返回原始事件列表；异常统一捕获转 JSON 错误"""
        events = []
        async for event in engine_method(**kwargs):
            events.append(event)
        return events

    @staticmethod
    def _handle_events(events: list, handlers: dict) -> dict:
        """
        按事件类型分发处理，返回 handlers 累积的结果字典。
        
        handlers 格式: {"event_type": lambda ctx, data: None}
        每个 handler 通过修改 ctx 字典来累积结果。
        """
        ctx = {}
        for event in events:
            event_type = event.get("type", "unknown")
            event_data = event.get("data", {})
            handler = handlers.get(event_type)
            if handler:
                handler(ctx, event_data)
        return ctx

    def __init__(self):
        """初始化 MCP Server"""
        self.settings = get_settings()
        logger.info("配置加载完成")

        # 初始化统一引擎
        kb_client = KBClient()
        llm_service = LLMService()
        db_service = DBService()

        self.engine = TestEngine(
            kb_client=kb_client,
            llm_service=llm_service,
            db_service=db_service
        )

        # 创建 MCP Server
        self.server = FastMCP("api-testing")

        # 注册工具
        self._register_tools()

        logger.info("API Testing MCP Server 初始化完成")

    def _register_tools(self):
        """注册所有 MCP 工具"""
        _collect = self._collect_stream
        _err = self._error
        _ok = self._ok

        # ========== Tool 1: get_api_flow ==========
        @self.server.tool()
        async def get_api_flow(
            kb_id: str,
            query: str = "请分析这个接口的业务流",
            kb_api_key: Optional[str] = None
        ) -> str:
            """获取接口的业务流。当用户需要分析接口的业务流程、调用顺序时使用。参数：kb_id（必填）、query（可选）、kb_api_key（可选）"""
            logger.info(f"调用 get_api_flow: kb_id={kb_id}, query={query[:50]}...")
            try:
                events = await _collect(
                    self.engine.get_flow, kb_id=kb_id, query=query, kb_api_key=kb_api_key
                )
                result_text = ""
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "chunk":
                        result_text += event_data.get("content", "")
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                return _ok(content=result_text or "未获取到业务流信息")
            except Exception as e:
                logger.exception("get_api_flow 执行失败")
                return _err(f"执行失败：{str(e)}")

        # ========== Tool 2: generate_testcases ==========
        @self.server.tool()
        async def generate_testcases(
            kb_id: str,
            query: str = "对文档中的接口设计接口测试用例",
            save_to_db: bool = False,
            knowledge_id: Optional[str] = None,
            kb_api_key: Optional[str] = None
        ) -> str:
            """生成接口测试用例。基于知识库中的接口文档，自动生成测试用例。参数：kb_id（必填）、query（可选）、save_to_db（可选）、knowledge_id（可选）、kb_api_key（可选）"""
            logger.info(f"调用 generate_testcases: kb_id={kb_id}")
            try:
                events = await _collect(
                    self.engine.generate_testcase, kb_id=kb_id, query=query,
                    kb_api_key=kb_api_key, save_to_db=save_to_db, knowledge_id=knowledge_id
                )
                result_text = ""
                test_cases = []
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "chunk":
                        result_text += event_data.get("content", "")
                    elif event_type == "saved":
                        test_cases.append(f"已保存 {event_data.get('count', 0)} 条测试用例")
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                result = result_text
                if test_cases:
                    result += "\n\n" + "\n".join(test_cases)
                return _ok(content=result, run_list=_parse_run_list(result_text))
            except Exception as e:
                logger.exception("generate_testcases 执行失败")
                return _err(f"执行失败：{str(e)}")

        # ========== Tool 3: get_api_dependency ==========
        @self.server.tool()
        async def get_api_dependency(
            case_id: str,
            api_name: str,
            precondition: str,
            testpoint: str,
            expectation: str,
            kb_id: str,
            kb_api_key: Optional[str] = None
        ) -> str:
            """获取接口依赖关系。分析测试用例执行所需的接口依赖和执行顺序。参数：case_id、api_name、precondition、testpoint、expectation、kb_id（均必填）、kb_api_key（可选）"""
            logger.info(f"调用 get_api_dependency: case_id={case_id}, api_name={api_name}")
            try:
                events = await _collect(
                    self.engine.get_api_dependency,
                    case_id=case_id, api_name=api_name, precondition=precondition,
                    testpoint=testpoint, expectation=expectation, kb_id=kb_id, kb_api_key=kb_api_key
                )
                result_text = ""
                dependency_info = None
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "chunk":
                        result_text += event_data.get("content", "")
                    elif event_type == "result":
                        dependency_info = event_data.get("dependency", {})
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                result = result_text
                if dependency_info:
                    result += f"\n\n依赖信息：{json.dumps(dependency_info, ensure_ascii=False, indent=2)}"
                return _ok(content=result, dependency=dependency_info)
            except Exception as e:
                logger.exception("get_api_dependency 执行失败")
                return _err(f"执行失败：{str(e)}")

        # ========== Tool 4: fill_testdata ==========
        @self.server.tool()
        async def fill_testdata(
            case_id: str,
            api_name: str,
            precondition: str,
            testpoint: str,
            expectation: str,
            dependency: dict,
            test_data: dict,
            kb_id: str,
            base_url: str = "http://127.0.0.1:8000",
            kb_api_key: Optional[str] = None
        ) -> str:
            """填充测试数据。根据接口依赖和测试数据要求，自动填充实际的测试参数。参数：case_id、api_name、precondition、testpoint、expectation、dependency、test_data、kb_id（均必填）、base_url（可选）、kb_api_key（可选）"""
            logger.info(f"调用 fill_testdata: case_id={case_id}")
            try:
                events = await _collect(
                    self.engine.fill_test_data,
                    case_id=case_id, api_name=api_name, precondition=precondition,
                    testpoint=testpoint, expectation=expectation, dependency=dependency,
                    test_data=test_data, kb_id=kb_id, kb_api_key=kb_api_key, base_url=base_url
                )
                result_text = ""
                filled_data = None
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "chunk":
                        result_text += event_data.get("content", "")
                    elif event_type == "result":
                        filled_data = event_data.get("filled_data", {})
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                result = result_text
                if filled_data:
                    result += f"\n\n填充数据：{json.dumps(filled_data, ensure_ascii=False, indent=2)}"
                return _ok(content=result, filled_data=filled_data, dependency=dependency)
            except Exception as e:
                logger.exception("fill_testdata 执行失败")
                return _err(f"执行失败：{str(e)}")

        # ========== Tool 5: execute_testcase ==========
        @self.server.tool()
        async def execute_testcase(
            case_id: str,
            api_name: str,
            precondition: str,
            testpoint: str,
            expectation: str,
            run_list: list,
            test_data: dict,
            kb_id: str,
            base_url: str = "http://127.0.0.1:8000",
            kb_api_key: Optional[str] = None
        ) -> str:
            """执行测试用例。按依赖顺序执行接口测试，自动分析参数依赖。参数：case_id、api_name、precondition、testpoint、expectation、run_list、test_data、kb_id（均必填）、base_url（可选）、kb_api_key（可选）"""
            logger.info(f"调用 execute_testcase: case_id={case_id}, run_list 数量={len(run_list)}")
            try:
                events = await _collect(
                    self.engine.execute_testcase,
                    case_id=case_id, api_name=api_name, precondition=precondition,
                    testpoint=testpoint, expectation=expectation, run_list=run_list,
                    test_data=test_data, base_url=base_url, kb_id=kb_id, kb_api_key=kb_api_key
                )
                result_text = ""
                execution_results = []
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "step":
                        result_text += f"[步骤] {event_data.get('message', '')}\n"
                    elif event_type == "result":
                        execution_results.append(event_data)
                        current_api = event_data.get("api_name", "unknown")
                        success = event_data.get("success", False)
                        status = "成功" if success else "失败"
                        result_text += f"[{current_api}] {status}\n"
                    elif event_type == "report":
                        summary = event_data
                        result_text += f"\n执行报告：{json.dumps(summary, ensure_ascii=False, indent=2)}"
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                if not result_text and execution_results:
                    result_text = f"执行完成，共执行 {len(execution_results)} 个接口\n"
                    result_text += json.dumps(execution_results, ensure_ascii=False, indent=2)
                return _ok(content=result_text, execution_results=execution_results, run_list=run_list)
            except Exception as e:
                logger.exception("execute_testcase 执行失败")
                return _err(f"执行失败：{str(e)}")

        # ========== Tool 6: validate_testcase ==========
        @self.server.tool()
        async def validate_testcase(
            case_id: str,
            api_name: str,
            precondition: str,
            testpoint: str,
            expectation: str,
            execution_results: list,
            kb_id: str,
            kb_api_key: Optional[str] = None
        ) -> str:
            """校验测试用例执行结果。分析测试执行结果，判断测试是否通过。参数：case_id、api_name、precondition、testpoint、expectation、execution_results、kb_id（均必填）、kb_api_key（可选）"""
            logger.info(f"调用 validate_testcase: case_id={case_id}")
            try:
                events = await _collect(
                    self.engine.validate_testcase,
                    case_id=case_id, api_name=api_name, precondition=precondition,
                    testpoint=testpoint, expectation=expectation,
                    execution_results=execution_results, kb_id=kb_id, kb_api_key=kb_api_key
                )
                result_text = ""
                for event in events:
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    if event_type == "step":
                        result_text += f"[步骤] {event_data.get('message', '')}\n"
                    elif event_type == "chunk":
                        result_text += event_data.get("content", "")
                    elif event_type == "result":
                        result_text += f"\n校验结果：{json.dumps(event_data, ensure_ascii=False, indent=2)}"
                    elif event_type == "step_complete":
                        result_text += f"\n[完成] {event_data.get('message', '')}"
                    elif event_type == "error":
                        return _err(event_data.get('message', '未知错误'))
                return _ok(content=result_text or "未获取到校验结果")
            except Exception as e:
                logger.exception("validate_testcase 执行失败")
                return _err(f"执行失败：{str(e)}")

    async def run(self):
        """运行 MCP Server"""
        logger.info("正在启动 API Testing MCP Server...")
        await self.server.run_stdio_async()


def _parse_run_list(content: str) -> list:
    """从生成的测试用例内容中解析 run_list"""
    try:
        content = content.strip()

        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1).strip()

        test_cases = json.loads(content)
        if isinstance(test_cases, list):
            run_list = []
            for tc in test_cases:
                if isinstance(tc, dict):
                    run_list.append({
                        "case_id": tc.get("case_id", tc.get("id", "")),
                        "api_name": tc.get("api_name", tc.get("apiname", "")),
                        "precondition": tc.get("precondition", ""),
                        "testpoint": tc.get("testpoint", ""),
                        "expectation": tc.get("expectation", tc.get("expected_result", ""))
                    })
            return run_list
        return []
    except Exception as e:
        logger.error(f"解析 run_list 失败：{e}")
        return []


def main():
    """入口函数"""
    mcp_server = ApiTestMcpServer()

    try:
        asyncio.run(mcp_server.run())
    except KeyboardInterrupt:
        logger.info("MCP Server 已停止")
    except Exception as e:
        logger.exception(f"MCP Server 异常退出：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
