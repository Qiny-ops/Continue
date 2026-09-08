# -*- coding: utf-8 -*-
"""
用例来源归一化：inline / file(Excel) / platform(回调 Django)
"""
import os
from typing import List

import httpx

from app.config import settings
from app.schemas.task import TestCaseItem
from app.services.excel_handler import ExcelHandler


# 中英表头映射 → TestCaseItem 字段
_KEY_ALIASES = {
    "case_no": "case_no",
    "用例编号": "case_no", "编号": "case_no", "id": "case_no",
    "testpoint": "testpoint",
    "测试点": "testpoint", "功能点": "testpoint", "title": "testpoint",
    "steps": "steps",
    "操作步骤": "steps", "步骤": "steps", "test_steps": "steps",
    "expectation": "expectation",
    "预期结果": "expectation", "预期": "expectation", "expected_result": "expectation",
}


def _normalize(case: dict, idx: int) -> TestCaseItem:
    out: dict = {}
    for k, v in (case or {}).items():
        if k is None:
            continue
        key = _KEY_ALIASES.get(str(k).strip(), None)
        if key:
            out[key] = "" if v is None else str(v).strip()
    case_no = out.get("case_no") or f"TC{idx:03d}"
    return TestCaseItem(
        case_no=case_no,
        testpoint=out.get("testpoint", ""),
        steps=out.get("steps", ""),
        expectation=out.get("expectation", ""),
    )


async def load_inline(test_cases: List[TestCaseItem] | List[dict]) -> List[TestCaseItem]:
    if not test_cases:
        return []
    if test_cases and isinstance(test_cases[0], TestCaseItem):
        return list(test_cases)
    return [_normalize(c, i + 1) for i, c in enumerate(test_cases)]


async def load_file(test_case_file: str) -> List[TestCaseItem]:
    path = os.path.join(settings.test_cases_dir, test_case_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"测试用例文件不存在: {path}")
    handler = ExcelHandler(path)
    try:
        rows = handler.get_test_cases()
    finally:
        handler.close()
    return [_normalize(r, i + 1) for i, r in enumerate(rows)]


async def load_platform(project_code: str) -> List[TestCaseItem]:
    """回调 Django 内部接口拉取用例（带 INTERNAL_API_KEY）"""
    if not project_code:
        raise ValueError("case_source=platform 时 project_code 必填")
    if not settings.internal_api_key:
        raise PermissionError("微服务未配置 INTERNAL_API_KEY，无法拉取平台用例")

    url = f"{settings.django_base_url.rstrip('/')}/api/internal/codecheck/cases/"
    headers = {"X-Internal-API-Key": settings.internal_api_key}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params={"project_code": project_code}, headers=headers)
        if resp.status_code == 401:
            raise PermissionError("平台鉴权失败：检查 INTERNAL_API_KEY")
        resp.raise_for_status()
        data = resp.json()

    items = data.get("data") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [_normalize(item, i + 1) for i, item in enumerate(items)]
