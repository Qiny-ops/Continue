# -*- coding: utf-8 -*-
"""
风险评估（移植自 checker/risk_analyzer.py）
"""
from typing import Any, Dict

from app.services.verifier import verifier


class RiskAnalyzer:
    async def assess(self, diff_info: Dict[str, Any], source_path: str) -> Dict[str, Any]:
        if not diff_info.get("full_diff"):
            return {
                "level": "低", "score": 0,
                "high_risk_files": [], "reason": "无代码变更内容",
            }
        ai_result = await verifier.assess_risk(
            diff_info["full_diff"], source_path
        )
        level = ai_result.get("风险等级", "低")
        if level not in ("高", "中", "低"):
            level = "未知"
        try:
            score = int(ai_result.get("风险分数", 0) or 0)
        except (TypeError, ValueError):
            score = 0
        score = max(0, min(100, score))
        files = ai_result.get("风险文件", [])
        if not isinstance(files, list):
            files = [str(files)]
        return {
            "level": level,
            "score": score,
            "high_risk_files": files,
            "reason": ai_result.get("评估理由", ""),
        }
