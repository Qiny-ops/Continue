# -*- coding: utf-8 -*-
"""
功能验证/风险评估（移植自 checker/verifier.py）

保留 claude_agent_sdk：模型可主动 Read/Glob/Grep 仓库文件。
为兼容 FastAPI 异步事件循环，anyio.run 在 thread 中执行。
"""
import asyncio
import json
import os
import re
from typing import Any, Dict

try:
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        ResultMessage,
    )
    from claude_agent_sdk.types import TextBlock
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "请安装 claude_agent_sdk: pip install claude-agent-sdk"
    ) from e

from app.config import settings

# 与 Claude Code 鉴权相关的环境变量，会被外部注入污染，需显式重建
_AUTH_ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
)

# aicheck-service 自有覆盖配置（优先级最高）
_SELF_OVERRIDE = {
    "ANTHROPIC_AUTH_TOKEN": "AICHECK_CLAUDE_API_KEY",
    "ANTHROPIC_BASE_URL": "AICHECK_CLAUDE_BASE_URL",
    "ANTHROPIC_MODEL": "AICHECK_CLAUDE_MODEL",
}


def _load_claude_settings_env() -> Dict[str, str]:
    """读取 ~/.claude/settings.json 的 env 段（Claude Code 的真实鉴权来源）"""
    path = os.path.expanduser("~/.claude/settings.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    env = data.get("env") or {}
    return {k: str(v) for k, v in env.items() if k in _AUTH_ENV_KEYS}


def _build_claude_env() -> Dict[str, str]:
    """
    为 Claude Code 子进程构造干净的鉴权环境。

    背景（BUG-001 复发）：服务进程若从 IDE 或其他终端启动，会继承到第三方中转的
    ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL（如讯飞、DeepSeek），其优先级高于
    ~/.claude/settings.json，导致 CLI 报 401 `API key format is incorrect`。

    优先级：aicheck 自有 AICHECK_CLAUDE_* > ~/.claude/settings.json > 进程原有值。
    且 ANTHROPIC_AUTH_TOKEN 与 ANTHROPIC_API_KEY 必须同值，否则旧的中转 key 会残留生效。
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    for key in _AUTH_ENV_KEYS:
        env.pop(key, None)

    merged: Dict[str, str] = {}
    for key in _AUTH_ENV_KEYS:  # 进程原有值兜底
        val = os.environ.get(key)
        if val:
            merged[key] = val
    merged.update(_load_claude_settings_env())  # settings.json 覆盖
    for target, source in _SELF_OVERRIDE.items():  # 自有配置最高优先级
        val = os.environ.get(source)
        if val:
            merged[target] = val

    token = merged.get("ANTHROPIC_AUTH_TOKEN") or merged.get("ANTHROPIC_API_KEY")
    if token:
        merged["ANTHROPIC_AUTH_TOKEN"] = token
        merged["ANTHROPIC_API_KEY"] = token

    env.update(merged)
    return env


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
        "判定要求（务必遵守）：\n"
        "1. 功能描述中若含「预期结果」，必须**逐条**核对，不得合并或跳过；\n"
        "2. 只要有任何一条预期结果未在代码中实现，即判「否」，并在理由中写明是哪一条；\n"
        "3. 尤其注意：跳转目标、跳转页面、提示文案、字段取值等**具体值**必须与预期完全一致，"
        "仅仅『登录成功并跳转了』不足以判定为「是」，若实际跳转页面/目标与预期不符一律判「否」；\n"
        "4. 不要因为整体流程已实现就忽略细节差异。\n\n"
        "请严格按照以下 JSON 格式输出分析结果，不要包含任何额外文字，不要使用 markdown 代码块；\n"
        "必须使用英文双引号包裹键名与字符串值，禁止使用单引号，禁止出现尾随逗号：\n"
        '{"功能是否完成": "是" 或 "否", "校验理由": "详细说明代码中是否实现了该功能，给出具体证据（如函数名、类名、关键逻辑）", '
        '"失败类型": "从下列枚举中任选其一：功能未实现 / 实现与预期不符 / 部分实现 / 无法定位实现 / 用例与代码库不匹配 / 其他", '
        '"失败原因": "一句话说明为什么判定失败，必须点明预期的哪个具体值与代码实际实现的哪个具体值不一致，不超过 80 字", '
        '"证据位置": "支撑该结论的代码位置，格式 文件路径:行号，多个用逗号分隔，如 src/views/Login.vue:119"}\n'
        "其中「失败类型」「失败原因」「证据位置」仅在判定为「否」时填写；判定为「是」时前两项填「无」、第三项填主要实现位置。\n"
        "「失败原因」必须写成可直接引用的完整句子（例如：预期跳转到个人中心页面，实际代码在 Login.vue:119 跳转到 /projects 项目列表页），"
        "不要写成「详见校验理由」这类指向性的空话。\n"
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
        "请严格按照以下 JSON 格式输出分析结果，不要包含任何额外文字，不要使用 markdown 代码块；\n"
        "必须使用英文双引号包裹键名与字符串值，禁止使用单引号，禁止出现尾随逗号：\n"
        '{"风险等级": "高" 或 "中" 或 "低", "风险分数": 0-100的整数, "风险文件": ["文件1", "文件2"], "评估理由": "详细的风险评估说明"}\n'
    )


def _strip_trailing_commas(text: str) -> str:
    """去掉对象/数组末尾的尾随逗号：`{"a":1,}` → `{"a":1}`"""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _single_to_double_quotes(text: str) -> str:
    """把 Python dict 风格的外层单引号转成合法 JSON 双引号

    只改「字符串定界」的单引号；若内容里出现双引号则转义，避免破坏 JSON。
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '"':  # 已是双引号字符串，原样搬运（内部 \" 已转义）
            out.append(ch)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\":
                    i += 2
                    if i - 1 < n:
                        out.append(text[i - 1])
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
        elif ch == "'":  # 单引号字符串 → 转成双引号
            out.append('"')
            i += 1
            while i < n:
                if text[i] == "\\":
                    out.append(text[i])
                    i += 1
                    if i < n:
                        out.append(text[i])
                        i += 1
                    continue
                if text[i] == "'":
                    break
                out.append('\\"' if text[i] == '"' else text[i])
                i += 1
            out.append('"')
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _parse_json(response: str) -> Dict[str, Any]:
    """从模型响应中解析 JSON；对常见的非标准输出做兜底修正

    模型偶发输出 Python dict 风格（单引号）或带尾随逗号，直接 json.loads 会失败，
    导致整条用例被判「异常」。这里按 原文 → 去尾随逗号 → 单引号转双引号 逐级兜底，
    全部失败时把原始响应片段带上，便于定位。
    """
    json_mod = __import__("json")

    candidates: list[str] = []
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if m:
        candidates.append(m.group(1))
    start = response.find("{")
    end = response.rfind("}") + 1
    if start != -1 and end > start:
        candidates.append(response[start:end])

    if not candidates:
        return {"error": "解析失败", "reason": f"未找到 JSON，响应: {response[:300]}"}

    last_err = ""
    for cand in candidates:
        for text in (cand, _strip_trailing_commas(cand), _single_to_double_quotes(_strip_trailing_commas(cand))):
            try:
                return json_mod.loads(text)
            except Exception as e:  # noqa: BLE001 - 逐级兜底
                last_err = str(e)

    return {
        "error": "解析错误",
        "reason": f"JSON 解析失败: {last_err}；原始响应: {response[:300]}",
    }


# 允许的失败类型枚举（前端报告直接展示，需保持稳定）
FAILURE_TYPES = (
    "功能未实现",
    "实现与预期不符",
    "部分实现",
    "无法定位实现",
    "用例与代码库不匹配",
    "其他",
)


def _normalize_failure_type(raw: Any) -> str:
    """把模型输出的失败类型收敛到枚举内；无法识别时按关键词归类"""
    text = str(raw or "").strip()
    if not text or text in ("无", "null", "None"):
        return ""
    for t in FAILURE_TYPES:
        if text == t:
            return t
    for t in FAILURE_TYPES[:-1]:  # 未精确命中时按包含关系归类
        if t in text:
            return t
    return "其他"


def _normalize_evidence(raw: Any) -> str:
    """证据位置可能是字符串或数组，统一成逗号分隔的字符串"""
    if isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw if str(x).strip()]
    else:
        items = [s.strip() for s in str(raw or "").replace("；", ",").split(",") if s.strip()]
    return "，".join(items)


