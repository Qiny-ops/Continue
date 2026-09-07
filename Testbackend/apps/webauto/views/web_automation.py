# -*- coding: utf-8 -*-
"""
Web 自动化用例视图

暴露给前端的 SSE 端点，调用 web-automation-service 微服务并透传流式事件，
同时记录执行历史（WebAutomationRun）。
"""

import json
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from django.utils import timezone

from apps.users.authentication import JWTAuthentication
from apps.testcase.models import TestCase
from apps.apitest.models import ApiEnvironment
from apps.webauto.models import WebAutomationRun
from apps.webauto.serializers import (
    WebAutomationRunSerializer,
    WebAutomationRunListSerializer,
)
from apps.webauto.clients import WebAutomationClient
from apps.core.utils.cors import get_safe_cors_origin

logger = logging.getLogger(__name__)


class WebAutomationViewSet(viewsets.ViewSet):
    """
    Web 自动化用例执行

    execute: 执行用例（SSE 流式，可传 case_id 复用功能用例 或 内联 testcase）
    plan:    规划 action_list（SSE 流式，预览/编辑）
    runs:    获取执行记录列表
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # ------------------------- 工具 -------------------------
    def _resolve_testcase(self, request):
        """从 case_id 或内联 testcase 解析出 (testcase_dict, title)。

        返回 (testcase, title, test_case_obj_or_None)
        """
        case_id = request.data.get('case_id')
        test_case = None
        if case_id:
            try:
                test_case = TestCase.objects.get(id=case_id)
            except TestCase.DoesNotExist:
                raise ValueError('用例不存在')
            testcase = {
                'precondition': test_case.precondition or '',
                'steps': test_case.steps or '',
                'expected_result': test_case.expected_result or '',
            }
            title = test_case.title or ''
        else:
            raw = request.data.get('testcase') or {}
            testcase = {
                'precondition': raw.get('precondition', '') or '',
                'steps': raw.get('steps', '') or '',
                'expected_result': raw.get('expected_result', '') or '',
            }
            title = raw.get('title', '') or ''
        return testcase, title, test_case

    def _resolve_start_url(self, request):
        """解析起始 URL：优先用显式 start_url，否则用所选「环境管理」环境的 base_url。

        返回 (start_url, environment_id)
        """
        start_url = request.data.get('start_url') or ''
        environment_id = request.data.get('environment_id') or None
        if not start_url and environment_id:
            try:
                env = ApiEnvironment.objects.get(id=environment_id)
                start_url = env.base_url or ''
            except ApiEnvironment.DoesNotExist:
                raise ValueError('所选环境不存在')
        return start_url, environment_id

    # ------------------------- 执行 -------------------------
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        执行 Web 自动化用例 - SSE 流式返回

        请求参数:
            - case_id:          功能用例 ID（可选，复用 precondition/steps/expected_result）
            - testcase:         内联用例（可选，与 case_id 二选一）
            - environment_id:   环境管理中的环境 ID（可选，自动取该环境 base_url 作为起始 URL）
            - start_url:        测试起始 URL（可选；缺省时由 environment_id 反解）
            - action_list:      预编排动作（可选；不传则走 agentic 看页面闭环）
            - site_hint:        站点提示
            - kb_id:            Web 站点知识库 ID（可选）
        """
        try:
            testcase, title, test_case = self._resolve_testcase(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_url, environment_id = self._resolve_start_url(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if not start_url:
            return Response(
                {'error': '缺少起始 URL：请选择环境或填写起始 URL'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action_list = request.data.get('action_list') or None
        site_hint = request.data.get('site_hint', '') or ''
        kb_id = request.data.get('kb_id', '') or ''

        # 创建执行记录
        run = WebAutomationRun.objects.create(
            test_case=test_case,
            case_title=title,
            start_url=start_url,
            environment_id=environment_id,
            result='running',
            executed_by=request.user,
        )

        client = WebAutomationClient()

        def generate():
            step_results = []
            run_finalized = {'done': False}

            def finalize_run(run_result, error_message=None):
                if run_finalized['done']:
                    return
                run_finalized['done'] = True
                run.result = run_result
                if error_message is not None:
                    run.error_message = error_message
                if run.end_time is None:
                    run.end_time = timezone.now()
                run.save()

            try:
                for line in client.execute_stream(
                    testcase=testcase,
                    start_url=start_url,
                    action_list=action_list,
                    site_hint=site_hint,
                    kb_id=kb_id,
                ):
                    if not line.startswith("data: "):
                        yield line
                        continue
                    try:
                        event = json.loads(line[6:].strip())
                    except json.JSONDecodeError:
                        yield line
                        continue

                    event_type = event.get("type")

                    if event_type == "step":
                        data = event.get("data", {})
                        step_results.append(data)
                        if not data.get("success", False):
                            pass  # 由最终 report 判定整体结果
                        yield line

                    elif event_type == "report":
                        # 上游给出结论，更新记录并发送聚合 report
                        rdata = event.get("data", {})
                        passed = rdata.get("passed")
                        if passed is None:
                            passed = all(s.get("success", False) for s in step_results)
                        run.result = 'pass' if passed else 'fail'
                        run.step_results = step_results
                        run.duration_ms = sum(s.get("duration_ms", 0) for s in step_results)
                        if run.end_time is None:
                            run.end_time = timezone.now()
                        run.save()
                        run_finalized['done'] = True
                        success_count = sum(1 for s in step_results if s.get("success", False))
                        yield f"data: {json.dumps({'type': 'report', 'data': {'passed': passed, 'success': success_count, 'total': len(step_results), 'result': run.result, 'duration_ms': run.duration_ms, 'step_count': len(step_results)}}, ensure_ascii=False)}\n\n"

                    elif event_type == "error":
                        run.error_message = event.get("data", {}).get("message", "")
                        finalize_run('error', run.error_message)
                        yield line

                    else:
                        # snapshot / plan_chunk / repair / start 等事件原样透传
                        yield line
            except Exception as exc:
                logger.error(f"Web 自动化执行流异常中断: {exc}", exc_info=True)
                try:
                    finalize_run('error', f'执行流异常中断: {str(exc)[:200]}')
                except Exception:
                    pass
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': '执行流异常中断'}}, ensure_ascii=False)}\n\n"
            finally:
                if not run_finalized['done']:
                    # 流异常结束未收到 report/error：以已收集步骤判定
                    passed = all(s.get("success", False) for s in step_results) if step_results else False
                    finalize_run('pass' if passed else 'fail')

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = get_safe_cors_origin(request)
        response['Access-Control-Allow-Credentials'] = 'true'
        return response

    # ------------------------- 规划预览 -------------------------
    @action(detail=False, methods=['post'])
    def plan(self, request):
        """
        规划 action_list - SSE 流式返回（预览/编辑用，不执行）

        请求参数同 execute 的 case_id / testcase / environment_id / start_url / site_hint / kb_id。
        """
        try:
            testcase, _title, _tc = self._resolve_testcase(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_url, _env_id = self._resolve_start_url(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if not start_url:
            return Response(
                {'error': '缺少起始 URL：请选择环境或填写起始 URL'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        site_hint = request.data.get('site_hint', '') or ''
        kb_id = request.data.get('kb_id', '') or ''

        client = WebAutomationClient()

        def generate():
            for line in client.plan_stream(
                testcase=testcase,
                start_url=start_url,
                site_hint=site_hint,
                kb_id=kb_id,
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

    # ------------------------- 执行记录 -------------------------
    @action(detail=False, methods=['get'])
    def runs(self, request):
        """获取 Web 自动化执行记录列表"""
        queryset = WebAutomationRun.objects.select_related('test_case', 'executed_by')
        test_case_id = request.query_params.get('test_case')
        if test_case_id:
            queryset = queryset.filter(test_case_id=test_case_id)
        result = request.query_params.get('result')
        if result:
            queryset = queryset.filter(result=result)
        queryset = queryset[:50]
        serializer = WebAutomationRunListSerializer(queryset, many=True)
        return Response(serializer.data)
