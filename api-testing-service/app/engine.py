#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一测试引擎

合并原 ApiTestEngine（业务流/生成/依赖/填充/LLM对话）
和 TestExecutionEngine（执行/校验）为一个引擎。

数据填充职责由独立的 fill_test_data 步骤承担；执行阶段为纯确定性逻辑，
不调用 LLM（写接口缺请求参数时显式报错，引导先完成数据填充）。
"""

import copy
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.services.kb_client import KBClient, KBError
from app.services.llm_service import LLMService
from app.services.db_service import DBService
from app.services.django_cleanup import cleanup_test_user, extract_test_usernames
from app.services.value_extractor import extract_value_from_response
from app.execute.executor import ApiTestExecutor
from app.utils.json_parser import parse_llm_json
from app.utils.logger import get_logger, mask
from app.utils.prompt_builder import PromptBuilder
from app.utils.sanitize import is_error_status, sanitize_filled_data, sanitize_run_list, bind_test_accounts
from app.utils.session import KBSession

logger = get_logger(__name__)


class TestEngine:
    """统一测试引擎"""

    __test__ = False  # pytest 不要将其当作测试类收集

    def __init__(
        self,
        kb_client: KBClient,
        llm_service: Optional[LLMService] = None,
        db_service: Optional[DBService] = None
    ):
        self.kb_client = kb_client
        self.llm = llm_service
        self.db = db_service

    def _event(self, step: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": step, "data": data}

    # ==================== 业务流 & 生成 ====================

    async def get_flow(
        self,
        kb_id: str,
        query: str,
        kb_api_key: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """获取接口业务流（流式）"""
        try:
            async with KBSession(self.kb_client, kb_id, kb_api_key) as session:
                yield self._event("session", {"action": "created", "session_id": session.session_id})
                async for event in session.chat_stream(query):
                    yield event
        except KBError as e:
            logger.error(f"Knowledge 服务调用失败：{e}")
            yield self._event("error", {"message": f"知识库服务调用失败：{e.message}"})
        except Exception as e:
            logger.exception("业务流获取失败")
            yield self._event("error", {"message": f"生成失败：{str(e)}"})

    async def generate_testcase(
        self,
        kb_id: str,
        query: str = "对文档中的接口设计接口测试用例",
        kb_api_key: Optional[str] = None,
        save_to_db: bool = False,
        knowledge_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """生成接口测试用例（流式）"""
        try:
            final_query = PromptBuilder.build_testcase_query(query)

            async with KBSession(self.kb_client, kb_id, kb_api_key) as session:
                yield self._event("session", {"action": "created", "session_id": session.session_id})

                content_buffer = ""
                async for event in session.chat_stream(final_query, knowledge_id):
                    if event.get("type") == "chunk":
                        content_buffer += event.get("data", {}).get("content", "")
                    yield event

                yield self._event("complete", {"message": "生成完成"})

                if save_to_db and self.db and self.db.enabled:
                    test_cases = parse_llm_json(content_buffer, expected_type=list)
                    if test_cases:
                        document_id = None
                        if knowledge_id:
                            doc = await self.db.get_document_by_knowledge_id(knowledge_id)
                            if doc:
                                document_id = doc.get("id")
                        count = await self.db.save_test_cases(test_cases, document_id, knowledge_id)
                        yield self._event("saved", {"count": count, "document_id": document_id})
                    else:
                        yield self._event("error", {"message": "未解析到有效的测试用例"})

        except KBError as e:
            logger.error(f"Knowledge 服务调用失败：{e}")
            yield self._event("error", {"message": f"知识库服务调用失败：{e.message}"})
        except Exception as e:
            logger.exception("生成测试用例失败")
            yield self._event("error", {"message": f"生成失败：{str(e)}"})

    # ==================== 依赖分析 & 数据填充 ====================

    async def get_api_dependency(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """获取接口依赖和执行顺序（流式）"""
        try:
            yield self._event("step", {"message": "正在加载相关信息..."})

            from app.config import get_settings
            settings = get_settings()
            prompt = PromptBuilder.build_dependency_prompt(
                case_id=case_id, api_name=api_name,
                precondition=precondition, testpoint=testpoint,
                expectation=expectation,
            )

            async with KBSession(self.kb_client, kb_id, kb_api_key) as session:
                full_response = ""
                async for event in session.chat_stream(prompt):
                    if event.get("type") == "chunk":
                        content = event.get("data", {}).get("content", "")
                        full_response += content
                        yield self._event("chunk", {"content": content})
                    else:
                        yield event

                dependency_info = parse_llm_json(full_response, expected_type=dict)
                if not dependency_info:
                    yield self._event("error", {"message": "无法解析依赖关系 JSON"})
                    return

                yield self._event("result", {"dependency": dependency_info})

        except Exception as e:
            logger.exception("获取接口依赖失败")
            yield self._event("error", {"message": f"获取依赖失败：{str(e)}"})

    async def fill_test_data(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        dependency: Dict[str, Any],
        test_data: Dict[str, Any],
        kb_id: str,
        kb_api_key: Optional[str] = None,
        base_url: str = "http://127.0.0.1:8000"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """填充测试数据（流式）"""
        try:
            yield self._event("step", {"message": "正在处理相关信息..."})

            prompt = PromptBuilder.build_fill_data_prompt(
                case_id=case_id, api_name=api_name,
                precondition=precondition, testpoint=testpoint,
                expectation=expectation,
                dependency=dependency, test_data=test_data,
                base_url=base_url,
            )

            async with KBSession(self.kb_client, kb_id, kb_api_key) as session:
                full_response = ""
                async for event in session.chat_stream(prompt):
                    if event.get("type") == "chunk":
                        content = event.get("data", {}).get("content", "")
                        full_response += content
                        yield self._event("chunk", {"content": content})
                    else:
                        yield event

                filled_data = parse_llm_json(full_response, expected_type=dict)
                if not filled_data:
                    yield self._event("error", {"message": "无法解析填充后的数据 JSON"})
                    return

                # 兜底清洗：将 <测试密码> 等占位符式值替换为合法值，避免接口返回 400
                filled_data = sanitize_filled_data(filled_data)

                yield self._event("result", {"filled_data": filled_data})

        except Exception as e:
            logger.exception("填充测试数据失败")
            yield self._event("error", {"message": f"填充数据失败：{str(e)}"})

    # ==================== 测试执行 ====================

    async def execute_testcase(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        run_list: List[Dict[str, Any]],
        test_data: Dict[str, Any],
        base_url: str,
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行测试用例（流式）"""
        executor = ApiTestExecutor(base_url=base_url)

        try:
            yield self._event("step", {"message": f"开始执行测试用例，共 {len(run_list)} 个接口"})

            # 数据填充职责已移至独立的 fill_test_data 步骤；执行阶段不再调用 LLM。
            # 写接口缺 request_body 时显式报错，引导调用方先完成数据填充
            empty_body_steps = [
                f"[{item.get('run_num', i + 1)}] {item.get('api_name', '')}"
                for i, item in enumerate(run_list)
                if (item.get("method", "")).upper() in ("POST", "PUT", "DELETE", "PATCH")
                and not item.get("request_body")
            ]
            if empty_body_steps:
                yield self._event("error", {
                    "message": (
                        f"以下写接口缺少请求参数：{'、'.join(empty_body_steps)}。"
                        "请先调用 fill_testdata 完成数据填充后再执行"
                    )
                })
                return

            run_list = sanitize_run_list(run_list)

            # runtime_vars 改为按步骤索引存储，避免多步骤同名变量碰撞（多用户串号）
            # 必须在 bind_test_accounts 之前初始化，否则下方读取时尚未赋值（UnboundLocalError）
            runtime_vars: Dict[str, Any] = {}

            from app.config import get_settings
            settings = get_settings()
            if settings.admin_username:
                runtime_vars["admin_username"] = settings.admin_username
                runtime_vars["__ADMIN_USERNAME__"] = settings.admin_username
            if settings.admin_password:
                runtime_vars["admin_password"] = settings.admin_password
                runtime_vars["__ADMIN_PASSWORD__"] = settings.admin_password

            # 账号隔离：为每个用例执行分配一组「执行级唯一测试账号」，绑定到注册/登录步骤，
            # 避免并发批量执行时多用例共用同一写死账号、互相污染数据导致结果失真
            bind_test_accounts(run_list, runtime_vars)

            # 向用户明示账号隔离的替换关系：依赖分析里显示的账号与本执行实际使用的账号不同，
            # 输出映射避免「思考过程账号 ≠ 执行账号」造成困惑
            for rw in runtime_vars.get("__ACCOUNT_REWRITES__", []):
                original = rw.get("original") or "（AI 填充值）"
                yield self._event("step", {
                    "message": (
                        f"账号隔离：步骤「{rw.get('api_name', '')}」 "
                        f"{original} → {rw.get('account', '')}（本次执行专用账号）"
                    )
                })

            # 按序执行每个接口
            for i, api_info in enumerate(run_list):
                run_num = api_info.get("run_num", i + 1)
                current_api_name = api_info.get("api_name", f"接口{run_num}")

                # 深拷贝防篡改：_resolve_placeholders 会修改 dict 内部字段，
                # 直接传引用会污染调用方传入的原始 run_list
                api_info = self._resolve_placeholders(
                    copy.deepcopy(api_info), runtime_vars
                )

                yield self._event("step", {"message": f"正在执行 [{run_num}] {current_api_name}..."})

                result = await executor.execute_api(api_info)

                # 提取 extract_vars：加 run_num 前缀防止跨步骤同名变量碰撞
                extract_vars = api_info.get("extract_vars")
                if extract_vars and isinstance(extract_vars, dict):
                    for var_name, var_path in extract_vars.items():
                        # 使用 run_num 下标防止多步骤提取同名变量（如 token）时相互覆盖
                        indexed_name = f"{var_name}_{run_num}"
                        value = self._extract_value_from_response(result, var_path)
                        if value is not None:
                            runtime_vars[indexed_name] = value
                            logger.info(f"提取变量: {indexed_name} (原名 {var_name}) = {mask(value)}")
                            # 同时保留原名作为"最新值"：后续步骤占位符可使用 {var_name} 获取最近一步的值
                            runtime_vars[var_name] = value

                # 自动提取 Cookie（也按步骤下标索引）
                if result.response and isinstance(result.response, dict):
                    resp_cookies = result.response.get("cookies", {})
                    for cookie_name, cookie_value in resp_cookies.items():
                        if cookie_value is not None:
                            indexed_name = f"{cookie_name}_{run_num}"
                            runtime_vars[indexed_name] = cookie_value
                            logger.info(f"自动提取Cookie: {indexed_name} = {mask(cookie_value)}")
                            # 同时保留原名作为"最新值"
                            runtime_vars[cookie_name] = cookie_value

                logger.info(f"接口{i+1} [{current_api_name}] 执行结果: status_code={result.status_code}, success={result.success}")

                yield self._event("result", {
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

                if result.status_code is None:
                    yield self._event("step_complete", {"message": f"接口 [{current_api_name}] 连接失败，停止后续执行"})
                    break

            yield self._event("step_complete", {"message": "测试用例执行完成"})

            history = executor.get_history()
            success_count = sum(1 for h in history if h.get("success", False))
            total_count = len(history)

            yield self._event("report", {
                "case_id": case_id,
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count,
                "results": history
            })

        except Exception as e:
            logger.exception("测试执行异常")
            yield self._event("error", {"message": f"执行失败：{str(e)}"})

        finally:
            # 仅做资源释放，禁止在 finally 中 yield：
            # 客户端断连时 Starlette 会抛 GeneratorExit，若此处仍有 yield 会触发
            # RuntimeError 且 executor.close() 被跳过，造成连接泄漏
            await executor.close()

        # 清理测试账号（在正常流程末尾、finally 之外 yield，避免 GeneratorExit 与 yield 冲突）
        # 优先清理本次执行实际创建的执行级唯一账号（由 bind_test_accounts 写入 runtime_vars）
        test_usernames = list(runtime_vars.get("__TEST_ACCOUNTS__", []) or [])
        if test_usernames:
            for username in test_usernames:
                yield self._event("step", {"message": f"正在清理测试账号: {username}..."})
                if await self._cleanup_test_user(base_url=base_url, username=username):
                    yield self._event("step_complete", {"message": f"测试账号 {username} 已清理"})
                else:
                    yield self._event("warning", {"message": f"测试账号 {username} 清理失败或不存在"})

    # ==================== 校验 ====================

    async def validate_testcase(
        self,
        case_id: str,
        api_name: str,
        precondition: str,
        testpoint: str,
        expectation: str,
        execution_results: List[Dict[str, Any]],
        kb_id: str,
        kb_api_key: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """校验测试用例（流式）"""
        try:
            enhanced_results = self._enhance_execution_results(execution_results)
            prompt = PromptBuilder.build_validate_prompt(
                case_id=case_id, api_name=api_name,
                precondition=precondition, testpoint=testpoint,
                expectation=expectation,
                execution_results=enhanced_results,
            )

            logger.info(f"校验输入: {json.dumps(enhanced_results, ensure_ascii=False, indent=2)[:2000]}")

            async with KBSession(self.kb_client, kb_id, kb_api_key) as session:
                yield self._event("step", {"message": "正在分析执行结果..."})

                full_response = ""
                async for event in session.chat_stream(prompt, temperature=0):
                    if event.get("type") == "chunk":
                        content = event.get("data", {}).get("content", "")
                        full_response += content
                        yield self._event("chunk", {"content": content})

                validation_result = parse_llm_json(full_response, expected_type=dict)

                if validation_result:
                    # 校验失败时，追加失败分析
                    # passed 可能为布尔或字符串（"false"/"False"），归一化后再判定，
                    # 避免严格 is False 比较导致失败分析被静默跳过
                    passed_val = validation_result.get("passed")
                    passed_is_false = (
                        passed_val is False
                        or (isinstance(passed_val, str) and passed_val.strip().lower() == "false")
                    )
                    if passed_is_false:
                        yield self._event("step", {"message": "正在分析失败原因..."})
                        analysis_prompt = PromptBuilder.build_failure_analysis_prompt(
                            case_id=case_id, api_name=api_name,
                            precondition=precondition, testpoint=testpoint,
                            expectation=expectation,
                            execution_results=enhanced_results,
                            validation_result=full_response,
                        )
                        analysis_response = ""
                        async for event in session.chat_stream(analysis_prompt, temperature=0):
                            if event.get("type") == "chunk":
                                content = event.get("data", {}).get("content", "")
                                analysis_response += content
                                yield self._event("chunk", {"content": content})

                        analysis_result = parse_llm_json(analysis_response, expected_type=dict)
                        if analysis_result:
                            validation_result["failure_analysis"] = analysis_result
                        else:
                            # 解析失败时降级保留原文，避免失败分析静默缺失
                            logger.warning(f"失败分析输出无法解析为 JSON: {analysis_response[:200]}")
                            validation_result["failure_analysis"] = {
                                "root_cause": analysis_response[:500] or "（失败分析输出为空）",
                            }

                    yield self._event("result", validation_result)
                else:
                    yield self._event("error", {"message": "无法解析校验结果"})

                yield self._event("step_complete", {"message": "测试校验完成"})

        except Exception as e:
            logger.exception("测试校验异常")
            yield self._event("error", {"message": f"校验失败：{str(e)}"})

    # ==================== LLM 对话 ====================

    async def llm_chat(
        self,
        query: str,
        system_message: Optional[str] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """直接调用 LLM 模型"""
        if not self.llm:
            yield self._event("error", {"message": "LLM 服务未初始化"})
            return

        try:
            messages: List[Dict[str, str]] = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": query})

            if stream:
                async for chunk in self.llm.chat_stream(messages):
                    yield self._event("chunk", {"content": chunk})
            else:
                result = await self.llm.chat(messages)
                yield self._event("result", {
                    "content": result["content"],
                    "usage": result.get("usage", {}),
                    "finish_reason": result.get("finish_reason")
                })

        except Exception as e:
            logger.exception("LLM 调用失败")
            yield self._event("error", {"message": f"LLM 调用失败：{str(e)}"})

    # ==================== 内部工具方法 ====================

    def _resolve_placeholders(self, api_info: Dict[str, Any], runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        """替换 api_info 中的占位符为运行时提取的值，并自动注入 token"""
        def replace_in_string(s: str) -> str:
            if not isinstance(s, str):
                return s
            changed = True
            for _ in range(10):  # 上限保护：值若含自身占位符会导致无限循环打满事件循环
                if not changed:
                    break
                changed = False
                for var_name, value in runtime_vars.items():
                    for fmt in ["${{" + var_name + "}}", "{{" + var_name + "}}", "{" + var_name + "}", var_name]:
                        if fmt in s:
                            s = s.replace(fmt, str(value))
                            logger.info(f"替换占位符: {fmt} -> {mask(value)}")
                            changed = True
            return s

        api_info["api_url"] = replace_in_string(api_info.get("api_url", ""))

        request_body = api_info.get("request_body", {})
        if isinstance(request_body, dict):
            for key, val in list(request_body.items()):
                if isinstance(val, str):
                    new_val = replace_in_string(val)
                    if new_val != val:
                        request_body[key] = new_val

        headers = api_info.get("headers", {})
        if isinstance(headers, dict):
            for key, val in list(headers.items()):
                if isinstance(val, str):
                    new_val = replace_in_string(val)
                    if new_val != val:
                        headers[key] = new_val

        # 自动注入 token（仅非异常场景）
        # 登录/注册步骤跳过：它们本身就是凭据的生产者，注入外部 token（如前一步
        # 管理员登录提取的 token）会让"普通用户登录"带着管理员凭据发出，请求语义错乱
        is_credential_producer = any(
            kw in str(api_info.get("api_name", "")) for kw in ("登录", "注册", "login", "register", "signup", "log_in", "sign_in")
        )
        # 步骤自身会提取 token 的（extract_vars 含 token 类变量）也跳过注入
        extracts_token = any(
            "token" in str(var_name).lower()
            for var_name in (api_info.get("extract_vars") or {})
        )
        has_auth = any("authorization" in k.lower() for k in api_info.get("headers", {}))
        if (
            not has_auth
            and not is_error_status(api_info.get("expected_status"))
            and not is_credential_producer
            and not extracts_token
        ):
            token_value = None
            for var_name, value in runtime_vars.items():
                name_lower = var_name.lower()
                if "token" in name_lower and not name_lower.startswith("csrf"):
                    token_value = value
                    break
            if token_value:
                if "headers" not in api_info:
                    api_info["headers"] = {}
                api_info["headers"]["Authorization"] = f"Bearer {token_value}"
                logger.info("自动注入 Authorization header")

        # 自动注入 Cookie
        has_cookie = any("cookie" in k.lower() for k in api_info.get("headers", {}))
        if not has_cookie:
            cookie_parts = []
            for var_name, value in runtime_vars.items():
                if any(kw in var_name.lower() for kw in ("sessionid", "session", "csrf", "csrftoken")):
                    cookie_parts.append(f"{var_name}={mask(value)}")
            if cookie_parts:
                if "headers" not in api_info:
                    api_info["headers"] = {}
                api_info["headers"]["Cookie"] = "; ".join(cookie_parts)
                logger.info(f"自动注入 Cookie header: {api_info['headers']['Cookie']}")

        return api_info

    def _extract_value_from_response(self, result: Any, path: str) -> Optional[Any]:
        """根据 JSONPath 风格路径从执行结果中提取值（委托到独立的 value_extractor 服务）"""
        return extract_value_from_response(result, path)

    def _enhance_execution_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """增强 execution_results，为每个结果添加事实性判定说明"""
        enhanced = []
        for r in results:
            item = dict(r)
            expected = item.get("expected_status")
            actual = item.get("status_code")

            if expected is not None and actual is not None:
                try:
                    from app.execute.executor import ApiTestExecutor
                    matched = ApiTestExecutor._match_status(expected, actual)
                    item["status_judgment"] = (
                        f"预期状态码{expected}，实际{actual}，{'匹配' if matched else '不匹配'}"
                    )
                except (ValueError, TypeError):
                    item["status_judgment"] = f"预期状态码{expected}，实际{actual}"

            enhanced.append(item)

        return enhanced

    async def _cleanup_test_user(
        self,
        base_url: str,
        username: Optional[str],
        auth_token: Optional[str] = None
    ) -> bool:
        """清理测试用户（委托到独立的 django_cleanup 服务）"""
        from app.config import get_settings
        settings = get_settings()
        return await cleanup_test_user(
            base_url, username,
            internal_api_key=settings.internal_api_key,
            auth_token=auth_token,
        )

    def _extract_test_usernames(self, run_list: List[Dict[str, Any]]) -> List[str]:
        """从 run_list 中提取需要清理的测试用户名（委托到 django_cleanup 服务）"""
        return extract_test_usernames(run_list)
