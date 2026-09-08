# -*- coding: utf-8 -*-
"""
并发执行器（async 重写）

- asyncio.Semaphore 限制并发（settings.concurrency，默认 3）
- 用例间 time.sleep 1s 间隔（课程要求 1s 限流）
- tenacity 指数退避重试：解析失败/异常时重试 max_retries 次
- 每条结果通过 on_result 回调实时写库
"""
import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

from tenacity import (
    AsyncRetrying, retry_if_result, stop_after_attempt, wait_exponential,
    RetryError,
)

from app.config import settings
from app.schemas.task import CheckResultItem, TestCaseItem
from app.services.verifier import verifier

logger = logging.getLogger("Executor")


def _should_retry(result: Dict[str, Any]) -> bool:
    status = result.get("功能是否完成", "")
    return status in ("解析失败", "解析错误", "异常")


def _build_feature_desc(tc: TestCaseItem) -> str:
    parts: list[str] = []
    if tc.testpoint:
        parts.append(f"测试点：{tc.testpoint}")
    if tc.steps:
        parts.append(f"操作步骤：{tc.steps}")
    if tc.expectation:
        parts.append(f"预期结果：{tc.expectation}")
    return "\n".join(parts)


def _to_result_item(tc: TestCaseItem, ai: Dict[str, Any]) -> CheckResultItem:
    completed = ai.get("功能是否完成", "未知")
    reason = ai.get("校验理由", "无校验理由")
    if completed == "是":
        return CheckResultItem(
            case_no=tc.case_no, testpoint=tc.testpoint,
            result="通过", reason=reason, success=True,
        )
    if completed == "否":
        return CheckResultItem(
            case_no=tc.case_no, testpoint=tc.testpoint,
            result="失败", reason=reason, success=False,
        )
    return CheckResultItem(
        case_no=tc.case_no, testpoint=tc.testpoint,
        result=completed or "未知", reason=reason, success=False,
    )


class TestExecutor:
    def __init__(self, on_result: Optional[Callable[[CheckResultItem], Awaitable[None]]] = None):
        self.concurrency = settings.concurrency
        self.max_retries = settings.max_retries
        self.interval = settings.request_interval
        self._last_call_ts: float = 0.0
        self._gate = asyncio.Lock()
        self.on_result = on_result

    async def _rate_limited(self) -> None:
        async with self._gate:
            now = time.monotonic()
            wait = self.interval - (now - self._last_call_ts)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_ts = time.monotonic()

    async def _run_one(self, tc: TestCaseItem, source_path: str, diff_context: str) -> CheckResultItem:
        feature_desc = _build_feature_desc(tc)
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_result(_should_retry),
                reraise=False,
            ):
                with attempt:
                    await self._rate_limited()
                    ai = await verifier.verify_feature(
                        feature_desc, source_path, diff_context
                    )
                    if _should_retry(ai):
                        logger.warning(
                            f"[{tc.case_no}] 重试中（{ai.get('功能是否完成')}）"
                        )
                    return ai
        except RetryError:
            return {"功能是否完成": "解析失败", "校验理由": "已达最大重试次数"}

        except Exception as e:
            return {"功能是否完成": "异常", "校验理由": str(e)}

        return {"功能是否完成": "未知", "校验理由": "未知"}

    async def execute_all(
        self,
        test_cases: List[TestCaseItem],
        source_path: str,
        diff_context: str = "",
    ) -> List[CheckResultItem]:
        if not test_cases:
            return []
        sem = asyncio.Semaphore(self.concurrency)
        results: List[CheckResultItem] = []
        results_lock = asyncio.Lock()

        async def _worker(tc: TestCaseItem):
            async with sem:
                ai = await self._run_one(tc, source_path, diff_context)
                item = _to_result_item(tc, ai)
                if self.on_result:
                    try:
                        await self.on_result(item)
                    except Exception as e:  # 不阻塞主流程
                        logger.error(f"on_result 回调失败: {e}")
                async with results_lock:
                    results.append(item)

        await asyncio.gather(*[_worker(tc) for tc in test_cases])
        # 按原顺序
        order = {tc.case_no: i for i, tc in enumerate(test_cases)}
        results.sort(key=lambda r: order.get(r.case_no, 0))
        return results
