#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停止所有服务脚本

停止前后端服务和两个AI微服务
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()


def print_header(title: str) -> None:
    """打印标题"""
    print("\n" + "=" * 50)
    print(f"   {title}")
    print("=" * 50 + "\n")


def stop_process_by_name(process_name: str) -> int:
    """通过进程名停止进程"""
    count = 0

    if sys.platform == "win32":
        # Windows 使用 taskkill
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                count = 1
        except Exception as e:
            print(f"  [错误] 停止 {process_name} 失败: {e}")
    else:
        # Linux/Mac 使用 pkill
        try:
            result = subprocess.run(
                ["pkill", "-f", process_name],
                capture_output=True,
            )
            count = result.returncode
        except Exception as e:
            print(f"  [错误] 停止 {process_name} 失败: {e}")

    return count


def stop_process_by_port(port: int) -> bool:
    """通过端口停止进程"""
    if sys.platform == "win32":
        try:
            # 查找占用端口的进程
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
            )

            pids = set()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids.add(pid)

            # 停止进程
            for pid in pids:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)

            return len(pids) > 0

        except Exception as e:
            print(f"  [错误] 查找端口 {port} 进程失败: {e}")
            return False
    else:
        try:
            result = subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            print(f"  [提示] fuser 命令不存在，跳过端口 {port}")
            return False


def main() -> None:
    print_header("停止所有服务")

    # 服务端口映射
    port_mapping = {
        5173: "Vue3 Frontend",
        8000: "Django Backend",
        8001: "AI Generator Service",
        8002: "API Testing Service",
        8003: "Web Automation Service",
        8004: "AI Code Check Service",
    }

    # 通过端口停止服务
    for port, name in port_mapping.items():
        print(f"正在停止 {name} (端口 {port})...")
        if stop_process_by_port(port):
            print(f"  [已停止] {name}")
        else:
            print(f"  [提示] {name} 未运行或已停止")

    # 额外清理 Node 和 Python 进程
    print("\n清理残留进程...")

    # 停止 node 进程 (Vite)
    print("  清理 node 进程...")
    stop_process_by_name("node.exe")

    # 停止 python 进程 (Django/Uvicorn)
    print("  清理相关 python 进程...")
    # 注意：不直接杀所有 python，只杀 uvicorn
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/FI", "WINDOWTITLE eq *uvicorn*"],
            capture_output=True,
        )

    print("\n所有服务已停止")


if __name__ == "__main__":
    main()
