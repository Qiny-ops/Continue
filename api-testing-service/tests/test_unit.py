#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心逻辑单元测试
"""

import json
import asyncio
import pytest

from app.engine import TestEngine
from app.utils.json_parser import (
    extract_json_block,
    extract_json_object,
    extract_json_array,
    parse_llm_json,
)
from app.utils.prompt_builder import PromptBuilder
from app.utils.sse import format_sse_event
from app.utils.sanitize import bind_test_accounts, is_error_status
from app.execute.executor import ApiTestExecutor


# ==================== JSON 解析测试 ====================

class TestExtractJsonBlock:
    def test_json_code_block(self):
        content = '```json\n{"key": "value"}\n```'
        assert extract_json_block(content) == '{"key": "value"}'

    def test_plain_code_block(self):
        content = '```\n{"key": "value"}\n```'
        assert extract_json_block(content) == '{"key": "value"}'

    def test_no_code_block(self):
        content = '{"key": "value"}'
        assert extract_json_block(content) == '{"key": "value"}'

    def test_text_with_json_block(self):
        content = 'Here is the result:\n```json\n[1, 2, 3]\n```\nDone.'
        assert extract_json_block(content) == '[1, 2, 3]'


class TestExtractJsonObject:
    def test_simple_object(self):
        content = 'prefix {"a": 1} suffix'
        assert extract_json_object(content) == '{"a": 1}'

    def test_no_object(self):
        content = 'no json here'
        assert extract_json_object(content) == 'no json here'


class TestExtractJsonArray:
    def test_simple_array(self):
        content = 'prefix [1, 2, 3] suffix'
        assert extract_json_array(content) == '[1, 2, 3]'

    def test_no_array(self):
        content = 'no json here'
        assert extract_json_array(content) == 'no json here'


class TestParseLlmJson:
    def test_dict_from_code_block(self):
        content = '```json\n{"name": "test"}\n```'
        result = parse_llm_json(content, expected_type=dict)
        assert result == {"name": "test"}

    def test_list_from_code_block(self):
        content = '```json\n[1, 2, 3]\n```'
        result = parse_llm_json(content, expected_type=list)
        assert result == [1, 2, 3]

    def test_dict_wrapped_as_list(self):
        content = '```json\n{"name": "test"}\n```'
        result = parse_llm_json(content, expected_type=list)
        assert result == [{"name": "test"}]

    def test_invalid_json_returns_none(self):
        content = 'this is not json at all'
        result = parse_llm_json(content, expected_type=dict)
        assert result is None

    def test_dict_embedded_in_text(self):
        content = 'Here is the result:\n{"key": "value"}\nEnd.'
        result = parse_llm_json(content, expected_type=dict)
        assert result == {"key": "value"}

    def test_list_with_run_list_key(self):
        content = '```json\n{"run_list": [{"id": 1}]}\n```'
        result = parse_llm_json(content, expected_type=dict)
        assert result == {"run_list": [{"id": 1}]}


# ==================== PromptBuilder 测试 ====================

class TestPromptBuilder:
    def test_build_simple(self):
        template = "Hello {{name}}, welcome to {{place}}."
        result = PromptBuilder.build(template, {"name": "World", "place": "Python"})
        assert result == "Hello World, welcome to Python."

    def test_build_auto_serialize_dict(self):
        template = "Data: {{data}}"
        result = PromptBuilder.build(template, {"data": {"key": "val"}})
        assert result == 'Data: {"key": "val"}'

    def test_build_auto_serialize_list(self):
        template = "Items: {{items}}"
        result = PromptBuilder.build(template, {"items": [1, 2, 3]})
        assert result == 'Items: [1, 2, 3]'

    def test_build_missing_variable(self):
        template = "Hello {{name}}"
        result = PromptBuilder.build(template, {})
        assert result == "Hello {{name}}"


# ==================== SSE 工具测试 ====================

class TestSseFormat:
    def test_format_sse_event(self):
        event = {"type": "step", "data": {"message": "hello"}}
        result = format_sse_event(event)
        assert result.startswith("data: ")
        assert json.loads(result[6:].strip()) == event


# ==================== Executor 状态码匹配测试 ====================

class TestStatusMatch:
    def test_exact_match_success(self):
        assert ApiTestExecutor._match_status(200, 200) is True

    def test_exact_match_failure(self):
        assert ApiTestExecutor._match_status(200, 401) is False

    def test_error_category_match_4xx(self):
        assert ApiTestExecutor._match_status(401, 403) is True

    def test_error_category_mismatch(self):
        assert ApiTestExecutor._match_status(401, 500) is False

    def test_wildcard_4xx(self):
        assert ApiTestExecutor._match_status("4XX", 403) is True

    def test_wildcard_4xx_fail(self):
        assert ApiTestExecutor._match_status("4XX", 200) is False

    def test_range_match(self):
        assert ApiTestExecutor._match_status("400-499", 403) is True

    def test_range_no_match(self):
        assert ApiTestExecutor._match_status("400-499", 200) is False

    def test_string_int_error_category(self):
        assert ApiTestExecutor._match_status("401", 403) is True

    def test_string_int_exact(self):
        assert ApiTestExecutor._match_status("200", 200) is True


# ==================== 错误状态判定测试 ====================

class TestIsErrorStatus:
    def test_none(self):
        assert is_error_status(None) is False

    def test_int_error(self):
        assert is_error_status(401) is True

    def test_int_success(self):
        assert is_error_status(200) is False

    def test_wildcard_4xx(self):
        assert is_error_status("4XX") is True

    def test_wildcard_5xx(self):
        assert is_error_status("5XX") is True

    def test_wildcard_2xx(self):
        assert is_error_status("2XX") is False

    def test_range_error(self):
        assert is_error_status("400-499") is True

    def test_range_success(self):
        assert is_error_status("200-299") is False

    def test_string_int_error(self):
        assert is_error_status("401") is True

    def test_invalid(self):
        assert is_error_status("abc") is False


# ==================== 账号隔离绑定测试 ====================

class TestBindTestAccounts:
    def _login_step(self, username, password, expected_status=None, name="用户登录接口"):
        step = {
            "api_name": name,
            "api_url": "/api/users/login/",
            "method": "POST",
            "request_body": {"username": username, "password": password},
        }
        if expected_status is not None:
            step["expected_status"] = expected_status
        return step

    def test_negative_login_not_rewritten(self):
        """SQL 注入等负面测试的登录步骤不应被改写为唯一测试账号"""
        step = self._login_step("' OR 1=1 --", "Test@123456", expected_status="4XX",
                                name="用户登录接口（SQL注入测试）")
        runtime_vars = {}
        accounts = bind_test_accounts([step], runtime_vars)

        assert accounts == []
        assert step["request_body"]["username"] == "' OR 1=1 --"
        assert step["request_body"]["password"] == "Test@123456"
        assert runtime_vars.get("__TEST_ACCOUNTS__") == []

    def test_positive_login_bound_to_unique_account(self):
        """正向登录步骤仍应绑定执行级唯一账号"""
        step = self._login_step("testuser", "Passw0rd!", expected_status=200)
        runtime_vars = {}
        accounts = bind_test_accounts([step], runtime_vars)

        assert len(accounts) == 1
        assert step["request_body"]["username"] == "{{__TEST_USERNAME_0__}}"
        assert runtime_vars["__TEST_USERNAME_0__"] == accounts[0]

    def test_negative_register_not_rewritten(self):
        """预期失败的注册步骤（如重复注册）不应被改写"""
        step = {
            "api_name": "用户注册接口（重复用户名）",
            "api_url": "/api/users/register/",
            "method": "POST",
            "request_body": {"username": "existing_user", "password": "Passw0rd!"},
            "expected_status": "4XX",
        }
        runtime_vars = {}
        accounts = bind_test_accounts([step], runtime_vars)

        assert accounts == []
        assert step["request_body"]["username"] == "existing_user"

    def test_no_expected_status_still_bound(self):
        """缺省 expected_status 的登录步骤保持原有绑定行为"""
        step = self._login_step("testuser", "Passw0rd!")
        runtime_vars = {}
        accounts = bind_test_accounts([step], runtime_vars)

        assert len(accounts) == 1

    def test_rewrite_log_records_original_and_new_account(self):
        """改写记录应包含原账号与隔离账号的映射，供执行日志展示"""
        steps = [
            {
                "api_name": "用户注册接口",
                "api_url": "/api/users/register/",
                "method": "POST",
                "request_body": {"username": "testuser", "password": "Passw0rd!",
                                 "email": "testuser@example.com"},
            },
            self._login_step("testuser", "Passw0rd!", name="用户登录接口"),
        ]
        runtime_vars = {}
        accounts = bind_test_accounts(steps, runtime_vars)

        rewrites = runtime_vars["__ACCOUNT_REWRITES__"]
        assert len(rewrites) == 2
        assert all(rw["original"] == "testuser" for rw in rewrites)
        # 注册步骤生成账号，登录步骤配对到同一账号
        assert rewrites[0]["account"] == accounts[0]
        assert rewrites[1]["account"] == accounts[0]

    def test_negative_step_not_in_rewrite_log(self):
        """被跳过的负面测试步骤不应出现在改写记录中"""
        step = self._login_step("' OR 1=1 --", "Test@123456", expected_status="4XX",
                                name="用户登录接口（SQL注入测试）")
        runtime_vars = {}
        bind_test_accounts([step], runtime_vars)

        assert runtime_vars["__ACCOUNT_REWRITES__"] == []


# ==================== 执行阶段空请求体拒绝测试 ====================

class TestExecuteEmptyBodyRejection:
    def _collect_events(self, run_list):
        engine = TestEngine(kb_client=None)
        events = []

        async def run():
            async for event in engine.execute_testcase(
                case_id="1", api_name="测试", precondition="", testpoint="",
                expectation="", run_list=run_list, test_data={},
                base_url="http://127.0.0.1:8000", kb_id="kb",
            ):
                events.append(event)

        asyncio.run(run())
        return events

    def test_write_step_with_empty_body_rejected(self):
        """写接口缺 request_body 时应报错并引导先调 fill_testdata，而非静默空跑"""
        run_list = [
            {
                "run_num": 1,
                "api_name": "用户登录接口",
                "api_url": "/api/users/login/",
                "method": "POST",
                "request_body": {},
                "expected_status": 200,
            },
        ]
        events = self._collect_events(run_list)

        errors = [e for e in events if e["type"] == "error"]
        assert len(errors) == 1
        assert "fill_testdata" in errors[0]["data"]["message"]
        assert "用户登录接口" in errors[0]["data"]["message"]
        # 不应有任何接口执行结果
        assert not [e for e in events if e["type"] == "result"]

    def test_write_step_with_missing_body_rejected(self):
        """request_body 字段缺失同样拒绝"""
        run_list = [
            {
                "run_num": 1,
                "api_name": "创建项目接口",
                "api_url": "/api/projects/",
                "method": "POST",
                "expected_status": 201,
            },
        ]
        events = self._collect_events(run_list)
        assert [e for e in events if e["type"] == "error"]

    def test_get_step_with_empty_body_not_rejected(self):
        """GET 请求 params 为空不触发拒绝（校验只针对写接口的 request_body）"""
        run_list = [
            {
                "run_num": 1,
                "api_name": "查询用户接口",
                "api_url": "/api/users/me/",
                "method": "GET",
                "expected_status": 200,
            },
        ]
        events = self._collect_events(run_list)
        errors = [e for e in events if e["type"] == "error"]
        # GET 步骤不因空参数报错（可能有其他网络错误，但没有 fill_testdata 引导）
        assert not any("fill_testdata" in e["data"].get("message", "") for e in errors)


# ==================== Token 自动注入测试 ====================

class TestTokenAutoInjection:
    def _resolve(self, api_info, runtime_vars):
        engine = TestEngine(kb_client=None)
        return engine._resolve_placeholders(api_info, runtime_vars)

    def test_login_step_not_injected_with_existing_token(self):
        """登录步骤不应被注入前一步（如管理员登录）提取的 token"""
        api_info = {
            "api_name": "用户登录接口",
            "api_url": "/api/users/login/",
            "method": "POST",
            "request_body": {"username": "{{__TEST_USERNAME_0__}}", "password": "{{__TEST_PASSWORD_0__}}"},
            "expected_status": 200,
        }
        runtime_vars = {"token": "admin_token_value", "token_1": "admin_token_value"}

        result = self._resolve(api_info, runtime_vars)

        headers = result.get("headers", {})
        assert not any("authorization" in k.lower() for k in headers)

    def test_register_step_not_injected(self):
        """注册步骤同样不应被注入 token"""
        api_info = {
            "api_name": "用户注册接口",
            "api_url": "/api/users/register/",
            "method": "POST",
            "request_body": {"username": "new_user"},
            "expected_status": 201,
        }
        runtime_vars = {"token": "admin_token_value"}

        result = self._resolve(api_info, runtime_vars)
        headers = result.get("headers", {})
        assert not any("authorization" in k.lower() for k in headers)

    def test_normal_step_still_injected(self):
        """普通业务步骤（需认证的查询）仍自动注入 token"""
        api_info = {
            "api_name": "查询项目列表接口",
            "api_url": "/api/projects/",
            "method": "GET",
            "expected_status": 200,
        }
        runtime_vars = {"token": "user_token_value"}

        result = self._resolve(api_info, runtime_vars)

        assert result["headers"]["Authorization"] == "Bearer user_token_value"

    def test_step_extracting_token_not_injected(self):
        """自身 extract_vars 含 token 的步骤（token 生产者）跳过注入"""
        api_info = {
            "api_name": "获取访问令牌接口",
            "api_url": "/api/auth/token/",
            "method": "POST",
            "request_body": {"grant_type": "password"},
            "expected_status": 200,
            "extract_vars": {"access_token": "$.run_list[0].response.body.data.token"},
        }
        runtime_vars = {"token": "admin_token_value"}

        result = self._resolve(api_info, runtime_vars)
        headers = result.get("headers", {})
        assert not any("authorization" in k.lower() for k in headers)
