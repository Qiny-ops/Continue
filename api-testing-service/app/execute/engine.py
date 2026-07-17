#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行引擎

核心功能：
1. 预填充：执行前一次性调 AI 填充所有接口参数
2. 执行：按序执行接口，动态提取变量、替换占位符
3. 断言统一由 validate_testcase 处理（前端单独调用）

AI 调用次数：执行阶段固定 1 次（预填充），断言在校验阶段
"""

import json
import re
from typing import Any, Dict, Generator, List, Optional

from app.services.kb_client import KBClient
from app.services.llm_service import LLMService
from app.prompts import get_execute_api_prompt, get_validate_prompt
from app.execute.executor import ApiTestExecutor, ExecutionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TestExecutionEngine:
    """测试执行引擎（全 AI 驱动）"""

    def __init__(self, kb_client: KBClient, llm_service: Optional[LLMService] = None):
        self.kb_client = kb_client
        self.llm = llm_service

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
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行测试用例（流式）

        流程：
        1. 按序执行每个接口，动态提取变量替换占位符
        2. 预填充仅在 run_list 缺少静态参数时调用
        断言统一由 validate_testcase 处理
        """
        executor = ApiTestExecutor(base_url=base_url)

        try:
            yield self._create_event(
                "step",
                {"message": f"开始执行测试用例，共 {len(run_list)} 个接口"}
            )

            # Step 1: 检查是否需要 AI 预填充
            # 依赖分析阶段已生成 request_body、extract_vars 等完整参数，
            # 只有当 run_list 缺少静态参数时才需要预填充
            needs_prefill = self._check_needs_prefill(run_list)

            if needs_prefill:
                prefilled_run_list = None
                yield self._create_event(
                    "step",
                    {"message": "正在调用 AI 预填充接口参数..."}
                )

                async for event in self._prefill_all_params(
                    case_id=case_id,
                    api_name=api_name,
                    precondition=precondition,
                    testpoint=testpoint,
                    expectation=expectation,
                    run_list=run_list,
                    test_data=test_data,
                    base_url=base_url,
                    kb_id=kb_id,
                    kb_api_key=kb_api_key
                ):
                    if event.get("type") == "chunk":
                        yield event
                    elif event.get("type") == "prefill_result":
                        prefilled_run_list = event.get("data", {}).get("run_list")

                if prefilled_run_list:
                    prefilled_run_list = self._merge_prefilled(prefilled_run_list, run_list)
                    yield self._create_event(
                        "step",
                        {"message": f"AI 预填充完成，共 {len(prefilled_run_list)} 个接口"}
                    )
                else:
                    logger.warning("AI 预填充失败，使用原始 run_list")
                    prefilled_run_list = run_list
            else:
                prefilled_run_list = run_list
                yield self._create_event(
                    "step",
                    {"message": "参数已完整，跳过预填充"}
                )

            # Step 2: 按序执行每个接口
            runtime_vars: Dict[str, Any] = {}

            # 预设管理员账号
            from app.config import get_settings
            settings = get_settings()
            if settings.admin_username:
                runtime_vars["admin_username"] = settings.admin_username
            if settings.admin_password:
                runtime_vars["admin_password"] = settings.admin_password

            for i, api_info in enumerate(prefilled_run_list):
                run_num = api_info.get("run_num", i + 1)
                current_api_name = api_info.get("api_name", f"接口{run_num}")

                # 执行前：替换残留的 {{变量名}} 占位符
                api_info = self._resolve_placeholders(api_info, runtime_vars)

                yield self._create_event(
                    "step",
                    {"message": f"正在执行 [{run_num}] {current_api_name}..."}
                )

                result = await executor.execute_api(api_info)

                # 执行后：提取 extract_vars 定义的变量
                extract_vars = api_info.get("extract_vars")
                if extract_vars and isinstance(extract_vars, dict):
                    for var_name, var_path in extract_vars.items():
                        if var_name not in runtime_vars:
                            value = self._extract_value_from_response(result, var_path)
                            if value is not None:
                                runtime_vars[var_name] = value
                                logger.info(f"提取变量: {var_name} = {value}")

                # 执行后：自动提取响应中常见的 Cookie 值到 runtime_vars
                if result.response and isinstance(result.response, dict):
                    resp_cookies = result.response.get("cookies", {})
                    for cookie_name, cookie_value in resp_cookies.items():
                        var_name = cookie_name
                        if var_name not in runtime_vars and cookie_value is not None:
                            runtime_vars[var_name] = cookie_value
                            logger.info(f"自动提取Cookie: {var_name} = {cookie_value}")

                logger.info(f"接口{i+1} [{current_api_name}] 执行结果: status_code={result.status_code}, expected_status={api_info.get('expected_status')}, success={result.success}, url={result.api_url}, headers={api_info.get('headers')}")

                yield self._create_event(
                    "result",
                    {
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
                    }
                )

                # HTTP 连接级别错误直接停止
                if result.status_code is None:
                    yield self._create_event(
                        "step_complete",
                        {"message": f"接口 [{current_api_name}] 连接失败，停止后续执行"}
                    )
                    break

            # 执行完成
            yield self._create_event(
                "step_complete",
                {"message": "测试用例执行完成"}
            )

            # 返回执行报告摘要
            history = executor.get_history()
            success_count = sum(1 for h in history if h.get("success", False))
            total_count = len(history)

            yield self._create_event(
                "report",
                {
                    "case_id": case_id,
                    "total": total_count,
                    "success": success_count,
                    "failed": total_count - success_count,
                    "results": history
                }
            )

        except Exception as e:
            logger.exception("测试执行异常")
            yield self._create_event(
                "error",
                {"message": f"执行失败：{str(e)}"}
            )

        finally:
            # 清理测试账号
            test_usernames = self._extract_test_usernames(run_list)
            if test_usernames:
                for username in test_usernames:
                    yield self._create_event(
                        "step",
                        {"message": f"正在清理测试账号: {username}..."}
                    )
                    cleanup_success = await self._cleanup_test_user(
                        base_url=base_url,
                        username=username
                    )
                    if cleanup_success:
                        yield self._create_event(
                            "step_complete",
                            {"message": f"测试账号 {username} 已清理"}
                        )
                    else:
                        yield self._create_event(
                            "warning",
                            {"message": f"测试账号 {username} 清理失败或不存在"}
                        )

            await executor.close()

    async def _prefill_all_params(
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
    ) -> Generator[Dict[str, Any], None, None]:
        """
        预填充模式：一次性调 AI 填充所有接口参数

        Yields:
            chunk 事件（AI 思考过程）和 prefill_result 事件（填充结果）
        """
        session_id = None
        try:
            session_result = await self.kb_client.create_session(kb_id, kb_api_key)
            session_id = session_result.get("id")

            if not session_id:
                logger.error("创建会话失败")
                yield self._create_event("prefill_result", {"run_list": None})
                return

            system_prompt = get_execute_api_prompt()

            # 获取管理员账号配置
            from app.config import get_settings
            settings = get_settings()

            prompt = system_prompt.replace("{{case_id}}", str(case_id))
            prompt = prompt.replace("{{api_name}}", api_name)
            prompt = prompt.replace("{{precondition}}", precondition)
            prompt = prompt.replace("{{testpoint}}", testpoint)
            prompt = prompt.replace("{{expectation}}", expectation)
            prompt = prompt.replace("{{run_list}}", json.dumps(run_list, ensure_ascii=False))
            prompt = prompt.replace("{{test_data}}", json.dumps(test_data, ensure_ascii=False))
            prompt = prompt.replace("{{base_url}}", base_url)
            prompt = prompt.replace("{{admin_username}}", settings.admin_username or "")
            prompt = prompt.replace("{{admin_password}}", settings.admin_password or "")

            full_response = ""
            async for event in self.kb_client.chat_stream(
                query=prompt,
                session_id=session_id,
                kb_id=kb_id,
                kb_api_key=kb_api_key
            ):
                if event.get("type") == "chunk":
                    content = event.get("data", {}).get("content", "")
                    full_response += content
                    yield self._create_event("chunk", {"content": content})
                else:
                    yield event

            # 解析返回的 JSON
            prefilled = self._parse_prefill_response(full_response)
            logger.info(f"AI 预填充响应: {full_response[:500]}")
            logger.info(f"解析后的 prefilled run_list 条数: {len(prefilled) if prefilled else 0}")
            yield self._create_event("prefill_result", {"run_list": prefilled})

        except Exception as e:
            logger.error(f"AI 预填充参数失败：{e}")
            yield self._create_event("prefill_result", {"run_list": None})

        finally:
            if session_id:
                try:
                    await self.kb_client.destroy_session(session_id, kb_api_key)
                except Exception as e:
                    logger.error(f"销毁会话失败：{e}")

    def _parse_prefill_response(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """解析 AI 预填充返回的 run_list JSON"""
        try:
            content = content.strip()

            # 尝试提取 markdown 代码块中的 JSON
            match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1).strip()
            else:
                match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()

            parsed = json.loads(content)

            # 返回格式可能是 {"run_list": [...]} 或直接是 [...]
            if isinstance(parsed, dict):
                if "run_list" in parsed:
                    return parsed["run_list"]
                # 可能返回的是单个接口信息包装在 dict 里
                return [parsed]
            elif isinstance(parsed, list):
                return parsed

            return None

        except json.JSONDecodeError as e:
            logger.error(f"解析预填充 JSON 失败：{e}，内容预览: {content[:200]}")
            return None

    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 AI 返回的 JSON"""
        try:
            content = content.strip()

            match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                content = match.group(1).strip()

            parsed = json.loads(content)

            if isinstance(parsed, dict):
                return parsed
            return None

        except json.JSONDecodeError as e:
            logger.error(f"解析 AI 响应 JSON 失败：{e}")
            return None

    def _extract_test_usernames(self, run_list: List[Dict[str, Any]]) -> List[str]:
        """从 run_list 中提取需要清理的时间戳格式测试用户名"""
        usernames = []
        pattern = r'^test_\d{8}_\d{6}_[a-z0-9]{4}$'

        for api_info in run_list:
            api_name = api_info.get("api_name", "")
            if "注册" not in api_name:
                continue

            request_body = api_info.get("request_body", {})
            if isinstance(request_body, dict):
                username = request_body.get("username", "")
                if re.match(pattern, username):
                    usernames.append(username)

        return usernames

    def _check_needs_prefill(self, run_list: List[Dict[str, Any]]) -> bool:
        """
        检查 run_list 是否需要 AI 预填充。

        如果每个接口都已有 request_body 且非空，则不需要预填充。
        只有当某些接口缺少 request_body 或 request_body 为空时才需要。
        """
        if not run_list:
            return False

        for api_info in run_list:
            method = (api_info.get("method", "")).upper()
            # POST/PUT/DELETE 通常需要 request_body
            if method in ("POST", "PUT", "DELETE", "PATCH"):
                request_body = api_info.get("request_body")
                if not request_body or (isinstance(request_body, dict) and len(request_body) == 0):
                    logger.info(f"接口 [{api_info.get('api_name', '')}] 缺少 request_body，需要预填充")
                    return True

        logger.info("所有接口参数已完整，无需预填充")
        return False

    def _merge_prefilled(
        self,
        prefilled: List[Dict[str, Any]],
        original: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并预填充结果和原始 run_list，防止 AI 篡改动态字段。

        规则：
        1. 以原始 run_list 为基准保留 extract_vars（AI 可能删改）
        2. 以原始 run_list 为基准保留 api_url 中的 {{xxx}} 占位符（AI 可能硬编码替换）
        3. 从预填充结果中取静态参数填充（用户名、密码、邮箱等）
        4. 保留原始的 run_list 长度和顺序
        5. 保留原始的 headers（特别是异常场景测试中显式设置的伪造 Authorization）
        """
        # 按 run_num 建立原始映射
        original_map = {}
        for item in original:
            run_num = item.get("run_num", 0)
            original_map[run_num] = item

        # 按 run_num 建立预填充映射
        prefilled_map = {}
        for item in prefilled:
            run_num = item.get("run_num", 0)
            prefilled_map[run_num] = item

        merged = []
        for item in original:
            run_num = item.get("run_num", 0)
            prefilled_item = prefilled_map.get(run_num, {})

            # 从原始复制一份
            merged_item = dict(item)

            if prefilled_item:
                # 从预填充取静态填充：request_body
                orig_body = item.get("request_body", {})
                filled_body = prefilled_item.get("request_body", {})
                if isinstance(filled_body, dict) and isinstance(orig_body, dict):
                    for key, val in filled_body.items():
                        # 只接受非占位符的值（AI 填充的实际数据）
                        if isinstance(val, str) and not re.match(r'^\{\{.+\}\}$', val) and not re.match(r'^\{.+\}$', val):
                            orig_body[key] = val
                    merged_item["request_body"] = orig_body

                # 保留原始的 extract_vars（AI 可能删改变量名）
                merged_item["extract_vars"] = item.get("extract_vars", {})

                # 保留原始的 api_url（含 {{xxx}} 占位符，AI 可能硬编码替换）
                merged_item["api_url"] = item.get("api_url", "")

                # 保留原始的 expected_status
                merged_item["expected_status"] = item.get("expected_status")

                # 保留原始的 description
                merged_item["description"] = item.get("description", "")

                # 保留原始的 headers（异常场景测试可能包含伪造的 Authorization）
                # 只有当原始 headers 为空时才使用预填充的 headers
                orig_headers = item.get("headers", {})
                if orig_headers and any("authorization" in k.lower() for k in orig_headers):
                    # 原始已设置 Authorization（可能是伪造Token），保留原值
                    merged_item["headers"] = orig_headers
                    logger.info(f"保留原始 headers（含 Authorization）: {orig_headers}")
                else:
                    # 原始无 Authorization，合并预填充的其他 headers
                    merged_item["headers"] = prefilled_item.get("headers", orig_headers)

            merged.append(merged_item)

        return merged

    def _resolve_placeholders(self, api_info: Dict[str, Any], runtime_vars: Dict[str, Any]) -> Dict[str, Any]:
        """
        替换 api_info 中的占位符为运行时提取的值，并自动注入 token。

        支持的占位符格式（AI 可能输出任意一种）：
        - {{var_name}}  标准双花括号
        - ${{var_name}} 带$前缀的双花括号
        - {var_name}    单花括号
        """
        def replace_in_string(s: str) -> str:
            """替换字符串中所有格式的占位符"""
            if not isinstance(s, str):
                return s
            changed = True
            while changed:
                changed = False
                for var_name, value in runtime_vars.items():
                    # 按优先级匹配：${{xxx}} > {{xxx}} > {xxx}
                    for fmt in ["${{" + var_name + "}}", "{{" + var_name + "}}", "{" + var_name + "}"]:
                        if fmt in s:
                            s = s.replace(fmt, str(value))
                            logger.info(f"替换占位符: {fmt} -> {value}")
                            changed = True
            return s

        # 替换 api_url
        api_url = api_info.get("api_url", "")
        api_info["api_url"] = replace_in_string(api_url)

        # 替换 request_body
        request_body = api_info.get("request_body", {})
        if isinstance(request_body, dict):
            for key, val in list(request_body.items()):
                if isinstance(val, str):
                    new_val = replace_in_string(val)
                    if new_val != val:
                        request_body[key] = new_val

        # 替换 headers 中的占位符（如 Authorization: Bearer {token_xxx}）
        headers = api_info.get("headers", {})
        if isinstance(headers, dict):
            for key, val in list(headers.items()):
                if isinstance(val, str):
                    new_val = replace_in_string(val)
                    if new_val != val:
                        headers[key] = new_val

        # 自动注入 token 到 Authorization header（如果还没有）
        # 注意：只有当接口未显式设置 Authorization，且不是异常场景测试时才自动注入
        has_auth = any("authorization" in k.lower() for k in api_info.get("headers", {}))
        if not has_auth:
            # 检查是否是异常场景测试（预期返回 4xx/5xx 错误码）
            expected_status = api_info.get("expected_status")
            is_error_test = False
            if expected_status is not None:
                try:
                    if isinstance(expected_status, int):
                        is_error_test = expected_status >= 400
                    elif isinstance(expected_status, str):
                        # 处理 "4XX", "401", "400-499" 等格式
                        exp_str = expected_status.upper()
                        if exp_str.endswith("XX"):
                            is_error_test = exp_str[0] in "45"
                        elif "-" in exp_str:
                            parts = exp_str.split("-")
                            is_error_test = int(parts[0]) >= 400
                        else:
                            is_error_test = int(exp_str) >= 400
                except (ValueError, TypeError):
                    pass

            # 异常场景测试不自动注入 token（测试用例可能需要伪造/无效 token）
            if is_error_test:
                logger.info(f"接口 [{api_info.get('api_name', '')}] 是异常场景测试 (expected_status={expected_status})，跳过自动注入 token")
            else:
                token_value = None
                for var_name, value in runtime_vars.items():
                    name_lower = var_name.lower()
                    # 匹配 token 类变量，但排除 csrftoken 等 Cookie 类变量
                    if "token" in name_lower and not name_lower.startswith("csrf"):
                        token_value = value
                        break
                if token_value:
                    if "headers" not in api_info:
                        api_info["headers"] = {}
                    api_info["headers"]["Authorization"] = f"Bearer {token_value}"
                    logger.info(f"自动注入 Authorization header")

        # 自动注入 Cookie header（如果还没有且有 session/csrf 类变量）
        has_cookie = any("cookie" in k.lower() for k in api_info.get("headers", {}))
        if not has_cookie:
            cookie_parts = []
            for var_name, value in runtime_vars.items():
                if any(kw in var_name.lower() for kw in ("sessionid", "session", "csrf", "csrftoken")):
                    cookie_parts.append(f"{var_name}={value}")
            if cookie_parts:
                if "headers" not in api_info:
                    api_info["headers"] = {}
                api_info["headers"]["Cookie"] = "; ".join(cookie_parts)
                logger.info(f"自动注入 Cookie header: {api_info['headers']['Cookie']}")

        return api_info

    def _extract_value_from_response(self, result: Any, path: str) -> Optional[Any]:
        """
        根据 JSONPath 风格路径从执行结果中提取值

        支持格式：$.run_list[0].response.body.data.id
        result 是 ExecutionResult，result.response 的结构为 {"status_code": ..., "body": {...}, "headers": ..., "cookies": {...}}
        所以去掉 $.run_list[N].response. 前缀后，路径为 body.data.id 或 cookies.sessionid
        """
        if not path or not result:
            return None

        try:
            # 移除 $. 前缀
            if path.startswith("$."):
                path = path[2:]

            # 去掉 run_list[N] 前缀
            match = re.match(r'run_list\[\d+\]\.(.*)', path)
            if match:
                path = match.group(1)

            # 去掉 response. 前缀（result.response 已经是 response 对象）
            if path.startswith("response."):
                path = path[len("response."):]

            # 起点是 result.response，结构为 {"status_code": ..., "body": {...}, "headers": ...}
            data = {}
            if hasattr(result, 'response') and result.response:
                data = result.response
            elif hasattr(result, 'status_code'):
                # 可能直接就是 response dict
                data = result

            # 按路径导航
            parts = path.split(".")
            current = data
            for part in parts:
                if current is None:
                    return None

                # 处理数组索引
                array_match = re.match(r'(\w+)\[(\d+)\]', part)
                if array_match:
                    key = array_match.group(1)
                    idx = int(array_match.group(2))
                    if isinstance(current, dict):
                        current = current.get(key)
                    else:
                        return None
                    if isinstance(current, list) and idx < len(current):
                        current = current[idx]
                    else:
                        return None
                else:
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        return None

            return current

        except Exception as e:
            logger.error(f"提取变量失败: path={path}, error={e}")
            return None

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
    ) -> Generator[Dict[str, Any], None, None]:
        """
        校验测试用例（流式）
        """
        session_id = None

        try:
            system_prompt = get_validate_prompt()

            session_result = await self.kb_client.create_session(kb_id, kb_api_key)
            session_id = session_result.get("id")

            if not session_id:
                yield self._create_event(
                    "error",
                    {"message": "创建会话失败"}
                )
                return

            prompt = system_prompt.replace("{{case_id}}", str(case_id))
            prompt = prompt.replace("{{api_name}}", api_name)
            prompt = prompt.replace("{{precondition}}", precondition)
            prompt = prompt.replace("{{testpoint}}", testpoint)
            prompt = prompt.replace("{{expectation}}", expectation)

            # 为 execution_results 补充 expected_status（前端可能丢失）
            enhanced_results = self._enhance_execution_results(execution_results)
            prompt = prompt.replace("{{execution_results}}", json.dumps(enhanced_results, ensure_ascii=False))

            # 调试：记录传给AI的执行结果
            logger.info(f"校验输入 enhanced_results: {json.dumps(enhanced_results, ensure_ascii=False, indent=2)[:2000]}")

            yield self._create_event(
                "step",
                {"message": "正在分析执行结果..."}
            )

            full_response = ""
            async for event in self.kb_client.chat_stream(
                query=prompt,
                session_id=session_id,
                kb_id=kb_id,
                kb_api_key=kb_api_key
            ):
                if event.get("type") == "chunk":
                    content = event.get("data", {}).get("content", "")
                    full_response += content
                    yield self._create_event(
                        "chunk",
                        {"content": content}
                    )

            validation_result = self._parse_ai_response(full_response)

            if validation_result:
                yield self._create_event(
                    "result",
                    validation_result
                )
            else:
                yield self._create_event(
                    "error",
                    {"message": "无法解析校验结果"}
                )

            yield self._create_event(
                "step_complete",
                {"message": "测试校验完成"}
            )

        except Exception as e:
            logger.exception("测试校验异常")
            yield self._create_event(
                "error",
                {"message": f"校验失败：{str(e)}"}
            )

        finally:
            if session_id:
                try:
                    await self.kb_client.destroy_session(session_id, kb_api_key)
                except Exception as e:
                    logger.error(f"销毁会话失败：{e}")

    def _enhance_execution_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        增强 execution_results，为每个结果添加事实性判定说明，辅助 AI 校验。

        expected_status 由执行阶段传入，不再做关键词推断。
        status_judgment 只陈述事实（预期值、实际值、是否匹配），判断交给 AI。
        """
        enhanced = []
        for r in results:
            item = dict(r)

            expected = item.get("expected_status")
            actual = item.get("status_code")

            if expected is not None and actual is not None:
                try:
                    exp_str = str(expected).upper()
                    act_int = actual

                    if exp_str.endswith("XX"):
                        base = int(exp_str[0]) * 100
                        matched = base <= act_int < base + 100
                    elif "-" in exp_str:
                        parts = exp_str.split("-")
                        matched = int(parts[0]) <= act_int <= int(parts[1])
                    else:
                        exp_int = int(exp_str.rstrip("Xx"))
                        if 400 <= exp_int < 600:
                            matched = (exp_int // 100) == (act_int // 100)
                        else:
                            matched = exp_int == act_int

                    item["status_judgment"] = (
                        f"预期状态码{expected}，实际{actual}，{'匹配' if matched else '不匹配'}"
                    )
                except (ValueError, TypeError):
                    item["status_judgment"] = f"预期状态码{expected}，实际{actual}"

            enhanced.append(item)

        return enhanced

    def _create_event(self, step: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建进度事件"""
        return {"type": step, "data": data}

    async def _cleanup_test_user(
        self,
        base_url: str,
        username: Optional[str],
        auth_token: Optional[str] = None
    ) -> bool:
        """清理测试用户"""
        if not username:
            return False

        pattern = r'test_\d{8}_\d{6}_[a-z0-9]{4}$'
        if not re.match(pattern, username):
            logger.info(f"用户名 {username} 不是时间戳格式测试账号，跳过清理")
            return False

        try:
            import httpx
            url = f"{base_url}/api/users/cleanup-test-user/?username={username}"
            headers = {"Content-Type": "application/json"}

            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, headers=headers)
                result = response.json()

                if result.get("code") == 200 or result.get("success"):
                    logger.info(f"测试用户 {username} 清理成功")
                    return True
                else:
                    logger.warning(f"清理测试用户失败: {result.get('message', 'Unknown error')}")
                    return False

        except Exception as e:
            logger.error(f"清理测试用户异常: {e}")
            return False
