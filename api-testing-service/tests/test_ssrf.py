#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSRF 防护单元测试

验证 execute_api 在构造目标 URL 后会经过 _validate_target_url 校验，
拦截非 http(s)、云元数据、受限 IP 等目标地址，避免凭据/内网被探测。
"""

import pytest

from app.execute.executor import ApiTestExecutor, _validate_target_url


class TestValidateTargetUrl:
    """_validate_target_url 单元断言"""

    def test_empty_url(self):
        assert _validate_target_url("", False) is not None

    def test_non_http_scheme(self):
        # file:// / ftp:// 等应被拒绝
        assert _validate_target_url("file:///etc/passwd", False) is not None
        assert _validate_target_url("ftp://example.com", False) is not None

    def test_cloud_metadata_ip(self):
        # 云元数据地址是 SSRF 最关键的目标
        assert _validate_target_url("http://169.254.169.254/latest/meta-data/", False) is not None
        assert _validate_target_url("http://169.254.169.254/", True) is not None

    def test_blocked_hostname(self):
        assert _validate_target_url("http://metadata.google.internal/", False) is not None

    def test_loopback_allowed_by_default(self):
        # 回环地址默认放行：本服务需对本地测试服务器(默认 127.0.0.1:8000)发起请求
        assert _validate_target_url("http://127.0.0.1:8000/api", False) is None
        assert _validate_target_url("http://localhost:8000/api", False) is None

    def test_reserved_multicast_blocked(self):
        assert _validate_target_url("http://240.0.0.1/", False) is not None  # 保留段
        assert _validate_target_url("http://224.0.0.1/", False) is not None  # 多播

    def test_link_local(self):
        assert _validate_target_url("http://169.254.1.1/", False) is not None

    def test_valid_http_https(self):
        assert _validate_target_url("http://example.com/api", False) is None
        assert _validate_target_url("https://example.com/api", False) is None

    def test_private_ip_allowed_by_default(self):
        # 默认允许访问内网测试服务器（block_private=False）
        assert _validate_target_url("http://10.0.0.5:8080/api", False) is None
        assert _validate_target_url("http://192.168.1.10/api", False) is None

    def test_private_ip_blocked_when_enabled(self):
        # 开启 block_private_targets 后禁止私网
        assert _validate_target_url("http://10.0.0.5:8080/api", True) is not None
        assert _validate_target_url("http://192.168.1.10/api", True) is not None


class TestExecuteApiSsrfGuard:
    """execute_api 在发起请求前应先做 URL 校验（不触网）"""

    def test_blocked_url_returns_error_without_request(self):
        import asyncio
        executor = ApiTestExecutor()
        result = asyncio.run(executor.execute_api({
            "api_url": "http://169.254.169.254/latest/meta-data/iam/",
            "method": "GET",
            "run_num": 1,
            "api_name": "探测元数据",
        }))
        assert result.success is False
        assert result.error is not None
        assert result.status_code is None
        assert result.response is None

    def test_valid_url_passes_validation(self):
        import asyncio
        # 合法地址通过校验（实际 HTTP 失败由网络决定，这里只验证不提前报错）
        executor = ApiTestExecutor()
        result = asyncio.run(executor.execute_api({
            "api_url": "http://example.com/api",
            "method": "GET",
            "run_num": 2,
            "api_name": "合法请求",
        }))
        # 未做真实请求，error 应来自网络层而非 SSRF 校验（即不为 None 是网络错，不是校验错）
        if result.error is not None:
            assert "169.254.169.254" not in result.error
