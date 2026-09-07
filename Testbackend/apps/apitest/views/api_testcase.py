# -*- coding: utf-8 -*-
"""
接口测试用例视图
"""

import json
import logging
import re
from collections import Counter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from django.utils import timezone

from apps.users.authentication import JWTAuthentication
from apps.apitest.models import ApiTestCase, ApiTestRun, ApiEnvironment
from apps.apitest.serializers import (
    ApiTestCaseSerializer,
    ApiTestCaseListSerializer,
    ApiTestRunSerializer,
    ApiTestRunListSerializer,
)
from apps.apitest.clients import ApiTestingClient
from apps.apitest.services import ApiTestPermissionService, parse_generated_cases, save_generated_cases
from apps.core.utils.cors import get_safe_cors_origin

logger = logging.getLogger(__name__)


# ==================== 生成内容级防循环（流式截断）辅助 ====================
# 与 generate_testcase.txt 提示词约束保持一致：单接口最多 8 条用例。
# 当模型在长文档上自我重复、为同一接口反复生成用例时，据此提前截断。
_APINAME_RE = re.compile(r'"apiname"\s*:\s*"([^"]*)"', re.DOTALL)
_MAX_CASES_PER_API = 8


def _find_duplicate_case_start(buffer):
    """检测模型输出是否陷入重复。

    同一个 apiname 出现次数超过 _MAX_CASES_PER_API（单接口用例数超出约束）即判定为
    循环，返回首个“溢出”用例对象的起点索引；否则返回 -1。
    """
    matches = list(_APINAME_RE.finditer(buffer))
    counts = Counter(m.group(1).strip().lower() for m in matches if m.group(1).strip())
    for apiname, cnt in counts.items():
        if cnt > _MAX_CASES_PER_API:
            occurrences = [m.start() for m in matches if m.group(1).strip().lower() == apiname]
            overflow = occurrences[_MAX_CASES_PER_API]  # 第 (MAX+1) 次出现
            case_start = buffer.rfind('{', 0, overflow)
            return case_start if case_start != -1 else overflow
    return -1


def _truncate_to_array(buffer_prefix):
    """将截取到重复用例之前的文本补成合法 JSON 数组结尾（[ ... ]）。"""
    s = buffer_prefix.rstrip()
    s = s.rstrip(',')
    s = s.rstrip()
    return s + "\n]"


