#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块

默认输出到 stderr（MCP 协议兼容），可通过 LOG_STREAM 环境变量切换。
"""
import logging
import os
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


service_logger = get_logger("ai-generator-service")
