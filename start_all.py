#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动所有服务脚本

启动前后端服务和两个AI微服务:
- Vue3 前端 (端口 5173)
- Django 后端 (端口 8000)
- AI Generator 服务 (端口 8001)
- API Testing 服务 (端口 8002)
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# 服务配置
SERVICES = {
    "frontend": {
        "name": "Vue3 Frontend",
        "port": 5173,
        "path": PROJECT_ROOT / "vue3-frontend",
        "command": ["pnpm", "dev"],
        "check_file": "node_modules",
        "url": "http://localhost:5173",
    },
    "backend": {
        "name": "Django Backend",
        "port": 8000,
        "path": PROJECT_ROOT / "Testbackend",
        "command": ["venv\\Scripts\\python.exe", "manage.py", "runserver", "0.0.0.0:8000"],
        "check_file": "venv",
        "url": "http://localhost:8000",
    },
    "ai_generator": {
        "name": "AI Generator Service",
        "port": 8001,
        "path": PROJECT_ROOT / "ai-generator-service",
        "command": ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
        "check_file": ".env",
        "url": "http://localhost:8001/docs",
    },
    "api_testing": {
        "name": "API Testing Service",
        "port": 8002,
        "path": PROJECT_ROOT / "api-testing-service",
        "command": ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
        "check_file": ".env",
        "url": "http://localhost:8002/docs",
    },
    "web_automation": {
        "name": "Web Automation Service",
        "port": 8003,
        "path": PROJECT_ROOT / "web-automation-service",
        "command": ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"],
        "check_file": ".env",
        "url": "http://localhost:8003/docs",
    },
    "ai_check": {
        "name": "AI Code Check Service",
        "port": 8004,
        "path": PROJECT_ROOT / "aicheck-service",
        "command": ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"],
        "check_file": ".env",
        "url": "http://localhost:8004/docs",
    },
}


def print_header(title: str) -> None:
    """打印标题"""
    print("\n" + "=" * 50)
    print(f"   {title}")
    print("=" * 50 + "\n")


def check_service_ready(service_key: str) -> tuple[bool, str]:
    """检查服务是否准备就绪"""
    service = SERVICES[service_key]
    check_path = service["path"] / service["check_file"]

    if not check_path.exists():
        return False, f"找不到 {service['check_file']}，请先配置服务"

    return True, ""


def start_service(service_key: str) -> bool:
    """启动单个服务"""
    service = SERVICES[service_key]

    print(f"[{service['name']}] 正在启动...")

    # 检查服务是否准备就绪
    ready, error = check_service_ready(service_key)
    if not ready:
        print(f"  [警告] {error}")
        return False

    try:
        env = os.environ.copy()
        service_path = str(service["path"])
        cmd_list = service["command"]
        window_title = service["name"]

        if sys.platform == "win32":
            # Windows: 构建批处理命令
            cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd_list)

            # 使用 os.startfile 或 subprocess 直接调用
            # 方案: 使用 start 命令，需要用 shell=True
            batch_cmd = f'start "{window_title}" cmd.exe /k "cd /d {service_path} & {cmd_str}"'

            subprocess.Popen(batch_cmd, shell=True, env=env)
        else:
            # Linux/macOS
            cmd_str = " ".join(cmd_list)
            if os.environ.get("TERM"):
                subprocess.Popen(
                    ["x-terminal-emulator", "-e", f"cd {service_path} && {cmd_str}"],
                    env=env,
                )
            else:
                subprocess.Popen(cmd_list, cwd=service_path, env=env)

        print(f"  [成功] 已在新窗口中启动 (端口: {service['port']})")
        return True

    except Exception as e:
        print(f"  [错误] 启动失败: {e}")
        return False


def print_summary() -> None:
    """打印服务摘要"""
    print("\n" + "=" * 50)
    print("   所有服务已启动")
    print("=" * 50 + "\n")
    print("服务地址:")
    for service in SERVICES.values():
        print(f"  - {service['name']:<20} {service['url']}")
    print("\n提示: 各服务在独立的命令行窗口中运行")
    print("      关闭对应窗口即可停止服务\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="启动所有服务")
    parser.add_argument("--skip-frontend", action="store_true", help="跳过前端服务")
    parser.add_argument("--skip-backend", action="store_true", help="跳过后端服务")
    parser.add_argument("--skip-ai-generator", action="store_true", help="跳过 AI Generator 服务")
    parser.add_argument("--skip-api-testing", action="store_true", help="跳过 API Testing 服务")
    parser.add_argument("--skip-web-automation", action="store_true", help="跳过 Web Automation 服务")
    parser.add_argument("--skip-ai-check", action="store_true", help="跳过 AI Code Check 服务")

    args = parser.parse_args()

    print_header("启动所有服务")

    # 确定要启动的服务
    services_to_start = []
    if not args.skip_frontend:
        services_to_start.append("frontend")
    if not args.skip_backend:
        services_to_start.append("backend")
    if not args.skip_ai_generator:
        services_to_start.append("ai_generator")
    if not args.skip_api_testing:
        services_to_start.append("api_testing")
    if not args.skip_web_automation:
        services_to_start.append("web_automation")
    if not args.skip_ai_check:
        services_to_start.append("ai_check")

    # 启动服务
    success_count = 0
    for i, service_key in enumerate(services_to_start, 1):
        print(f"\n[{i}/{len(services_to_start)}] {SERVICES[service_key]['name']}")
        if start_service(service_key):
            success_count += 1
        time.sleep(1)

    # 打印摘要
    print_summary()
    print(f"成功启动 {success_count}/{len(services_to_start)} 个服务")


if __name__ == "__main__":
    main()
