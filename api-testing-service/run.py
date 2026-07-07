#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本

使用方式：
    python run.py
"""

import uvicorn

from app.config import get_settings
from app.utils.logger import service_logger

if __name__ == "__main__":
    settings = get_settings()

    host = "0.0.0.0"
    port = 8002
    debug = settings.debug

    service_logger.info("=" * 60)
    service_logger.info("API Testing Service 启动")
    service_logger.info("=" * 60)
    service_logger.info(f"监听地址：http://{host}:{port}")
    service_logger.info(f"API 文档：http://{host}:{port}/docs")
    service_logger.info(f"调试模式：{debug}")
    service_logger.info("=" * 60)
    service_logger.info("可用接口:")
    service_logger.info("  GET  /api/v1/health - 健康检查")
    service_logger.info("  GET  /api/v1/status - 服务状态")
    service_logger.info("  POST /api/v1/flow - 获取接口业务流（流式）")
    service_logger.info("  POST /api/v1/testcase/generate - 生成测试用例（流式）")
    service_logger.info("  POST /api/v1/dependency - 获取接口依赖（流式）")
    service_logger.info("  POST /api/v1/testdata/fill - 填充测试数据（流式）")
    service_logger.info("  POST /api/v1/testcase/execute - 执行测试用例（流式）")
    service_logger.info("  POST /api/v1/testcase/validate - 校验测试用例（流式）")
    service_logger.info("  POST /api/v1/llm/chat - LLM 对话（同步）")
    service_logger.info("  POST /api/v1/llm/chat/stream - LLM 对话（流式）")
    service_logger.info("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
    )