"""
AI TestCase Generator Client
调用 AI 微服务生成测试用例

此模块属于基础设施层（Client Layer），负责与AI微服务的HTTP通信。
"""
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from threading import Lock
import numpy as np

import logging

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常"""

    def __init__(self, message: str, code: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ModelNotReadyError(AIServiceError):
    """模型未就绪"""

    def __init__(self):
        super().__init__(
            message="AI模型服务未就绪，请稍后重试",
            code="MODEL_NOT_READY",
        )


@dataclass
class AIGenerationResult:
    """AI生成结果"""

    success: bool
    result: Any  # 解析后的 JSON 结果（测试用例列表）
    raw_content: Optional[str]  # 原始返回内容
    error: Optional[str]
    thinking: Optional[str] = None  # AI 思考过程


@dataclass
class TestCaseGenerateResult:
    """测试用例生成结果（新接口）"""

    success: bool
    cases: List[Dict[str, Any]]  # 用例列表
    error: Optional[str] = None


class OpenAIEmbeddingClient:
    """
    OpenAI Embedding 客户端

    用于计算文本向量，支持语义相似度计算
    """

    def __init__(self):
        self.api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.base_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.timeout = getattr(settings, "OPENAI_EMBEDDING_TIMEOUT", 30)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文本的Embedding向量，自动分批处理（每批最多64条）

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not self.api_key:
            raise AIServiceError("OPENAI_API_KEY 未配置", "CONFIG_ERROR")

        # 过滤空文本，用占位符替代
        processed_texts = []
        for text in texts:
            if not text or not text.strip():
                processed_texts.append("空文本占位符")
            else:
                processed_texts.append(text.strip())

        # 分批请求，每批最多64条
        batch_size = 64
        all_embeddings = []

        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": batch
                    }
                )

                if response.status_code != 200:
                    error_detail = ""
                    try:
                        error_detail = response.json()
                    except (ValueError, Exception):
                        error_detail = response.text
                    raise AIServiceError(f"Embedding API 错误: {response.status_code}, 详情: {error_detail}", "EMBEDDING_ERROR")

                data = response.json()
                embeddings = sorted(data["data"], key=lambda x: x["index"])
                all_embeddings.extend([e["embedding"] for e in embeddings])

        return all_embeddings

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2)))

    async def find_duplicates(
        self,
        cases: List[Dict[str, Any]],
        threshold: float = 0.85
    ) -> List[int]:
        """
        找出重复用例的索引

        Args:
            cases: 用例列表，每个用例需包含 title 和 steps
            threshold: 相似度阈值

        Returns:
            需要去重的用例索引列表（保留第一个，删除后续重复的）
        """
        if len(cases) <= 1:
            return []

        # 构建去重文本
        texts = []
        for case in cases:
            text = f"{case.get('title', '')} {case.get('steps', '')[:200]}"
            texts.append(text)

        # 获取向量
        embeddings = await self.get_embeddings(texts)

        # 找出重复项
        duplicates = []
        for i in range(len(embeddings)):
            if i in duplicates:
                continue
            for j in range(i + 1, len(embeddings)):
                if j in duplicates:
                    continue
                similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                if similarity >= threshold:
                    logger.info(f"发现重复用例: [{i}] 和 [{j}] 相似度={similarity:.3f}")
                    duplicates.append(j)

        return duplicates


class AITestCaseClient:
    """
    AI测试用例生成微服务客户端（异步版本）

    微服务接口：
    - POST /api/v1/infer - 单次推理
    - POST /api/v1/infer/stream - 流式推理
    - POST /api/v1/batch - 批量推理
    - GET /api/v1/health - 健康检查
    """

    def __init__(self):
        self.base_url = getattr(settings, "AI_SERVICE_URL", "http://localhost:8001")
        # 超时配置：连接超时10秒，读取超时120秒（生成用例可能较慢）
        self.timeout = getattr(settings, "AI_SERVICE_TIMEOUT", 120)
        self.connect_timeout = getattr(settings, "AI_CONNECT_TIMEOUT", 10)
        self.cache_enabled = getattr(settings, "AI_CACHE_ENABLED", True)
        self.cache_ttl = getattr(settings, "AI_CACHE_TTL", 3600)

    def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=self.connect_timeout,
                read=self.timeout,
                write=self.timeout,
                pool=30
            ),
        )

    async def generate_cases(
        self,
        input_text: str,
    ) -> AIGenerationResult:
        """
        调用AI微服务生成测试用例

        Args:
            input_text: 输入文本

        Returns:
            AIGenerationResult: 生成结果
        """
        payload = {
            "messages": [
                {"role": "user", "content": input_text}
            ],
        }

        # 检查缓存
        if self.cache_enabled:
            cache_key = self._get_cache_key(input_text)
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"AI generation cache hit: {cache_key[:20]}...")
                return AIGenerationResult(**cached)

        # 调用AI服务
        try:
            async with self._get_client() as client:
                response = await client.post("/api/v1/infer", json=payload)
                response.raise_for_status()
                data = response.json()

                result = AIGenerationResult(
                    success=data.get("success", False),
                    result=data.get("result"),
                    raw_content=data.get("raw_content"),
                    error=data.get("error"),
                    thinking=data.get("thinking"),
                )

                # 缓存成功的结果
                if self.cache_enabled and result.success:
                    cache.set(cache_key, result.__dict__, self.cache_ttl)

                logger.info(
                    f"AI generation completed: success={result.success}, "
                    f"has_result={result.result is not None}"
                )

                return result

        except httpx.TimeoutException:
            logger.error("AI service timeout")
            raise AIServiceError("AI服务响应超时，请稍后重试", "TIMEOUT")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise ModelNotReadyError()
            logger.error(f"AI service error: {e.response.status_code}")
            raise AIServiceError(
                f"AI服务异常: {e.response.status_code}",
                "SERVICE_ERROR",
                {"status_code": e.response.status_code},
            )

        except httpx.RequestError as e:
            logger.error(f"AI service connection error: {e}")
            raise AIServiceError(
                "无法连接AI服务，请检查服务状态",
                "CONNECTION_ERROR",
                {"error": str(e)},
            )

    async def generate_cases_stream(
        self,
        input_text: str,
    ) -> AsyncGenerator[str, None]:
        """
        流式调用AI微服务生成测试用例

        Args:
            input_text: 输入文本

        Yields:
            str: 流式返回的内容片段
        """
        payload = {
            "messages": [
                {"role": "user", "content": input_text}
            ],
        }

        try:
            async with self._get_client() as client:
                async with client.stream(
                    "POST",
                    "/api/v1/infer/stream",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # 去掉 "data: " 前缀
                            if data == "[DONE]":
                                break
                            yield data

        except httpx.TimeoutException:
            logger.error("AI service stream timeout")
            yield "[错误] AI服务响应超时"

        except httpx.HTTPStatusError as e:
            logger.error(f"AI service stream error: {e.response.status_code}")
            yield f"[错误] AI服务异常: {e.response.status_code}"

        except httpx.RequestError as e:
            logger.error(f"AI service stream connection error: {e}")
            yield "[错误] 无法连接AI服务"

    async def generate_cases_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[AIGenerationResult]:
        """
        批量生成测试用例

        Args:
            items: 批量推理项列表，每项包含 input_text

        Returns:
            List[AIGenerationResult]: 生成结果列表
        """
        batch_items = []
        for item in items:
            input_text = item.get("input_text", "")
            batch_items.append({
                "messages": [{"role": "user", "content": input_text}],
            })

        payload = {"items": batch_items}

        try:
            async with self._get_client() as client:
                response = await client.post("/api/v1/batch", json=payload)
                response.raise_for_status()
                data = response.json()

                results = []
                for r in data.get("results", []):
                    results.append(AIGenerationResult(
                        success=r.get("success", False),
                        result=r.get("result"),
                        raw_content=None,
                        error=r.get("error"),
                        thinking=r.get("thinking"),
                    ))

                logger.info(
                    f"AI batch generation completed: "
                    f"total={data.get('total')}, completed={data.get('completed')}"
                )

                return results

        except httpx.TimeoutException:
            logger.error("AI service timeout")
            raise AIServiceError("AI服务响应超时，请稍后重试", "TIMEOUT")

        except httpx.RequestError as e:
            logger.error(f"AI service connection error: {e}")
            raise AIServiceError(
                "无法连接AI服务，请检查服务状态",
                "CONNECTION_ERROR",
                {"error": str(e)},
            )

    async def health_check(self) -> bool:
        """检查AI服务健康状态"""
        try:
            async with self._get_client() as client:
                response = await client.get("/api/v1/health")
                return response.status_code == 200
        except Exception:
            logger.warning("AI service health check failed", exc_info=True)
            return False

    async def get_service_info(self) -> Optional[dict]:
        """获取服务信息"""
        try:
            async with self._get_client() as client:
                response = await client.get("/")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Get service info error: {e}")
            return None

    async def generate_test_cases_for_func_point(
        self,
        module: str,
        func_point: str,
        related_detail: str = "",
        test_directions: List[str] = None,
        temperature: float = None,
    ) -> TestCaseGenerateResult:
        """
        为单个功能点生成测试用例（一次请求处理多个测试方向）

        Args:
            module: 模块名称
            func_point: 功能点
            related_detail: 关联需求详情
            test_directions: 测试方向列表
            temperature: 生成温度（可选，用于重试时降低随机性）

        Returns:
            TestCaseGenerateResult: 生成结果
        """
        if test_directions is None:
            test_directions = ["功能点测试", "业务逻辑测试", "其他测试"]

        payload = {
            "module": module,
            "func_point": func_point,
            "related_detail": related_detail,
            "test_directions": test_directions,
        }

        # 如果指定了temperature，添加到payload
        if temperature is not None:
            payload["temperature"] = temperature

        try:
            async with self._get_client() as client:
                response = await client.post("/api/v1/testcase/generate", json=payload)
                response.raise_for_status()
                data = response.json()

                return TestCaseGenerateResult(
                    success=data.get("success", False),
                    cases=data.get("cases", []),
                    error=data.get("error"),
                )

        except httpx.TimeoutException:
            logger.error("AI service timeout")
            raise AIServiceError("AI服务响应超时，请稍后重试", "TIMEOUT")

        except httpx.RequestError as e:
            logger.error(f"AI service connection error: {e}")
            raise AIServiceError(
                "无法连接AI服务，请检查服务状态",
                "CONNECTION_ERROR",
                {"error": str(e)},
            )

    async def generate_test_cases_for_func_point_stream(
        self,
        module: str,
        func_point: str,
        related_detail: str = "",
        test_directions: List[str] = None,
        temperature: float = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式为单个功能点生成测试用例

        调用 AI 微服务的 /api/v1/infer/stream 接口，
        逐 chunk 解析 <thinking> 标签，yield 分类后的片段。
        对每个测试方向分别流式调用，thinking 内容实时推送，
        最终从 content 部分解析 JSON 用例列表。

        Yields:
            dict: {"type": "thinking"|"content"|"done"|"error", ...}
        """
        if test_directions is None:
            test_directions = ["功能点测试", "业务逻辑测试", "其他测试"]

        base_text = f"模块：{module}，功能点：{func_point}"
        if related_detail and related_detail != "无相关需求":
            base_text += f"\n关联需求：{related_detail}"
        else:
            base_text += "\n关联需求：无"

        all_cases = []

        for direction in test_directions:
            # 使用与微服务 /api/v1/testcase/generate 相同的方向提示词格式
            direction_prompts = {
                "功能点测试": "测试方向：功能点测试用例场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
                "业务逻辑测试": "测试方向：业务逻辑测试用例场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
                "其他测试": "测试方向：其他测试场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
            }
            direction_prompt = direction_prompts.get(direction, f"测试方向：{direction}。请生成测试用例，严格按照 json 格式返回。")
            input_text = f"{base_text}\n{direction_prompt}"
            messages = [{"role": "user", "content": input_text}]

            dir_content = ""
            in_thinking = False
            thinking_buffer = ""  # 缓存可能跨 chunk 的标签检测

            try:
                payload = {"messages": messages}
                if temperature is not None:
                    payload["temperature"] = temperature

                async with self._get_client() as client:
                    async with client.stream(
                        "POST",
                        "/api/v1/infer/stream",
                        json=payload,
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break

                                # 将缓存和当前 chunk 合并处理
                                process_text = thinking_buffer + data
                                thinking_buffer = ""

                                while process_text:
                                    if not in_thinking:
                                        # 寻找 <thinking> 开始标签
                                        idx = process_text.find("<thinking>")
                                        if idx >= 0:
                                            before = process_text[:idx]
                                            if before.strip():
                                                dir_content += before
                                                yield {"type": "content", "chunk": before, "direction": direction}
                                            in_thinking = True
                                            process_text = process_text[idx + len("<thinking>"):]
                                        else:
                                            # 检查末尾是否有不完整标签
                                            partial = self._check_partial_tag(process_text, "<thinking>")
                                            if partial:
                                                safe_part = process_text[:-len(partial)]
                                                if safe_part:
                                                    dir_content += safe_part
                                                    yield {"type": "content", "chunk": safe_part, "direction": direction}
                                                thinking_buffer = partial
                                                break
                                            else:
                                                if process_text.strip():
                                                    dir_content += process_text
                                                    yield {"type": "content", "chunk": process_text, "direction": direction}
                                                break
                                    else:
                                        # 寻找 </thinking> 结束标签
                                        idx = process_text.find("</thinking>")
                                        if idx >= 0:
                                            thinking_chunk = process_text[:idx]
                                            if thinking_chunk:
                                                yield {"type": "thinking", "chunk": thinking_chunk, "direction": direction}
                                            in_thinking = False
                                            process_text = process_text[idx + len("</thinking>"):]
                                        else:
                                            partial = self._check_partial_tag(process_text, "</thinking>")
                                            if partial:
                                                safe_part = process_text[:-len(partial)]
                                                if safe_part:
                                                    yield {"type": "thinking", "chunk": safe_part, "direction": direction}
                                                thinking_buffer = partial
                                                break
                                            else:
                                                yield {"type": "thinking", "chunk": process_text, "direction": direction}
                                                break

                # 流结束，处理残留的 thinking buffer
                if thinking_buffer:
                    if in_thinking:
                        yield {"type": "thinking", "chunk": thinking_buffer, "direction": direction}
                    else:
                        dir_content += thinking_buffer

            except httpx.TimeoutException:
                logger.error(f"Stream timeout for direction {direction}")
                yield {"type": "error", "error": "AI服务响应超时", "direction": direction}
                continue
            except httpx.HTTPStatusError as e:
                logger.error(f"Stream HTTP error for direction {direction}: {e.response.status_code}")
                yield {"type": "error", "error": f"AI服务异常: {e.response.status_code}", "direction": direction}
                continue
            except httpx.RequestError as e:
                logger.error(f"Stream connection error for direction {direction}: {e}")
                yield {"type": "error", "error": "无法连接AI服务", "direction": direction}
                continue
            except Exception as e:
                logger.error(f"Stream error for direction {direction}: {e}")
                yield {"type": "error", "error": str(e), "direction": direction}
                continue

            # 从本方向的 content 解析用例
            if dir_content:
                from apps.core.utils.json_parser import JSONParser
                success, parsed, error = JSONParser.try_parse(dir_content)
                if success and parsed:
                    if isinstance(parsed, dict):
                        all_cases.append(parsed)
                    elif isinstance(parsed, list):
                        all_cases.extend(parsed)

        # 标准化用例格式
        normalized_cases = []
        for case in all_cases:
            try:
                normalized_cases.append({
                    "title": case.get("title") or case.get("testpoint") or case.get("name", ""),
                    "steps": case.get("steps") or case.get("test_steps") or case.get("description", ""),
                    "expected_result": case.get("expected_result") or case.get("expectation") or case.get("expected", ""),
                    "priority": case.get("priority", "中"),
                    "test_type": case.get("test_type", ""),
                    "precondition": case.get("precondition", ""),
                    "tags": case.get("tags", []),
                })
            except Exception:
                logger.warning(f"跳过无效测试用例: {case.get('title', 'unknown')}", exc_info=True)
                continue

        yield {"type": "done", "cases": normalized_cases}

    @staticmethod
    def _check_partial_tag(text: str, tag: str) -> str:
        """检查文本末尾是否可能是标签的开头部分，返回最长的未完成部分"""
        for i in range(len(tag) - 1, 0, -1):
            if text.endswith(tag[:i]):
                return tag[:i]
        return ""

    def _get_cache_key(self, input_text: str) -> str:
        """生成缓存key"""
        import hashlib

        hash_value = hashlib.sha256(input_text.encode()).hexdigest()
        return f"ai_gen:{hash_value}"


class AsyncEventLoopManager:
    """
    异步事件循环管理器

    每次调用都创建新的事件循环并在新线程中运行，避免 "event loop is already running" 错误。
    线程安全，支持多线程并发调用。
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化线程池"""
        # 线程池大小，可根据并发需求调整
        max_workers = getattr(settings, "AI_CLIENT_THREAD_POOL_SIZE", 10)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ai_client_")
        logger.info(f"AsyncEventLoopManager initialized with max_workers={max_workers}")

    def run_async(self, coro, timeout: int = None):
        """
        在线程池中运行异步协程

        每次调用都创建新的事件循环，避免事件循环冲突。

        Args:
            coro: 异步协程对象
            timeout: 超时时间（秒），None表示使用默认超时

        Returns:
            协程的返回结果

        Raises:
            AIServiceError: 超时或执行错误
        """
        def run_in_new_loop():
            """在新线程中创建新的事件循环并运行"""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                # 清理：关闭事件循环
                try:
                    new_loop.run_until_complete(new_loop.shutdown_asyncgens())
                except Exception:
                    logger.debug("事件循环清理异常（可忽略）", exc_info=True)
                new_loop.close()

        try:
            future = self._executor.submit(run_in_new_loop)
            actual_timeout = timeout or getattr(settings, "AI_SERVICE_TIMEOUT", 600)
            return future.result(timeout=actual_timeout)
        except TimeoutError:
            logger.error(f"Async operation timed out after {timeout}s")
            raise AIServiceError("AI服务响应超时，请稍后重试", "TIMEOUT")
        except Exception as e:
            logger.error(f"Async operation failed: {e}")
            if isinstance(e, AIServiceError):
                raise
            raise AIServiceError(f"异步操作失败: {str(e)}", "ASYNC_ERROR")


# 全局事件循环管理器实例
_loop_manager = AsyncEventLoopManager()


class AITestCaseClientSync:
    """
    同步版本的AI客户端（用于Django同步视图）

    使用线程池+复用事件循环，优化高并发性能。

    Usage:
        client = AITestCaseClientSync()
        result = client.generate_cases(input_text="...")
    """

    def __init__(self):
        self._async_client = AITestCaseClient()
        self._loop_manager = _loop_manager

    def generate_cases(self, *args, **kwargs) -> AIGenerationResult:
        """
        同步生成测试用例

        使用线程池执行异步任务，避免阻塞主线程。
        """
        return self._loop_manager.run_async(
            self._async_client.generate_cases(*args, **kwargs)
        )

    def generate_cases_stream(self, *args, **kwargs):
        """
        同步流式生成测试用例

        返回生成器，每次yield一个内容片段。
        每次调用都在新线程和新事件循环中运行。
        """
        def run_in_new_loop():
            """在新线程中创建新的事件循环并收集流式数据"""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                chunks = []
                async def collect_chunks():
                    async for chunk in self._async_client.generate_cases_stream(*args, **kwargs):
                        chunks.append(chunk)
                    return chunks
                return new_loop.run_until_complete(collect_chunks())
            finally:
                try:
                    new_loop.run_until_complete(new_loop.shutdown_asyncgens())
                except Exception:
                    logger.debug("事件循环清理异常（可忽略）", exc_info=True)
                new_loop.close()

        # 在线程池中运行
        future = self._loop_manager._executor.submit(run_in_new_loop)
        actual_timeout = getattr(settings, "AI_SERVICE_TIMEOUT", 600)
        chunks = future.result(timeout=actual_timeout)

        for chunk in chunks:
            yield chunk

    def generate_cases_batch(self, *args, **kwargs) -> List[AIGenerationResult]:
        """
        同步批量生成测试用例

        使用线程池执行异步任务，避免阻塞主线程。
        """
        return self._loop_manager.run_async(
            self._async_client.generate_cases_batch(*args, **kwargs)
        )

    def generate_test_cases_for_func_point(
        self,
        module: str,
        func_point: str,
        related_detail: str = "",
        test_directions: List[str] = None,
        temperature: float = None,
    ) -> TestCaseGenerateResult:
        """
        同步为单个功能点生成测试用例（一次请求处理多个测试方向）

        Args:
            module: 模块名称
            func_point: 功能点
            related_detail: 关联需求详情
            test_directions: 测试方向列表
            temperature: 生成温度（可选，用于重试时降低随机性）

        Returns:
            TestCaseGenerateResult: 生成结果
        """
        return self._loop_manager.run_async(
            self._async_client.generate_test_cases_for_func_point(
                module=module,
                func_point=func_point,
                related_detail=related_detail,
                test_directions=test_directions,
                temperature=temperature,
            )
        )

    def health_check(self) -> bool:
        """同步健康检查"""
        return self._loop_manager.run_async(
            self._async_client.health_check(),
            timeout=10  # 健康检查使用较短超时
        )

    def get_service_info(self) -> Optional[dict]:
        """同步获取服务信息"""
        return self._loop_manager.run_async(
            self._async_client.get_service_info(),
            timeout=10  # 获取信息使用较短超时
        )

    def deduplicate_cases(
        self,
        cases: List[Dict[str, Any]],
        threshold: float = 0.85,
    ) -> List[Dict[str, Any]]:
        """
        使用Embedding向量去重测试用例

        Args:
            cases: 用例列表
            threshold: 相似度阈值（默认0.85）

        Returns:
            去重后的用例列表
        """
        if len(cases) <= 1:
            return cases

        embedding_client = OpenAIEmbeddingClient()

        async def _deduplicate():
            duplicates = await embedding_client.find_duplicates(cases, threshold)
            # 过滤掉重复项
            return [case for i, case in enumerate(cases) if i not in duplicates]

        return self._loop_manager.run_async(_deduplicate(), timeout=30)