def _map_feature(parsed: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in parsed:
        return {
            "功能是否完成": parsed["error"],
            "校验理由": parsed.get("reason", ""),
            "失败类型": "校验执行异常",
            "失败原因": parsed.get("reason", "") or "校验过程异常，未获得有效结论",
            "证据位置": "",
        }
    return {
        "功能是否完成": parsed.get("功能是否完成", "解析失败"),
        "校验理由": parsed.get("校验理由", "无校验理由"),
        "失败类型": _normalize_failure_type(parsed.get("失败类型")),
        "失败原因": str(parsed.get("失败原因", "") or "").strip(),
        "证据位置": _normalize_evidence(parsed.get("证据位置")),
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


def _run_query_blocking(prompt: str, source_path: str) -> list[str]:
    """在线程中独立 event loop 跑 anyio.run，避免与 FastAPI 主循环冲突

    返回「候选文本列表」，按可信度降序：
      1) ResultMessage.result —— 本次查询的最终结论
      2) 各 AssistantMessage 的 TextBlock —— 逆序（越靠后越接近结论）

    修复 BUG-010：此前把所有文本块拼成一个字符串，模型在探索代码过程中输出的
    中间文本（"Let me start by exploring..."）会盖掉/污染最终 JSON，导致解析失败。
    """
    def _collect() -> list[str]:
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="acceptEdits",
            cwd=source_path,
            env=_build_claude_env(),
        )
        texts: list[str] = []
        finals: list[str] = []

        async def _run():
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            texts.append(block.text)
                elif isinstance(message, ResultMessage):
                    if message.result:
                        finals.append(message.result)

        import anyio
        anyio.run(_run)
        return finals + texts[::-1]  # 最终结论优先，其余逆序
    return _collect()


def _parse_first_valid(candidates: list[str]) -> Dict[str, Any]:
    """逐个候选解析，取第一个成功结果；全失败时保留最有价值的错误信息"""
    best_err = ""
    for cand in candidates:
        parsed = _parse_json(cand)
        if "error" not in parsed:
            return parsed
        reason = parsed.get("reason", "")
        # 优先保留「找到 JSON 但解析失败」的错误，它比「未找到 JSON」更有价值
        if reason.startswith("JSON 解析失败") or not best_err:
            best_err = reason

    joined = "\n".join(candidates)  # 最后兜底：整体拼接再试一次
    parsed = _parse_json(joined)
    if "error" not in parsed:
        return parsed

    return {"error": "解析失败", "reason": best_err or "模型未返回任何可解析内容"}


async def _invoke(prompt: str, source_path: str) -> list[str]:
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
            return _map_feature(_parse_first_valid(response))
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
            return _map_risk(_parse_first_valid(response))
        except Exception as e:
            return {
                "风险等级": "未知", "风险分数": 0, "风险文件": [],
                "评估理由": f"异常: {e}",
            }


verifier = FeatureVerifier()