class ApiTestCaseViewSet(viewsets.ModelViewSet):
    """
    接口测试用例管理

    list: 获取用例列表
    create: 创建用例
    retrieve: 获取用例详情
    update: 更新用例
    destroy: 删除用例
    execute: 执行用例（流式）
    runs: 获取执行记录
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取用户有权限的项目用例"""
        queryset = ApiTestCase.objects.select_related('project', 'created_by', 'updated_by')

        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # 只返回用户有权限的项目用例
        user_project_ids = ApiTestPermissionService.get_user_project_ids(self.request.user)

        return queryset.filter(project_id__in=user_project_ids)

    def get_serializer_class(self):
        if self.action == 'list':
            return ApiTestCaseListSerializer
        return ApiTestCaseSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        执行测试用例 - SSE 流式返回

        执行流程：
        1. 调用微服务 /dependency 获取 run_list（接口执行顺序）
        2. 调用微服务 /testcase/execute 执行测试

        请求参数:
            - environment_id: 执行环境 ID
        """
        test_case = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response({'error': '缺少 environment_id'}, status=400)

        try:
            environment = ApiEnvironment.objects.get(id=environment_id)
        except ApiEnvironment.DoesNotExist:
            return Response({'error': '环境不存在'}, status=404)

        # 检查环境是否属于同一项目
        if environment.project_id != test_case.project_id:
            return Response({'error': '环境与用例不属于同一项目'}, status=400)

        # 检查知识库ID
        if not test_case.knowledge_base_id:
            return Response({'error': '测试用例未关联知识库'}, status=400)

        # 创建执行记录
        run = ApiTestRun.objects.create(
            test_case=test_case,
            environment=environment,
            result='running',
            executed_by=request.user
        )

        client = ApiTestingClient()

        def generate():
            step_results = []
            all_success = True
            run_list = []

            def finalize_run(run_result, error_message=None, error_step=None):
                """统一收尾：更新执行记录并同步用例状态，避免统计/列表卡在旧值。

                status 仅由执行结果派生：pass→passed；fail/error→failed。
                所有 run 结束路径（依赖分析失败 / 执行出错 / SSE 异常中断）均经此收口。
                """
                # 幂等保护：report 已完成收尾（pass/fail）后若流异常再走此路径，跳过避免重复计数
                if run.result in ('pass', 'fail') and run.end_time:
                    return
                run.result = run_result
                if error_message is not None:
                    run.error_message = error_message
                if error_step is not None:
                    run.error_step = error_step
                if run.end_time is None:
                    run.end_time = timezone.now()
                run.save()
                test_case.status = 'passed' if run_result == 'pass' else 'failed'
                test_case.save(update_fields=['status'])

            try:
                # ==================== Step 1: 获取依赖关系 ====================
                yield f"data: {json.dumps({'type': 'step', 'data': {'message': '正在分析接口依赖关系...'}}, ensure_ascii=False)}\n\n"

                dependency_content = ""
                for line in client.get_dependency_stream(
                    case_id=str(test_case.id),
                    api_name=test_case.name,
                    precondition=test_case.precondition,
                    testpoint=test_case.testpoint,
                    expectation=test_case.expectation,
                    kb_id=test_case.knowledge_base_id
                ):
                    # 透传依赖分析的进度
                    if line.startswith("data: "):
                        try:
                            event = json.loads(line[6:].strip())
                            event_type = event.get("type")

                            if event_type == "chunk":
                                # 依赖分析的思考过程，透传给前端
                                yield line
                            elif event_type == "result":
                                # 获取到依赖分析结果（旧格式）
                                dependency_data = event.get("data", {})
                                logger.info(f"依赖分析结果: {json.dumps(dependency_data, ensure_ascii=False)[:500]}")
                                run_list = dependency_data.get("dependency", {}).get("run_list", [])
                                if not run_list:
                                    run_list = dependency_data.get("run_list", [])
                                logger.info(f"解析出的 run_list: {run_list}")
                                if run_list:
                                    yield f"data: {json.dumps({'type': 'dependency', 'data': {'run_list': run_list, 'message': f'分析完成，共 {len(run_list)} 个接口'}}, ensure_ascii=False)}\n\n"
                                else:
                                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': '未能获取接口执行列表'}}, ensure_ascii=False)}\n\n"
                                    finalize_run('error', '未能获取接口执行列表')
                                    return
                            elif event_type == "dependency":
                                # 获取到依赖分析结果（新格式）
                                dependency_data = event.get("data", {})
                                run_list = dependency_data.get("run_list", [])
                                logger.info(f"解析出的 run_list: {run_list}")
                                if not run_list:
                                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': '未能获取接口执行列表'}}, ensure_ascii=False)}\n\n"
                                    finalize_run('error', '未能获取接口执行列表')
                                    return
                            elif event_type == "error":
                                yield line
                                finalize_run('error', event.get("data", {}).get("message", "依赖分析失败"))
                                return
                        except json.JSONDecodeError:
                            pass

                if not run_list:
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': '依赖分析未返回执行列表'}}, ensure_ascii=False)}\n\n"
                    finalize_run('error', '依赖分析未返回执行列表')
                    return

                # ==================== Step 1.5: 数据填充 ====================
                # 依赖分析只负责编排（request_body 可为空壳），数据值由 fill 步骤填充。
                # 执行阶段不再内置 AI 预填充兜底，写接口缺参数时必须在执行前完成填充
                def _needs_fill(items):
                    for it in items:
                        if not isinstance(it, dict):
                            continue
                        if (it.get("method", "")).upper() in ("POST", "PUT", "DELETE", "PATCH") \
                                and not it.get("request_body"):
                            return True
                    return False

                if _needs_fill(run_list):
                    yield f"data: {json.dumps({'type': 'step', 'data': {'message': '正在填充测试数据...'}}, ensure_ascii=False)}\n\n"

                    for line in client.fill_testdata_stream(
                        case_id=str(test_case.id),
                        api_name=test_case.name,
                        precondition=test_case.precondition,
                        testpoint=test_case.testpoint,
                        expectation=test_case.expectation,
                        dependency={"case_id": test_case.id, "run_list": run_list},
                        test_data=test_case.test_data or {},
                        kb_id=test_case.knowledge_base_id,
                        base_url=environment.base_url
                    ):
                        if not line.startswith("data: "):
                            continue
                        try:
                            event = json.loads(line[6:].strip())
                        except json.JSONDecodeError:
                            continue

                        if event.get("type") == "chunk":
                            # 数据填充的思考过程透传给前端
                            yield line
                        elif event.get("type") == "result":
                            filled = event.get("data", {}).get("filled_data", {})
                            filled_run_list = []
                            if isinstance(filled, dict):
                                filled_run_list = filled.get("run_list", [])
                            elif isinstance(filled, list):
                                filled_run_list = filled
                            if filled_run_list:
                                run_list = filled_run_list
                                yield f"data: {json.dumps({'type': 'fill', 'data': {'run_list': run_list, 'message': f'数据填充完成，共 {len(run_list)} 个接口'}}, ensure_ascii=False)}\n\n"
                            else:
                                yield f"data: {json.dumps({'type': 'error', 'data': {'message': '数据填充未返回有效结果'}}, ensure_ascii=False)}\n\n"
                                finalize_run('error', '数据填充未返回有效结果')
                                return
                        elif event.get("type") == "error":
                            yield line
                            finalize_run('error', event.get("data", {}).get("message", "数据填充失败"))
                            return

                # ==================== Step 2: 执行测试用例 ====================
                logger.info(f"开始执行测试用例, run_list={run_list}, base_url={environment.base_url}")
                yield f"data: {json.dumps({'type': 'step', 'data': {'message': f'开始执行，共 {len(run_list)} 个接口...'}}, ensure_ascii=False)}\n\n"

                for line in client.execute_testcase_stream(
                    case_id=str(test_case.id),
                    api_name=test_case.name,
                    precondition=test_case.precondition,
                    testpoint=test_case.testpoint,
                    expectation=test_case.expectation,
                    run_list=run_list,
                    test_data=test_case.test_data or {},
                    kb_id=test_case.knowledge_base_id,
                    base_url=environment.base_url
                ):
                    # 解析 SSE 事件，收集执行结果
                    if line.startswith("data: "):
                        try:
                            event = json.loads(line[6:].strip())
                            event_type = event.get("type")

                            if event_type == "result":
                                step_results.append(event.get("data", {}))
                                if not event.get("data", {}).get("success", False):
                                    all_success = False
                                yield line

                            elif event_type == "report":
                                # 执行完成，更新记录
                                run.step_results = step_results
                                run.result = 'pass' if all_success else 'fail'
                                total_ms = sum(
                                    s.get("duration_ms", 0) for s in step_results
                                )
                                run.duration_ms = total_ms
                                if run.end_time is None:
                                    run.end_time = timezone.now()
                                run.save()

                                # 更新用例状态（由执行结果派生，禁止手动写入）
                                test_case.status = 'passed' if all_success else 'failed'
                                test_case.save(update_fields=['status'])


                                # 发送包含完整执行结果的 report 事件
                                success_count = sum(1 for s in step_results if s.get("success", False))
                                yield f"data: {json.dumps({'type': 'report', 'data': {'passed': all_success, 'success': success_count, 'total': len(step_results), 'result': run.result, 'duration_ms': total_ms, 'step_count': len(step_results)}}, ensure_ascii=False)}\n\n"

                            elif event_type == "error":
                                finalize_run('error', event.get("data", {}).get("message", ""))
                                yield line

                            else:
                                yield line

                        except json.JSONDecodeError:
                            yield line
                    else:
                        yield line
            except Exception as exc:
                # SSE 连接中断 / 微服务异常：确保 run 与用例状态不被永久卡在 running/旧值
                logger.error(f"用例执行流异常中断: {exc}", exc_info=True)
                try:
                    finalize_run('error', f'执行流异常中断: {str(exc)[:200]}')
                except Exception:
                    pass
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': '执行流异常中断'}}, ensure_ascii=False)}\n\n"
                return

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = get_safe_cors_origin(request)
        response['Access-Control-Allow-Credentials'] = 'true'

        return response

    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """获取用例的执行记录"""
        test_case = self.get_object()

        runs = ApiTestRun.objects.filter(
            test_case=test_case
        ).select_related('environment', 'executed_by')[:20]

        serializer = ApiTestRunListSerializer(runs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        校验测试用例执行结果 - SSE 流式返回

        请求参数:
            - execution_results: 执行结果列表（由前端传入执行结果）
        """
        test_case = self.get_object()
        execution_results = request.data.get('execution_results', [])

        if not execution_results:
            return Response({'error': '缺少 execution_results'}, status=400)

        if not test_case.knowledge_base_id:
            return Response({'error': '测试用例未关联知识库'}, status=400)

        client = ApiTestingClient()

        def generate():
            for line in client.validate_testcase_stream(
                case_id=str(test_case.id),
                api_name=test_case.name,
                precondition=test_case.precondition,
                testpoint=test_case.testpoint,
                expectation=test_case.expectation,
                execution_results=execution_results,
                kb_id=test_case.knowledge_base_id
            ):
                yield line

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = get_safe_cors_origin(request)
        response['Access-Control-Allow-Credentials'] = 'true'

        return response

    @action(detail=False, methods=['post'])
    def generate_from_kb(self, request):
        """
        从知识库生成测试用例 - 流式

        请求参数:
            - knowledge_base_id: 知识库 ID
            - project_id: 项目 ID（用于保存）
            - knowledge_ids: 知识文档 ID 列表（可选）
        """
        knowledge_base_id = request.data.get('knowledge_base_id')
        project_id = request.data.get('project_id')
        knowledge_ids = request.data.get('knowledge_ids', [])

        if not knowledge_base_id:
            return Response({'error': '缺少 knowledge_base_id'}, status=400)

        if not project_id:
            return Response({'error': '缺少 project_id'}, status=400)

        # 检查用户权限
        if not ApiTestPermissionService.user_is_project_member(request.user, project_id):
            return Response({'error': '无权限访问该项目'}, status=403)

        client = ApiTestingClient()

        def generate():
            full_content = ""
            thinking_content = ""
            loop_detected = False
            logger.info(f"开始从知识库生成测试用例，kb_id={knowledge_base_id}, project_id={project_id}")

            stream = client.generate_testcase_stream(
                kb_id=knowledge_base_id,
                knowledge_ids=knowledge_ids if knowledge_ids else None
            )
            try:
                for line in stream:
                    logger.info(f"收到原始行: {line[:100] if len(line) > 100 else line}")

                    # 解析 SSE 事件（内容级防循环 + 收尾保存）
                    parsed = None
                    if line.startswith("data: "):
                        try:
                            parsed = json.loads(line[6:].strip())
                        except json.JSONDecodeError:
                            parsed = None
                    event_type = parsed.get("type") if parsed else None

                    if event_type == "chunk":
                        if loop_detected:
                            # 已检测循环：丢弃后续 chunk，不再转发，避免前端/内容继续重复
                            continue
                        chunk_content = parsed.get("data", {}).get("content", "")
                        # 预判：追加本 chunk 后若出现重复用例（单接口超量），则截断并提前收尾
                        probe = full_content + chunk_content
                        dup_start = _find_duplicate_case_start(probe)
                        if dup_start >= 0:
                            loop_detected = True
                            full_content = _truncate_to_array(probe[:dup_start])
                            logger.warning("检测到生成内容循环（重复用例），已自动截断并提前结束")
                            break
                        full_content += chunk_content
                        yield line
                        continue

                    elif event_type == "thinking":
                        # 思考过程照常转发（不参与存库内容）
                        yield line
                        thinking_content += parsed.get("data", {}).get("content", "")
                        continue

                    elif event_type == "complete":
                        # 仅转发，真正收尾统一在循环结束后处理，避免重复保存
                        yield line
                        continue

                    else:
                        # session / reference / error 等事件原样转发
                        yield line
            finally:
                # 释放上游 SSE 流（含循环提前 break 的情况）
                try:
                    stream.close()
                except Exception:
                    pass

            # ==================== 统一收尾：只保存一次 ====================
            content_to_parse = full_content or thinking_content
            logger.info(f"生成收尾，loop_detected={loop_detected}, chunk 长度: {len(full_content)}, thinking 长度: {len(thinking_content)}")

            if not content_to_parse:
                logger.warning("生成内容为空")
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'AI 未返回有效内容'}}, ensure_ascii=False)}\n\n"
            else:
                try:
                    test_cases_data = parse_generated_cases(content_to_parse)
                    logger.info(f"解析到 {len(test_cases_data)} 个测试用例")
                    if test_cases_data:
                        saved_ids = save_generated_cases(
                            test_cases_data,
                            project_id,
                            request.user,
                            knowledge_base_id
                        )
                        logger.info(f"保存完成，saved_ids: {saved_ids}")
                        yield f"data: {json.dumps({'type': 'saved', 'data': {'count': len(saved_ids), 'ids': saved_ids}}, ensure_ascii=False)}\n\n"
                    else:
                        logger.warning(f"未解析到有效用例，内容预览: {content_to_parse[:500]}")
                        yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'AI 返回内容无法解析为测试用例', 'detail': content_to_parse[:300]}}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.error(f"保存生成的用例失败: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': f'保存用例失败: {str(e)}'}}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = get_safe_cors_origin(request)
        response['Access-Control-Allow-Credentials'] = 'true'

        return response


class ApiTestRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    接口测试执行记录管理

    list: 获取执行记录列表
    retrieve: 获取执行记录详情
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取用户有权限的执行记录"""
        queryset = ApiTestRun.objects.select_related(
            'test_case', 'environment', 'executed_by'
        )

        test_case_id = self.request.query_params.get('test_case')
        if test_case_id:
            queryset = queryset.filter(test_case_id=test_case_id)

        result = self.request.query_params.get('result')
        if result:
            queryset = queryset.filter(result=result)

        # 只返回用户有权限的项目执行记录
        user_project_ids = ApiTestPermissionService.get_user_project_ids(self.request.user)

        queryset = queryset.filter(
            test_case__project_id__in=user_project_ids
        )

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ApiTestRunListSerializer
        return ApiTestRunSerializer
