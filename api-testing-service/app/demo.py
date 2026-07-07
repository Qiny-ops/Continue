#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo 示例

使用 Claude Agent SDK 检查源码中功能是否已实现。
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage
from claude_agent_sdk.types import TextBlock, ThinkingBlock, ToolUseBlock


async def check_feature_with_sdk(code_path: str, test_case: str) -> None:
    """
    使用 Claude Agent SDK 检查指定源码中某个功能是否已实现。

    Args:
        code_path: 要检查的源代码根目录的路径
        test_case: 测试用例的描述

    Returns:
        None，结果会直接打印到控制台
    """
    prompt = (
        f"请检查以下路径的代码：'{code_path}'。"
        f"测试用例：'{test_case}'。"
        f"请分析该功能是否已实现，并给出详细的证据和结论。"
    )

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="acceptEdits",
        cwd=code_path
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="")
                elif isinstance(block, ThinkingBlock):
                    print("\n[思考过程]", end="")
                elif isinstance(block, ToolUseBlock):
                    print(f"\n[调用工具: {block.name}]", end="")
                else:
                    print(f"\n[未知块类型: {type(block).__name__}]", end="")
    print()


async def main() -> None:
    """主函数"""
    await check_feature_with_sdk(
        code_path="/path/to/project/",
        test_case="学习警告短信推送的功能实现了吗？"
    )


if __name__ == "__main__":
    anyio.run(main)
