#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server 启动脚本

使用方式：
    python run_mcp_server.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.mcp_server import main

if __name__ == "__main__":
    main()