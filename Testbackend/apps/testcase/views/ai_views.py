"""
AI生成测试用例视图 - 流式版本（SSE实时推送日志）
支持JSON验证、KTO数据集保存、重试机制
"""
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
import json
import time
import logging

from apps.users.authentication import JWTAuthentication
from apps.testcase.clients.ai_client import AIServiceError, ModelNotReadyError
from apps.testcase.services.ai_generation_service import AIGenerationService, KTODatasetWriter, TestCaseDataValidator

logger = logging.getLogger(__name__)


def _sanitize_log_content(content: str, max_length: int = 200) -> str:
    """
    日志内容脱敏，截断过长内容，避免敏感信息泄露
    """
    if not content:
        return ""
    # 截断内容
    truncated = content[:max_length]
    if len(content) > max_length:
        truncated += "..."
    return truncated


class AIGenerationRateThrottle(UserRateThrottle):
    """AI生成限流：每用户每小时10次（流式接口更严格）"""
    rate = '10/hour'


class AIGenerationBatchRateThrottle(UserRateThrottle):
    """批量生成限流：每用户每小时20次"""
    rate = '20/hour'


@extend_schema(tags=['AI生成'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationBatchRateThrottle])
def generate_test_cases_batch(request):
    """
    AI生成测试用例 - 批量返回（含详细进度信息）

    返回每个步骤的详细日志和每个请求的结果

    Request Body:
        - knowledge_base_ids: 知识库ID列表
        - knowledge_ids: 文件ID列表
        - version_id: 版本ID

    Returns:
        - success: 是否成功
        - logs: 步骤日志列表
        - requests: 每个请求的详细信息列表
        - cases: 所有创建的测试用例
        - errors: 所有错误详情
    """
    knowledge_base_ids = request.data.get("knowledge_base_ids", [])
    knowledge_ids = request.data.get("knowledge_ids", [])
    version_id = request.data.get("version_id")

    if not knowledge_base_ids:
        return Response(
            {"success": False, "error": "knowledge_base_ids不能为空"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not version_id:
        return Response(
            {"success": False, "error": "version_id不能为空"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 日志收集
    logs = []

    def add_log(step, status, message, data=None):
        logs.append({
            "step": step,
            "status": status,
            "message": message,
            "data": data or {},
            "timestamp": time.time()
        })

    try:
        from apps.knowledge.services.requirement_service import RequirementService
        from apps.testcase.models import TestCase, TestModule

        service = AIGenerationService()
        req_service = RequirementService()

        # 1. 需求提取
        add_log("extract", "start", "开始提取需求...")

        requirements, session_id = req_service.extract(
            knowledge_base_ids, knowledge_ids
        )

        if not requirements:
            add_log("extract", "complete", "未提取到功能点", {"count": 0})
            return Response({
                "success": True,
                "created_count": 0,
                "error_count": 0,
                "logs": logs,
                "requests": [],
                "cases": [],
                "errors": [],
            })

        add_log("extract", "complete", f"提取完成，共{len(requirements)}个功能点", {
            "count": len(requirements),
            "requirements": [{"module": r.get("模块"), "func_point": r.get("功能点")} for r in requirements[:10]]
        })

        # 2. 检索关联需求
        add_log("retrieve", "start", f"开始检索关联需求，共{len(requirements)}个功能点...")

        requirements_with_details = req_service.retrieve_related(
            requirements, knowledge_base_ids, knowledge_ids, session_id,
            parallel=True, max_workers=5
        )

        add_log("retrieve", "complete", f"检索完成，共{len(requirements_with_details)}个功能点")

        # 3. 构建批量请求
        add_log("build", "start", "构建AI请求...")

        batch_items = []
        item_mapping = []

        for item in requirements_with_details:
            base_text = service._build_input_text(item)
            for j, prompt in enumerate(service.TEST_PROMPTS):
                batch_items.append({'input_text': f"{base_text}\n{prompt}"})
                item_mapping.append({
                    'module': item['module'],
                    'func_point': item['func_point'],
                    'test_type_index': j,
                })

        add_log("build", "complete", f"构建完成，共{len(batch_items)}个请求", {
            "total_requests": len(batch_items),
            "function_points": len(requirements_with_details),
            "test_directions": len(service.TEST_PROMPTS)
        })

        # 4. 预创建模块
        add_log("module", "start", "创建模块...")

        module_names = set(m['module'] for m in item_mapping if m.get('module'))
        module_map = {}
        for name in module_names:
            module_map[name] = TestModule.objects.get_or_create(
                version_id=version_id,
                name=name,
                defaults={'sort_order': 0}
            )[0]

        add_log("module", "complete", f"模块创建完成，共{len(module_map)}个模块")

        # 5. 批量调用AI
        add_log("generate", "start", f"开始调用AI生成，共{len(batch_items)}个请求...", {
            "total_requests": len(batch_items)
        })

        total_start_time = time.time()
        ai_results = service.ai_client.generate_cases_batch(batch_items)
        total_elapsed = time.time() - total_start_time

        add_log("generate", "complete", f"AI生成完成，耗时{total_elapsed:.2f}秒")

        # 6. 处理结果
        add_log("save", "start", "保存测试用例...")

        requests_detail = []
        all_cases = []
        all_errors = []
        total_created = 0
        total_errors = 0

        for i, (ai_result, mapping) in enumerate(zip(ai_results, item_mapping)):
            test_type = service.TEST_TYPE_NAMES[mapping['test_type_index']]
            request_info = {
                "index": i + 1,
                "module": mapping['module'],
                "func_point": mapping['func_point'],
                "test_type": test_type,
            }

            if ai_result.success and ai_result.result:
                cases_data = ai_result.result if isinstance(ai_result.result, list) else [ai_result.result]
                created_in_request = []

                for case_data in cases_data:
                    try:
                        module_name = mapping.get('module', '')
                        priority = service._parse_priority(case_data.get("priority"))
                        steps_text = service._parse_steps(case_data)
                        expected_result_text = service._parse_expected_result(case_data)
                        title = service._parse_title(case_data) or f"{module_name}-{mapping.get('func_point', '测试用例')}"
                        precondition = service._parse_precondition(case_data)

                        module = module_map.get(module_name)

                        case = TestCase.objects.create(
                            title=title,
                            precondition=precondition,
                            priority=priority,
                            tags=case_data.get("tags", []),
                            requirement=f"{module_name}: {mapping.get('func_point', '')}",
                            version_id=version_id,
                            module=module,
                            created_by=request.user,
                            updated_by=request.user,
                            generation_source="ai_generated",
                            review_status="pending",
                            steps=steps_text,
                            expected_result=expected_result_text,
                        )

                        created_in_request.append({
                            'id': case.id,
                            'title': case.title,
                            'priority': case.priority,
                        })
                        total_created += 1
                        all_cases.append({
                            'id': case.id,
                            'title': case.title,
                            'module': module_name,
                            'priority': case.priority,
                        })

                    except Exception as e:
                        total_errors += 1
                        all_errors.append({
                            'request_index': i + 1,
                            'module': mapping['module'],
                            'func_point': mapping['func_point'],
                            'error': str(e),
                        })

                request_info["success"] = True
                request_info["cases_count"] = len(created_in_request)
                request_info["cases"] = created_in_request

            else:
                request_info["success"] = False
                request_info["error"] = ai_result.error or "生成失败"
                request_info["cases_count"] = 0
                request_info["cases"] = []
                total_errors += 1
                all_errors.append({
                    'request_index': i + 1,
                    'module': mapping['module'],
                    'func_point': mapping['func_point'],
                    'error': ai_result.error or "生成失败",
                })

            requests_detail.append(request_info)

        add_log("save", "complete", f"保存完成，成功{total_created}条，失败{total_errors}条", {
            "created": total_created,
            "errors": total_errors
        })

        return Response({
            "success": True,
            "created_count": total_created,
            "error_count": total_errors,
            "total_requests": len(batch_items),
            "total_elapsed": round(total_elapsed, 2),
            "logs": logs,
            "requests": requests_detail,
            "cases": all_cases,
            "errors": all_errors,
            "session_id": session_id,
        })

    except ModelNotReadyError:
        add_log("error", "error", "AI服务暂不可用，请稍后重试")
        return Response(
            {"success": False, "error": "AI服务暂不可用，请稍后重试", "logs": logs},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except AIServiceError as e:
        add_log("error", "error", e.message)
        return Response(
            {"success": False, "error": e.message, "code": e.code, "logs": logs},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        add_log("error", "error", str(e))
        return Response(
            {"success": False, "error": str(e), "logs": logs},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from django.views.decorators.csrf import csrf_exempt


def _check_rate_limit(request):
    """
    手动限流检查（用于原生Django视图）
    返回 (allowed, error_response)
    """
    from rest_framework.throttling import UserRateThrottle
    from rest_framework.request import Request

    throttle = AIGenerationRateThrottle()
    drf_request = Request(request)

    if not throttle.allow_request(drf_request, None):
        return False, JsonResponse(
            {"success": False, "error": "请求过于频繁，请稍后再试"},
            status=429
        )
    return True, None


@csrf_exempt
def generate_test_cases_stream_native(request):
    """
    AI生成测试用例 - SSE流式返回（原生 Django 视图）

    使用 Server-Sent Events 实时推送每个步骤的日志
    """
    import json
    from django.http import JsonResponse, StreamingHttpResponse
    from apps.users.authentication import JWTAuthentication

    # 限流检查
    allowed, error_response = _check_rate_limit(request)
    if not allowed:
        return error_response

    # 获取 Origin
    origin = request.META.get('HTTP_ORIGIN', 'http://localhost:5174')

    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # JWT 认证
    auth = JWTAuthentication()
    auth_result = auth.authenticate(request)
    if auth_result is None:
        response = JsonResponse({'success': False, 'error': '未认证'}, status=401)
        response['Access-Control-Allow-Origin'] = origin
        return response

    user, token = auth_result
    request.user = user

    # 解析请求体
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        response = JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        response['Access-Control-Allow-Origin'] = origin
        return response

    knowledge_base_ids = body.get("knowledge_base_ids", [])
    knowledge_ids = body.get("knowledge_ids", [])
    version_id = body.get("version_id")

    logger.info(f"Stream request: kb_ids={knowledge_base_ids}, knowledge_ids={knowledge_ids}, version_id={version_id}")

    if not knowledge_base_ids:
        response = JsonResponse({'success': False, 'error': 'knowledge_base_ids不能为空'}, status=400)
        response['Access-Control-Allow-Origin'] = origin
        return response

    if not version_id:
        response = JsonResponse({'success': False, 'error': 'version_id不能为空'}, status=400)
        response['Access-Control-Allow-Origin'] = origin
        return response

    # 权限验证：检查用户是否有权限访问该版本
    try:
        from apps.testcase.models import TestCaseRepository, TestCaseVersion
        version = TestCaseVersion.objects.filter(id=version_id).select_related('repository').first()
        if not version:
            response = JsonResponse({'success': False, 'error': '版本不存在'}, status=404)
            response['Access-Control-Allow-Origin'] = origin
            return response

        # 检查用户是否是项目的成员
        from apps.projects.models import ProjectMember
        project_id = version.repository.project_id
        if not ProjectMember.objects.filter(project_id=project_id, user=user).exists():
            response = JsonResponse({'success': False, 'error': '您没有权限访问该项目'}, status=403)
            response['Access-Control-Allow-Origin'] = origin
            return response
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        # 权限检查失败不阻止流程，只记录日志
        pass

    # 生成唯一的任务ID，用于取消机制
    import uuid
    task_id = str(uuid.uuid4())

    def send_event(event_type, data):
        # 添加注释行来强制flush（某些服务器需要）
        return f": keepalive\n\nevent: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def check_cancelled():
        """检查任务是否被取消"""
        from django.core.cache import cache
        return cache.get(f"ai_gen_cancel:{task_id}", False)

    def generate_stream():
        try:
            from apps.knowledge.services.requirement_service import RequirementService
            from apps.testcase.models import TestCase, TestModule
            from django.core.cache import cache

            logger.info(f"Starting stream generation, task_id={task_id}")

            # 发送task_id给前端，用于取消操作
            yield send_event("started", {"task_id": task_id})

            service = AIGenerationService()
            req_service = RequirementService()

            # 检查是否被取消
            if check_cancelled():
                yield send_event("cancelled", {"message": "任务已取消"})
                return

            # 1. 创建会话并提取需求
            step_start_time = time.time()
            yield send_event("progress", {
                "step": "extract",
                "status": "start",
                "message": "开始需求提炼..."
            })

            create_result = req_service.repository.create_session(knowledge_base_ids[0])
            if not create_result.get('success'):
                yield send_event("progress", {
                    "step": "extract",
                    "status": "error",
                    "message": f"创建会话失败: {create_result.get('error')}"
                })
                yield send_event("error", {"error": f"创建会话失败: {create_result.get('error')}"})
                return

            session_id = create_result['data']['id']

            mentioned_items = req_service._build_mentioned_items(knowledge_base_ids, knowledge_ids)
            query_text = req_service.DEFAULT_REQUIREMENT_QUERY

            # 使用try-finally确保会话被销毁
            try:
                result = req_service.repository.agent_chat(
                    session_id=session_id,
                    query=query_text,
                    knowledge_base_ids=knowledge_base_ids,
                    knowledge_ids=knowledge_ids,
                    mentioned_items=mentioned_items,
                    agent_id='builtin-smart-reasoning',
                    temperature=0.2,
                    max_tokens=4096,
                )
            finally:
                # 无论成功失败都销毁会话，避免WeKnora会话堆积
                try:
                    req_service.repository.delete_session(session_id)
                    logger.info(f"Session deleted after agent chat: {session_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete session {session_id}: {e}")

            if not result.get('success'):
                yield send_event("progress", {
                    "step": "extract",
                    "status": "error",
                    "message": f"需求提取失败: {result.get('error')}"
                })
                yield send_event("error", {"error": f"需求提取失败: {result.get('error')}"})
                return

            content = result['data']['content']

            from apps.core.utils.json_parser import JSONParser
            success, requirements, error = JSONParser.try_parse(content)

            if not success:
                logger.error(f"JSON解析失败，原始内容: {_sanitize_log_content(content, 100)}")
                yield send_event("progress", {
                    "step": "extract",
                    "status": "error",
                    "message": f"需求提取失败: JSON解析错误"
                })
                yield send_event("error", {
                    "error": f"JSON解析失败: {error}",
                    "hint": "AI返回的数据格式不正确，请重试或检查需求文档内容",
                })
                return

            extract_elapsed = time.time() - step_start_time
            if not requirements:
                yield send_event("progress", {
                    "step": "extract",
                    "status": "complete",
                    "message": "未提取到功能点",
                    "data": {"count": 0},
                    "elapsed": extract_elapsed
                })
                yield send_event("complete", {
                    "success": True,
                    "created_count": 0,
                    "error_count": 0,
                    "message": "未提取到功能点"
                })
                return

            yield send_event("progress", {
                "step": "extract",
                "status": "complete",
                "message": f"需求提炼完成，共{len(requirements)}个功能点",
                "data": {
                    "count": len(requirements),
                    "requirements": [{"module": r.get("模块"), "func_point": r.get("功能点")} for r in requirements[:10]],
                    "show_detail": False
                },
                "elapsed": extract_elapsed
            })

            # 4. 检索关联需求（使用向量检索，并行执行）
            step_start_time = time.time()
            yield send_event("progress", {
                "step": "retrieve",
                "status": "start",
                "message": "正在检索功能点所关联内容..."
            })

            # 分批并行智能推理检索
            from concurrent.futures import ThreadPoolExecutor, as_completed
            batch_size = 10  # 每批处理的功能点数量
            total_batches = (len(requirements) + batch_size - 1) // batch_size
            logger.info(f"开始分批并行智能推理检索，共 {len(requirements)} 个功能点，分 {total_batches} 批")

            def process_batch(batch_idx, batch_requirements):
                """处理单个批次"""
                logger.debug(f"处理第 {batch_idx + 1} 批，功能点 {len(batch_requirements)} 个")

                # 创建会话
                create_result = req_service.repository.create_session(knowledge_base_ids[0])
                if not create_result.get('success'):
                    logger.error(f"创建会话失败: {create_result.get('error')}")
                    return batch_idx, [
                        {
                            'module': req.get('模块', ''),
                            'func_point': req.get('功能点', ''),
                            'related_detail': '',
                            'related_chunks': [],
                        }
                        for req in batch_requirements
                    ]

                session_id = create_result['data']['id']
                mentioned_items = req_service._build_mentioned_items(knowledge_base_ids, knowledge_ids)

                try:
                    # 构建批量查询
                    func_points_text = "\n".join([
                        f"{i+1}. {item.get('功能点', '')}"
                        for i, item in enumerate(batch_requirements)
                    ])

                    batch_query = f"""请根据需求文档原文，找出以下功能点对应的相关内容。

功能点列表：
{func_points_text}

重要要求：
1. 必须为每个功能点都返回结果，不能遗漏任何一个
2. 必须直接引用文档原文，不要改写或总结
3. 引用的内容要完整，包含功能描述的关键信息
4. 如果原文中有多个相关段落，可以合并引用
5. 每个功能点引用的原文不超过300字
6. 如果找不到完全匹配的原文，返回最相关的段落

请严格按以下JSON格式返回（必须包含所有{len(batch_requirements)}个功能点）：
[
  {{"index": 1, "content": "原文引用..."}},
  {{"index": 2, "content": "原文引用..."}},
  ...
  {{"index": {len(batch_requirements)}, "content": "原文引用..."}}
]

注意：
1. 只返回JSON数组，不要其他说明文字
2. content必须是文档原文，不能是AI生成的总结
3. index从1开始，必须连续，不能跳过任何一个编号
4. 总共必须返回{len(batch_requirements)}条结果"""

                    agent_result = req_service.repository.agent_chat(
                        session_id=session_id,
                        query=batch_query,
                        knowledge_base_ids=knowledge_base_ids,
                        knowledge_ids=knowledge_ids,
                        mentioned_items=mentioned_items,
                        agent_id='builtin-smart-reasoning',
                        temperature=0.2,
                        max_tokens=4096,
                    )

                    if agent_result.get('success'):
                        content = agent_result['data'].get('content', '')
                        logger.debug(f"第 {batch_idx + 1} 批返回内容长度: {len(content)}")

                        # 解析JSON结果
                        from apps.core.utils.json_parser import JSONParser
                        success, parsed_results, error = JSONParser.try_parse(content)

                        if success and parsed_results:
                            logger.debug(f"第 {batch_idx + 1} 批解析成功: {len(parsed_results)} 条结果")

                            # 构建结果映射
                            result_map = {}
                            for item in parsed_results:
                                idx = item.get('index', 0)
                                content_val = item.get('content', '')
                                if idx > 0:
                                    result_map[idx - 1] = content_val

                            # 检查是否有遗漏的功能点
                            missing_indices = [i for i in range(len(batch_requirements)) if i not in result_map]
                            if missing_indices:
                                logger.info(f"第 {batch_idx + 1} 批有遗漏功能点: {missing_indices}，开始单独检索")
                                # 对遗漏的功能点单独检索
                                for missing_idx in missing_indices:
                                    missing_req = batch_requirements[missing_idx]
                                    missing_func_point = missing_req.get('功能点', '')

                                    # 单独查询
                                    single_query = f"""请从需求文档中找出以下功能点对应的原文内容。

功能点：{missing_func_point}

要求：
1. 直接引用文档原文
2. 如果找不到完全匹配，返回最相关的段落
3. 只返回原文内容，不要添加任何解释

原文内容："""

                                    single_result = req_service.repository.agent_chat(
                                        session_id=session_id,
                                        query=single_query,
                                        knowledge_base_ids=knowledge_base_ids,
                                        knowledge_ids=knowledge_ids,
                                        mentioned_items=mentioned_items,
                                        agent_id='builtin-smart-reasoning',
                                        temperature=0.2,
                                        max_tokens=500,
                                    )

                                    if single_result.get('success'):
                                        single_content = single_result['data'].get('content', '')
                                        logger.debug(f"单独检索 index={missing_idx + 1} 成功，长度: {len(single_content)}")
                                        result_map[missing_idx] = single_content[:500]

                            # 组装结果
                            results = []
                            for i, req in enumerate(batch_requirements):
                                related_content = result_map.get(i, '')
                                results.append({
                                    'module': req.get('模块', ''),
                                    'func_point': req.get('功能点', ''),
                                    'related_detail': related_content[:500] if related_content else '',
                                    'related_chunks': [{
                                        'content': related_content[:500] if related_content else '',
                                        'score': 1.0,
                                        'knowledge_title': '智能推理',
                                        'chunk_index': 0,
                                    }] if related_content else [],
                                })
                            return batch_idx, results
                        else:
                            logger.warning(f"第 {batch_idx + 1} 批JSON解析失败: {error}")
                    else:
                        logger.error(f"第 {batch_idx + 1} 批Agent失败: {agent_result.get('error')}")

                except Exception as e:
                    logger.error(f"第 {batch_idx + 1} 批异常: {e}")

                finally:
                    try:
                        req_service.repository.delete_session(session_id)
                    except:
                        pass

                # 返回空结果
                return batch_idx, [
                    {
                        'module': req.get('模块', ''),
                        'func_point': req.get('功能点', ''),
                        'related_detail': '',
                        'related_chunks': [],
                    }
                    for req in batch_requirements
                ]

            # 准备批次数据
            batches = []
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(requirements))
                batches.append((batch_idx, requirements[start_idx:end_idx]))

            # 并行处理所有批次
            batch_results = [None] * total_batches
            max_workers = min(3, total_batches)  # 并发数，最多3个

            with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="batch_") as executor:
                futures = {
                    executor.submit(process_batch, batch_idx, batch_reqs): batch_idx
                    for batch_idx, batch_reqs in batches
                }

                for future in as_completed(futures):
                    if check_cancelled():
                        for f in futures:
                            f.cancel()
                        yield send_event("cancelled", {"message": "任务已取消"})
                        return

                    batch_idx, results = future.result()
                    batch_results[batch_idx] = results

            # 合并所有批次结果
            requirements_with_details = []
            for results in batch_results:
                if results:
                    requirements_with_details.extend(results)

            # 检查是否被取消
            if check_cancelled():
                yield send_event("cancelled", {"message": "任务已取消"})
                return

            # 统计检索结果
            retrieve_elapsed = time.time() - step_start_time
            has_related = sum(1 for r in requirements_with_details if r['related_detail'])

            # 调试：打印第一个结果的详细信息
            if requirements_with_details and len(requirements_with_details) > 0:
                first = requirements_with_details[0]
                logger.info(f"调试 - 第一个结果: module={first.get('module')}, func_point={first.get('func_point')[:30]}, chunks_count={len(first.get('related_chunks', []))}, related_detail_len={len(first.get('related_detail', ''))}")
                if first.get('related_chunks'):
                    logger.info(f"调试 - 第一个chunk: {first['related_chunks'][0]}")

            retrieve_details = [
                {
                    'module': r['module'],
                    'func_point': r['func_point'][:50] + '...' if len(r['func_point']) > 50 else r['func_point'],
                    'has_related': bool(r['related_detail']),
                    'chunks_count': len(r['related_chunks']),
                    'related_chunks': r['related_chunks'],  # 包含检索内容
                }
                for r in requirements_with_details[:20]  # 只返回前20个
            ]

            yield send_event("progress", {
                "step": "retrieve",
                "status": "complete",
                "message": f"检索完成，共{len(requirements_with_details)}个功能点，{has_related}个有关联内容",
                "data": {
                    "total": len(requirements_with_details),
                    "has_related": has_related,
                    "retrieve_details": retrieve_details,
                },
                "elapsed": retrieve_elapsed
            })

            # 3. 预创建模块
            step_start_time = time.time()
            yield send_event("progress", {
                "step": "module",
                "status": "start",
                "message": "创建测试模块..."
            })

            # 收集所有模块名
            module_names = set()
            for item in requirements_with_details:
                module_names.add(item['module'])

            module_map = {}
            for name in module_names:
                if name:
                    module_map[name] = TestModule.objects.get_or_create(
                        version_id=version_id,
                        name=name,
                        defaults={'sort_order': 0}
                    )[0]

            module_elapsed = time.time() - step_start_time

            yield send_event("progress", {
                "step": "module",
                "status": "complete",
                "message": f"模块创建完成，共{len(module_map)}个模块",
                "elapsed": module_elapsed
            })

            # 检查是否被取消
            if check_cancelled():
                yield send_event("cancelled", {"message": "任务已取消"})
                return

            # 4. 使用新接口并行生成测试用例（每个功能点一次请求）
            total_requests = len(requirements_with_details)
            step_start_time = time.time()
            yield send_event("progress", {
                "step": "generate",
                "status": "start",
                "message": f"开始AI生成测试用例，共{total_requests}个功能点..."
            })

            total_start_time = time.time()
            total_created = 0
            total_errors = 0
            total_duplicates = 0
            all_cases = []

            # 使用线程池并行发送请求
            from concurrent.futures import ThreadPoolExecutor
            import queue
            import threading

            # 线程安全的结果队列
            result_queue = queue.Queue()

            def process_func_point(index, item):
                """处理单个功能点的测试用例生成（流式推送 thinking）"""
                if check_cancelled():
                    result_queue.put({'type': 'task_done'})
                    return

                module = item['module']
                func_point = item['func_point']
                related_detail = item.get('related_detail', '')

                request_start_time = time.time()

                # 发送"发送中"事件
                result_queue.put({
                    'type': 'request',
                    'data': {
                        "index": index + 1,
                        "total": total_requests,
                        "status": "sending",
                        "module": module,
                        "func_point": func_point,
                    }
                })

                def validate_case_fields(case_data):
                    """验证用例字段是否完整"""
                    required_fields = ['title', 'steps', 'expected_result']
                    # 无效的默认值
                    invalid_defaults = ['未命名用例', '未命名', '无', '暂无', '']
                    missing_fields = []
                    for field in required_fields:
                        value = case_data.get(field, '')
                        # 检查是否为空
                        if not value or (isinstance(value, str) and not value.strip()):
                            missing_fields.append(field)
                        # 检查是否为无效默认值（仅对title字段）
                        elif field == 'title' and isinstance(value, str) and value.strip() in invalid_defaults:
                            missing_fields.append(field)
                    return missing_fields

                def validate_cases(cases):
                    """验证用例列表，返回有效用例和有问题的用例"""
                    valid_cases = []
                    invalid_cases = []
                    for case in cases:
                        missing = validate_case_fields(case)
                        if missing:
                            invalid_cases.append({'case': case, 'missing_fields': missing})
                        else:
                            valid_cases.append(case)
                    return valid_cases, invalid_cases

                try:
                    # 首次尝试：使用流式调用，实时推送 thinking
                    # process_func_point 已在 ThreadPoolExecutor 工作线程中，
                    # 可以安全创建新事件循环运行异步流式生成器
                    from apps.testcase.clients.ai_client import AITestCaseClient
                    import asyncio as _asyncio

                    stream_result = None
                    stream_error = None
                    client = None  # 非流式回退时赋值

                    _loop = _asyncio.new_event_loop()
                    _asyncio.set_event_loop(_loop)
                    try:
                        async def _stream_and_push():
                            async_client = AITestCaseClient()
                            async for chunk in async_client.generate_test_cases_for_func_point_stream(
                                module=module,
                                func_point=func_point,
                                related_detail=related_detail,
                            ):
                                chunk_type = chunk.get("type")
                                if chunk_type == "thinking":
                                    result_queue.put({
                                        'type': 'thinking_chunk',
                                        'data': {
                                            "index": index + 1,
                                            "chunk": chunk.get("chunk", ""),
                                        }
                                    })
                                elif chunk_type == "done":
                                    return chunk
                                elif chunk_type == "error":
                                    nonlocal stream_error
                                    stream_error = chunk.get("error", "")
                                    logger.warning(f"[流式生成] 功能点 [{func_point}] 方向 {chunk.get('direction', '')} 错误: {stream_error}")
                            return None

                        stream_result = _loop.run_until_complete(_stream_and_push())
                    except Exception as e:
                        logger.error(f"[流式生成异常] 功能点 [{func_point}]: {e}")
                        stream_error = str(e)
                    finally:
                        try:
                            _loop.run_until_complete(_loop.shutdown_asyncgens())
                        except Exception:
                            pass
                        _loop.close()

                    if stream_result and stream_result.get("type") == "done":
                        stream_cases = stream_result.get("cases", [])
                    else:
                        stream_cases = []

                    # 验证流式结果
                    valid_cases = []
                    if stream_cases:
                        valid_cases, invalid_cases = validate_cases(stream_cases)
                        if invalid_cases:
                            logger.warning(f"[流式生成] 功能点 [{func_point}]: {len(invalid_cases)} 个用例字段不完整，完整用例 {len(valid_cases)} 个")

                    # 如果流式生成未获得完整用例，回退到带重试的非流式方式
                    if not valid_cases:
                        logger.info(f"[回退非流式] 功能点 [{func_point}]: 流式未获得完整用例，尝试非流式重试")
                        from apps.testcase.clients.ai_client import AITestCaseClientSync
                        client = AITestCaseClientSync()

                        accumulated_cases = {}  # key: title, value: case

                        for attempt in range(3):
                            try:
                                temperature = None
                                if attempt > 0:
                                    temperature = max(0.5, 1.0 - attempt * 0.1 - (attempt > 1) * 0.1)

                                result = client.generate_test_cases_for_func_point(
                                    module=module,
                                    func_point=func_point,
                                    related_detail=related_detail,
                                    temperature=temperature,
                                )

                                if not result.success:
                                    logger.warning(f"[重试 {attempt+1}/3] 功能点 [{func_point}]: {result.error}")
                                    continue

                                cases = result.cases or []
                                if not cases:
                                    logger.warning(f"[重试 {attempt+1}/3] 功能点 [{func_point}]: 未生成用例")
                                    continue

                                retry_valid, retry_invalid = validate_cases(cases)
                                for case in retry_valid:
                                    title = case.get('title', '')
                                    if title and title not in accumulated_cases:
                                        accumulated_cases[title] = case

                                if not retry_invalid:
                                    break

                            except Exception as e:
                                logger.error(f"[重试异常 {attempt+1}/3] 功能点 [{func_point}]: {e}")

                        valid_cases = list(accumulated_cases.values())

                    request_elapsed = time.time() - request_start_time

                    if not valid_cases:
                        logger.warning(f"[最终失败] 功能点 [{func_point}]: 未能获得完整用例")
                        result_queue.put({
                            'type': 'request',
                            'data': {
                                "index": index + 1,
                                "total": total_requests,
                                "status": "error",
                                "module": module,
                                "func_point": func_point,
                                "error": stream_error or "未能生成完整用例",
                                "elapsed": request_elapsed,
                            },
                            'success': False,
                        })
                        return

                    cases = valid_cases
                    logger.info(f"[AI用例] 功能点 [{func_point}]: 收到 {len(cases)} 个完整用例")

                    # 向量去重
                    if len(cases) > 1:
                        try:
                            from apps.testcase.clients.ai_client import AITestCaseClientSync
                            _dedup_client = client or AITestCaseClientSync()
                            original_count = len(cases)
                            cases = _dedup_client.deduplicate_cases(cases, threshold=0.85)
                            duplicates_removed = original_count - len(cases)
                            if duplicates_removed > 0:
                                logger.info(f"功能点 [{func_point}] 去重: {original_count} -> {len(cases)}，移除 {duplicates_removed} 个重复用例")
                        except Exception as e:
                            logger.warning(f"向量去重失败: {e}，保留所有用例")

                    # 保存用例
                    created_cases = []
                    with transaction.atomic():
                        for case_data in cases:
                            try:
                                priority = service._parse_priority(case_data.get("priority"))
                                steps_text = case_data.get("steps", "")
                                expected_result_text = case_data.get("expected_result", "")
                                title = case_data.get("title", "") or f"{module}-{func_point}"
                                precondition = case_data.get("precondition", "")
                                test_type = case_data.get("test_type", "")

                                module_obj = module_map.get(module)

                                case = TestCase.objects.create(
                                    title=title,
                                    precondition=precondition,
                                    priority=priority,
                                    tags=case_data.get("tags", []),
                                    requirement=f"{module}: {func_point}",
                                    version_id=version_id,
                                    module=module_obj,
                                    created_by=user,
                                    updated_by=user,
                                    generation_source="ai_generated",
                                    review_status="pending",
                                    steps=steps_text,
                                    expected_result=expected_result_text,
                                )

                                created_cases.append({
                                    'id': case.id,
                                    'title': case.title,
                                    'priority': case.priority,
                                    'test_type': test_type,
                                })

                            except Exception as e:
                                logger.error(f"保存用例失败: {e}")

                    logger.info(f"[保存完成] 功能点 [{func_point}]: 创建 {len(created_cases)} 个用例")
                    result_queue.put({
                        'type': 'request',
                        'data': {
                            "index": index + 1,
                            "total": total_requests,
                            "status": "success",
                            "module": module,
                            "func_point": func_point,
                            "cases_count": len(created_cases),
                            "cases": created_cases,
                            "elapsed": request_elapsed,
                        },
                        'success': True,
                        'cases_count': len(created_cases),
                    })

                except Exception as e:
                    request_elapsed = time.time() - request_start_time
                    logger.error(f"[AI异常] 功能点 [{func_point}]: {type(e).__name__}: {e}")
                    result_queue.put({
                        'type': 'request',
                        'data': {
                            "index": index + 1,
                            "total": total_requests,
                            "status": "error",
                            "module": module,
                            "func_point": func_point,
                            "error": str(e),
                            "elapsed": request_elapsed,
                        },
                        'success': False,
                    })

                finally:
                    result_queue.put({'type': 'task_done'})

            # 并行执行请求
            max_workers = getattr(settings, "AI_CLIENT_THREAD_POOL_SIZE", 5)

            with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ai_gen_") as executor:
                futures = set()

                # 提交所有任务
                for i, item in enumerate(requirements_with_details):
                    future = executor.submit(process_func_point, i, item)
                    futures.add(future)

                # 实时处理结果队列
                completed_count = 0

                while completed_count < total_requests:
                    try:
                        result = result_queue.get(timeout=0.1)

                        if result.get('type') == 'task_done':
                            completed_count += 1
                        elif result.get('type') == 'thinking_chunk':
                            yield send_event("thinking_chunk", result['data'])
                        elif result.get('type') == 'request':
                            yield send_event("request", result['data'])

                            if result.get('success'):
                                total_created += result.get('cases_count', 0)
                            else:
                                total_errors += 1

                    except queue.Empty:
                        continue

                # 确保所有future都被处理
                for future in futures:
                    try:
                        future.result(timeout=1)
                    except Exception:
                        pass
                futures.clear()

            total_elapsed = time.time() - total_start_time
            generate_elapsed = time.time() - step_start_time

            # 5. 完成
            yield send_event("progress", {
                "step": "complete",
                "status": "complete",
                "message": f"AI生成完成，耗时{total_elapsed:.2f}秒，成功{total_created}条，失败{total_errors}条",
                "data": {"created": total_created, "errors": total_errors, "elapsed": round(total_elapsed, 2)},
                "elapsed": generate_elapsed
            })

            yield send_event("complete", {
                "success": True,
                "created_count": total_created,
                "error_count": total_errors,
                "total_requests": total_requests,
                "total_elapsed": round(total_elapsed, 2),
                "cases": all_cases,
            })

        except ModelNotReadyError:
            logger.error("Model not ready error")
            yield send_event("error", {
                "error": "AI服务暂不可用，请稍后重试",
                "code": "MODEL_NOT_READY"
            })
        except AIServiceError as e:
            logger.error(f"AI service error: {e.message}, code: {e.code}")
            yield send_event("error", {
                "error": e.message,
                "code": e.code,
                "details": e.details if hasattr(e, 'details') else None
            })
        except Exception as e:
            logger.error(f"Stream generation error: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            yield send_event("error", {
                "error": str(e),
                "code": "INTERNAL_ERROR",
                "traceback": traceback.format_exc() if settings.DEBUG else None
            })

    response = StreamingHttpResponse(
        generate_stream(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = origin
    response['Access-Control-Allow-Credentials'] = 'true'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response


@extend_schema(tags=['AI生成'])
@api_view(['POST', 'OPTIONS'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@throttle_classes([AIGenerationRateThrottle])
def generate_test_cases_stream(request):
    """
    AI生成测试用例 - SSE流式返回（实时推送日志）

    使用Server-Sent Events实时推送每个步骤的日志
    """
    # 处理 OPTIONS 预检请求
    if request.method == 'OPTIONS':
        response = Response({})
        response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    knowledge_base_ids = request.data.get("knowledge_base_ids", [])
    knowledge_ids = request.data.get("knowledge_ids", [])
    version_id = request.data.get("version_id")

    logger.info(f"Stream request received: kb_ids={knowledge_base_ids}, knowledge_ids={knowledge_ids}, version_id={version_id}")

    if not knowledge_base_ids:
        return Response(
            {"success": False, "error": "knowledge_base_ids不能为空"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not version_id:
        return Response(
            {"success": False, "error": "version_id不能为空"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 获取当前用户
    user = request.user

    def send_event(event_type, data):
        """发送SSE事件"""
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def generate_stream():
        try:
            from apps.knowledge.services.requirement_service import RequirementService
            from apps.testcase.models import TestCase, TestModule

            logger.info(f"Starting stream generation: kb_ids={knowledge_base_ids}, knowledge_ids={knowledge_ids}, version_id={version_id}")

            service = AIGenerationService()
            req_service = RequirementService()

            # 1. 需求提取
            yield send_event("progress", {
                "step": "extract",
                "status": "start",
                "message": "开始提取需求..."
            })

            requirements, session_id = req_service.extract(
                knowledge_base_ids, knowledge_ids
            )

            if not requirements:
                yield send_event("progress", {
                    "step": "extract",
                    "status": "complete",
                    "message": "未提取到功能点",
                    "data": {"count": 0}
                })
                yield send_event("complete", {
                    "success": True,
                    "created_count": 0,
                    "error_count": 0,
                    "message": "未提取到功能点"
                })
                return

            yield send_event("progress", {
                "step": "extract",
                "status": "complete",
                "message": f"提取完成，共{len(requirements)}个功能点",
                "data": {
                    "count": len(requirements),
                    "requirements": [{"module": r.get("模块"), "func_point": r.get("功能点")} for r in requirements[:10]]
                }
            })

            # 2. 检索关联需求 - 逐个处理并实时推送进度
            yield send_event("progress", {
                "step": "retrieve",
                "status": "start",
                "message": f"开始检索关联需求，共{len(requirements)}个功能点..."
            })

            requirements_with_details = []
            mentioned_items = req_service._build_mentioned_items(knowledge_base_ids, knowledge_ids)

            for i, item in enumerate(requirements):
                module = item.get('模块', '')
                func_point = item.get('功能点', '')

                # 推送当前检索进度
                yield send_event("progress", {
                    "step": "retrieve",
                    "status": "processing",
                    "message": f"检索关联需求 [{i+1}/{len(requirements)}]: {module} - {func_point[:20]}...",
                    "data": {"current": i + 1, "total": len(requirements)}
                })

                query = req_service.RELATED_REQUIREMENT_QUERY.format(func_point=func_point)
                result = req_service.repository.agent_chat(
                    session_id=session_id,
                    query=query,
                    knowledge_base_ids=knowledge_base_ids,
                    knowledge_ids=knowledge_ids,
                    mentioned_items=mentioned_items,
                    agent_id='builtin-smart-reasoning',
                )

                related_detail = ""
                if result.get('success'):
                    related_detail = result.get('data', {}).get('content', '')

                requirements_with_details.append({
                    'module': module,
                    'func_point': func_point,
                    'related_detail': related_detail,
                })

            yield send_event("progress", {
                "step": "retrieve",
                "status": "complete",
                "message": f"检索完成，共{len(requirements_with_details)}个功能点"
            })

            # 3. 构建批量请求
            yield send_event("progress", {
                "step": "build",
                "status": "start",
                "message": "构建AI请求..."
            })

            batch_items = []
            item_mapping = []

            for item in requirements_with_details:
                base_text = service._build_input_text(item)
                for j, prompt in enumerate(service.TEST_PROMPTS):
                    batch_items.append({'input_text': f"{base_text}\n{prompt}"})
                    item_mapping.append({
                        'module': item['module'],
                        'func_point': item['func_point'],
                        'test_type_index': j,
                    })

            yield send_event("progress", {
                "step": "build",
                "status": "complete",
                "message": f"构建完成，共{len(batch_items)}个请求",
                "data": {
                    "total_requests": len(batch_items),
                    "function_points": len(requirements_with_details),
                    "test_directions": len(service.TEST_PROMPTS)
                }
            })

            # 4. 预创建模块
            yield send_event("progress", {
                "step": "module",
                "status": "start",
                "message": "创建模块..."
            })

            module_names = set(m['module'] for m in item_mapping if m.get('module'))
            module_map = {}
            for name in module_names:
                module_map[name] = TestModule.objects.get_or_create(
                    version_id=version_id,
                    name=name,
                    defaults={'sort_order': 0}
                )[0]

            yield send_event("progress", {
                "step": "module",
                "status": "complete",
                "message": f"模块创建完成，共{len(module_map)}个模块"
            })

            # 5. 批量调用AI - 先推送每个请求的准备状态
            yield send_event("progress", {
                "step": "generate",
                "status": "start",
                "message": f"开始调用AI生成，共{len(batch_items)}个请求...",
                "data": {"total_requests": len(batch_items)}
            })

            # 推送每个请求的准备状态
            for i, mapping in enumerate(item_mapping):
                test_type = service.TEST_TYPE_NAMES[mapping['test_type_index']]
                yield send_event("progress", {
                    "step": "generate",
                    "status": "preparing",
                    "message": f"准备生成 [{i+1}/{len(batch_items)}]: {mapping['module']} - {mapping['func_point'][:20]}... ({test_type})",
                    "data": {"current": i + 1, "total": len(batch_items)}
                })

            total_start_time = time.time()
            ai_results = service.ai_client.generate_cases_batch(batch_items)
            total_elapsed = time.time() - total_start_time

            yield send_event("progress", {
                "step": "generate",
                "status": "complete",
                "message": f"AI生成完成，耗时{total_elapsed:.2f}秒",
                "data": {"elapsed": round(total_elapsed, 2)}
            })

            # 6. 处理结果 - 流式推送每个请求结果
            yield send_event("progress", {
                "step": "save",
                "status": "start",
                "message": "保存测试用例..."
            })

            total_created = 0
            total_errors = 0
            all_cases = []

            for i, (ai_result, mapping) in enumerate(zip(ai_results, item_mapping)):
                test_type = service.TEST_TYPE_NAMES[mapping['test_type_index']]

                # 推送当前保存进度
                yield send_event("progress", {
                    "step": "save",
                    "status": "processing",
                    "message": f"保存测试用例 [{i+1}/{len(ai_results)}]: {mapping['module']} - {mapping['func_point'][:20]}...",
                    "data": {"current": i + 1, "total": len(ai_results)}
                })

                request_info = {
                    "index": i + 1,
                    "module": mapping['module'],
                    "func_point": mapping['func_point'],
                    "test_type": test_type,
                }

                if ai_result.success and ai_result.result:
                    cases_data = ai_result.result if isinstance(ai_result.result, list) else [ai_result.result]
                    created_in_request = []

                    for case_data in cases_data:
                        try:
                            priority = service._parse_priority(case_data.get("priority"))
                            steps_text = service._parse_steps(case_data)
                            expected_result_text = service._parse_expected_result(case_data)
                            title = service._parse_title(case_data) or f"{module_name}-{mapping.get('func_point', '测试用例')}"
                            precondition = service._parse_precondition(case_data)

                            module_name = mapping.get('module', '')
                            module = module_map.get(module_name)

                            case = TestCase.objects.create(
                                title=title,
                                precondition=precondition,
                                priority=priority,
                                tags=case_data.get("tags", []),
                                requirement=f"{module_name}: {mapping.get('func_point', '')}",
                                version_id=version_id,
                                module=module,
                                created_by=user,
                                updated_by=user,
                                generation_source="ai_generated",
                                review_status="pending",
                                steps=steps_text,
                                expected_result=expected_result_text,
                            )

                            created_in_request.append({
                                'id': case.id,
                                'title': case.title,
                                'priority': case.priority,
                            })
                            total_created += 1
                            all_cases.append({
                                'id': case.id,
                                'title': case.title,
                                'module': module_name,
                                'priority': case.priority,
                            })

                        except Exception as e:
                            total_errors += 1

                    request_info["success"] = True
                    request_info["cases_count"] = len(created_in_request)
                    request_info["cases"] = created_in_request

                    # 推送单个请求结果
                    yield send_event("result", request_info)

                else:
                    request_info["success"] = False
                    request_info["error"] = ai_result.error or "生成失败"
                    request_info["cases_count"] = 0
                    request_info["cases"] = []
                    total_errors += 1

                    # 推送失败结果
                    yield send_event("result", request_info)

            yield send_event("progress", {
                "step": "save",
                "status": "complete",
                "message": f"保存完成，成功{total_created}条，失败{total_errors}条",
                "data": {"created": total_created, "errors": total_errors}
            })

            # 完成
            yield send_event("complete", {
                "success": True,
                "created_count": total_created,
                "error_count": total_errors,
                "total_requests": len(batch_items),
                "total_elapsed": round(total_elapsed, 2),
                "cases": all_cases,
                "session_id": session_id,
            })

        except ModelNotReadyError:
            logger.error("Model not ready error")
            yield send_event("error", {
                "error": "AI服务暂不可用，请稍后重试"
            })
        except AIServiceError as e:
            logger.error(f"AI service error: {e.message}, code: {e.code}")
            yield send_event("error", {
                "error": e.message,
                "code": e.code
            })
        except Exception as e:
            logger.error(f"Stream generation error: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            yield send_event("error", {
                "error": str(e)
            })

    return StreamingHttpResponse(
        generate_stream(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': request.META.get('HTTP_ORIGIN', '*'),
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
    )


@extend_schema(tags=['AI生成'])
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def ai_service_status(request):
    """获取AI服务状态"""
    from apps.testcase.clients.ai_client import AITestCaseClientSync

    try:
        client = AITestCaseClientSync()
        is_healthy = client.health_check()
        service_info = client.get_service_info()

        return Response({
            "success": True,
            "healthy": is_healthy,
            "service": service_info,
        })

    except AIServiceError as e:
        return Response({
            "success": False,
            "healthy": False,
            "error": e.message,
        })
    except Exception as e:
        logger.error(f"AI status check error: {e}")
        return Response({
            "success": False,
            "healthy": False,
            "error": "服务状态检查失败",
        })


@extend_schema(tags=['AI生成'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def cancel_ai_generation(request):
    """
    取消AI生成任务

    Request Body:
        - task_id: 任务ID（从SSE started事件获取）

    Returns:
        - success: 是否成功
    """
    from django.core.cache import cache

    task_id = request.data.get("task_id")
    if not task_id:
        return Response({
            "success": False,
            "error": "task_id不能为空"
        }, status=400)

    # 设置取消标志，有效期5分钟
    cache.set(f"ai_gen_cancel:{task_id}", True, timeout=300)

    logger.info(f"AI generation cancelled: task_id={task_id}")

    return Response({
        "success": True,
        "message": "取消请求已发送"
    })