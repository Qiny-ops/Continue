#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块

默认输出到 stderr（MCP 协议兼容），可通过 LOG_STREAM 环境变量切换。
mask() 脱敏函数为 api-testing 独有功能。
"""
import logging
import os
import re
import sys
from typing import Optional

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _get_log_stream():
    """确定日志输出流：默认 stderr（MCP 安全），可设 LOG_STREAM=stdout 切回 stdout"""
    if os.environ.get("LOG_STREAM", "").lower() == "stdout":
        return sys.stdout
    return sys.stderr


def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，通常使用 __name__
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    console_handler = logging.StreamHandler(_get_log_stream())
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    logger.addHandler(console_handler)

    return logger


def set_log_level(level: int):
    """设置全局日志级别"""
    logging.root.setLevel(level)
    for handler in logging.root.handlers:
        handler.setLevel(level)


# 敏感信息脱敏（api-testing 独有的安全功能）
_SENSITIVE_KEYWORDS = [
    "password", "passwd", "pwd",
    "token", "api_key", "authorization",
    "cookie", "set-cookie", "sessionid",
    "jsessionid", "x-api-key", "x-auth-token",
]


def mask(text) -> str:
    """脱敏文本中的敏感信息

    兼容非字符串输入（如从响应提取的 int 型 user_id、dict 型 headers、
    None 等），先统一转为字符串再做脱敏，避免 re.sub 抛出 TypeError。
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        # int / dict / list / bool 等统一转字符串，避免 re.sub 崩溃
        text = str(text)
    if not text:
        return text
    for keyword in _SENSITIVE_KEYWORDS:
        pattern = re.compile(
            rf'({re.escape(keyword)})["\s:]*["\']?([^"\'&\s,;}}]+)',
            re.IGNORECASE,
        )
        text = pattern.sub(r'\1 ***', text)
    return text


# 模块级日志记录器（兼容 app.utils.__init__ 和其他直接 import 调用方）
service_logger = get_logger("api-testing-service")
