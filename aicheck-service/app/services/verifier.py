# -*- coding: utf-8 -*-
"""
功能验证/风险评估（移植自 checker/verifier.py）

保留 claude_agent_sdk：模型可主动 Read/Glob/Grep 仓库文件。
为兼容 FastAPI 异步事件循环，anyio.run 在 thread 中执行。
"""
import asyncio
import re
from typing import Any, Dict

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage
    from claude_agent_sdk.types import TextBlock
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "请安装 claude_agent_sdk: pip install claude-agent-sdk"
    ) from e

from app.config import settings


def _build_feature_prompt(source_path: str, feature_desc: str, diff_context: str = "") -> str:
    diff_section = ""
    if diff_context:
        diff_section = (
            f"\n本次代码变更内容（diff）：\n{diff_context[:3000]}\n\n"
            "请重点关注本次变更中涉及的功能实现，判断变更是否实现了所需功能。\n"
        )

    return (
        f"请分析以下源码路径中的代码：\n路径：{source_path}\n\n"
        f"需要验证的功能描述：\n{feature_desc}\n"
        f"{diff_section}"
        "请严格按照以下 JSON 格式输出分析结果，不要包含任何额外文字，不要使用 markdown 代码块：\n"
        '{"功能是否完成": "是" 或 "否", "校验理由": "详细说明代码中是否实现了该功能，给出具体证据（如函数名、类名、关键逻辑）"}\n'
    )


def _build_risk_prompt(diff_content: str) -> str:
    return (
        "请分析以下代码变更内容（git diff），评估此次变更的风险等级。\n\n"
        f"变更内容：\n{diff_content[:5000]}\n\n"
        "请从以下几个方面评估风险：\n"
        "1. 变更范围：修改了哪些模块，影响范围有多大\n"
        "2. 变更类型：新增功能、修改逻辑、删除代码、重构等\n"
        "3. 潜在影响：是否涉及核心逻辑、数据库、API 接口、安全相关\n"
        "4. 代码质量：是否存在明显的问题或隐患\n\n"
        "请严格按照以下 JSON 格式输出分析结果，不要包含任何额外文字，不要使用 markdown 代码块：\n"
        '{"风险等级": "高" 或 "中" 或 "低", "风险分数": 0-100的整数, "风险文件": ["文件1", "文件2"], "评估理由": "详细的风险评估说明"}\n'
    )


def _parse_json(response: str) -> Dict[str, Any]:
    try:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if m:
            return __import__("json").loads(m.group(1))
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return __import__("json").loads(response[start:end])
        return {"error": "解析失败", "reason": f"未找到 JSON，响应: {response[:200]}"}
    except Exception as e:  # json.JSONDecodeError 等
        return {"error": "解析错误", "reason": f"JSON 解析失败: {e}"}


def _map_feature(parsed: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in parsed:
        return {"功能是否完成": parsed["error"], "校验理由": parsed.get("reason", "")}
    return {
        "功能是否完成": parsed.get("功能是否完成", "解析失败"),
        "校验理由": parsed.get("校验理由", "无校验理由"),
    }


def _map_risk(parsed: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in parsed:
        return {
            "风险等级": "未知", "风险分数": 0, "风险文件": [],
            "评估理由": parsed.get("reason", "解析失败"),
        }
    return {
        "风险等级": parsed.get("风险等级", "未知"),
        "风险分数": parsed.get("风险分数", 0),
        "风险文件": parsed.get("风险文件", []),
        "评估理由": parsed.get("评估理由", "无评估理由"),
    }


def _run_query_blocking(prompt: str, source_path: str) -> str:
    """在线程中独立 event loop 跑 anyio.run，避免与 FastAPI 主循环冲突"""
    def _collect() -> str:
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="acceptEdits",
            cwd=source_path,
        )
        chunks: list[str] = []

        async def _run():
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            chunks.append(block.text)
        import anyio
        anyio.run(_run)
        return "".join(chunks)
    return _collect()


async def _invoke(prompt: str, source_path: str) -> str:
    return await asyncio.to_thread(_run_query_blocking, prompt, source_path)


def _is_path_allowed(path: str) -> bool:
    if not settings.allowed_root_paths:
        return True  # 未配置时放行
    import os
    real = os.path.realpath(path)
    return any(real.startswith(os.path.realpath(r)) for r in settings.allowed_root_paths)


class FeatureVerifier:
    """功能验证器（也用于风险评估）"""

    async def verify_feature(
        self, feature_desc: str, source_path: str, diff_context: str = ""
    ) -> Dict[str, Any]:
        if not _is_path_allowed(source_path):
            return {"功能是否完成": "否", "校验理由": f"路径不在允许范围内: {source_path}"}
        prompt = _build_feature_prompt(source_path, feature_desc, diff_context)
        try:
            response = await asyncio.wait_for(
                _invoke(prompt, source_path), timeout=settings.timeout
            )
            return _map_feature(_parse_json(response))
        except Exception as e:
            return {"功能是否完成": "异常", "校验理由": str(e)}

    async def assess_risk(
        self, diff_content: str, source_path: str
    ) -> Dict[str, Any]:
        if not _is_path_allowed(source_path):
            return {
                "风险等级": "未知", "风险分数": 0, "风险文件": [],
                "评估理由": "路径不在允许范围内",
            }
        prompt = _build_risk_prompt(diff_content)
        try:
            response = await asyncio.wait_for(
                _invoke(prompt, source_path), timeout=settings.timeout
            )
            return _map_risk(_parse_json(response))
        except Exception as e:
            return {
                "风险等级": "未知", "风险分数": 0, "风险文件": [],
                "评估理由": f"异常: {e}",
            }


verifier = FeatureVerifier()
