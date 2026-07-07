# -*- coding: utf-8 -*-
"""
接口测试用例视图
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
from apps.apitest.models import ApiTestCase, ApiTestRun, ApiEnvironment
from apps.apitest.serializers import (
    ApiTestCaseSerializer,
    ApiTestCaseListSerializer,
    ApiTestRunSerializer,
    ApiTestRunListSerializer,
)
from apps.apitest.clients import ApiTestingClient
from apps.projects.models import ProjectMember

logger = logging.getLogger(__name__)


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
        user_project_ids = ProjectMember.objects.filter(
            user=self.request.user
        ).values_list('project_id', flat=True)

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
        origin = request.META.get('HTTP_ORIGIN', 'http://localhost:5173')

        def generate():
            step_results = []
            all_success = True
            run_list = []

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
                                run.result = 'error'
                                run.error_message = '未能获取接口执行列表'
                                run.end_time = timezone.now()
                                run.save()
                                return
                        elif event_type == "dependency":
                            # 获取到依赖分析结果（新格式）
                            dependency_data = event.get("data", {})
                            run_list = dependency_data.get("run_list", [])
                            logger.info(f"解析出的 run_list: {run_list}")
                            if not run_list:
                                yield f"data: {json.dumps({'type': 'error', 'data': {'message': '未能获取接口执行列表'}}, ensure_ascii=False)}\n\n"
                                run.result = 'error'
                                run.error_message = '未能获取接口执行列表'
                                run.end_time = timezone.now()
                                run.save()
                                return
                        elif event_type == "error":
                            yield line
                            run.result = 'error'
                            run.error_message = event.get("data", {}).get("message", "依赖分析失败")
                            run.end_time = timezone.now()
                            run.save()
                            return
                    except json.JSONDecodeError:
                        pass

            if not run_list:
                yield f"data: {json.dumps({'type': 'error', 'data': {'message': '依赖分析未返回执行列表'}}, ensure_ascii=False)}\n\n"
                run.result = 'error'
                run.error_message = '依赖分析未返回执行列表'
                run.end_time = timezone.now()
                run.save()
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
                            run.end_time = timezone.now()
                            total_ms = sum(
                                s.get("duration_ms", 0) for s in step_results
                            )
                            run.duration_ms = total_ms
                            run.save()

                            # 更新用例状态
                            test_case.status = 'passed' if all_success else 'failed'
                            test_case.save(update_fields=['status'])

                            # 发送包含完整执行结果的 report 事件
                            yield f"data: {json.dumps({'type': 'report', 'data': {'passed': all_success, 'result': run.result, 'duration_ms': total_ms, 'step_count': len(step_results)}}, ensure_ascii=False)}\n\n"

                        elif event_type == "error":
                            run.result = 'error'
                            run.error_message = event.get("data", {}).get("message", "")
                            run.end_time = timezone.now()
                            run.save()
                            yield line

                        else:
                            yield line

                    except json.JSONDecodeError:
                        yield line
                else:
                    yield line

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = origin
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
        origin = request.META.get('HTTP_ORIGIN', 'http://localhost:5173')

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
        response['Access-Control-Allow-Origin'] = origin
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
        if not ProjectMember.objects.filter(
            project_id=project_id,
            user=request.user
        ).exists():
            return Response({'error': '无权限访问该项目'}, status=403)

        client = ApiTestingClient()
        origin = request.META.get('HTTP_ORIGIN', 'http://localhost:5173')

        def generate():
            full_content = ""
            thinking_content = ""
            logger.info(f"开始从知识库生成测试用例，kb_id={knowledge_base_id}, project_id={project_id}")

            for line in client.generate_testcase_stream(
                kb_id=knowledge_base_id,
                knowledge_ids=knowledge_ids if knowledge_ids else None
            ):
                logger.info(f"收到原始行: {line[:100] if len(line) > 100 else line}")
                yield line

                # 收集完整内容用于存库
                if line.startswith("data: "):
                    try:
                        event_json = line[6:].strip()
                        event = json.loads(event_json)
                        event_type = event.get("type")
                        logger.info(f"收到事件: type={event_type}")

                        if event_type == "chunk":
                            chunk_content = event.get("data", {}).get("content", "")
                            full_content += chunk_content
                            logger.debug(f"chunk 内容长度: {len(chunk_content)}, 累计长度: {len(full_content)}")

                        elif event_type == "thinking":
                            think_content = event.get("data", {}).get("content", "")
                            thinking_content += think_content

                        elif event_type == "complete":
                            # chunk 内容优先；若为空则回退使用 thinking 内容
                            content_to_parse = full_content or thinking_content
                            logger.info(f"生成完成，chunk 长度: {len(full_content)}, thinking 长度: {len(thinking_content)}, 使用: {'chunk' if full_content else 'thinking'}")

                            if not content_to_parse:
                                logger.warning("生成内容为空")
                                yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'AI 未返回有效内容'}}, ensure_ascii=False)}\n\n"
                                continue

                            try:
                                test_cases_data = _parse_generated_cases(content_to_parse)
                                logger.info(f"解析到 {len(test_cases_data)} 个测试用例")
                                if test_cases_data:
                                    saved_ids = _save_generated_cases(
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

                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 解析失败: {e}")

        response = StreamingHttpResponse(
            generate(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'

        return response


def _parse_generated_cases(content: str) -> list:
    """解析 AI 生成的测试用例 JSON"""
    import re

    content = content.strip()
    logger.info(f"尝试解析生成内容，长度: {len(content)}, 预览: {content[:200]}...")

    if not content:
        logger.warning("生成内容为空")
        return []

    # 提取 markdown 代码块中的 JSON（优先匹配最后的代码块，避免 thinking 中的代码块干扰）
    json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', content)
    if json_blocks:
        content = json_blocks[-1].strip()
        logger.info(f"从 ```json 代码块中提取 JSON（共 {len(json_blocks)} 个块，取最后一个），长度: {len(content)}")
    else:
        plain_blocks = re.findall(r'```\s*([\s\S]*?)\s*```', content)
        if plain_blocks:
            content = plain_blocks[-1].strip()
            logger.info(f"从 ``` 代码块中提取 JSON（共 {len(plain_blocks)} 个块，取最后一个），长度: {len(content)}")

    # 如果内容不是以 { 或 [ 开头，尝试提取 JSON 数组
    if not content.startswith('{') and not content.startswith('['):
        # 找到最后一个 [ 和对应的 ] 来提取 JSON 数组（避免 thinking 中的误匹配）
        start = content.rfind('[')
        if start != -1:
            # 从最后一个 [ 开始，找到匹配的 ]
            bracket_count = 0
            end = -1
            for i in range(start, len(content)):
                if content[i] == '[':
                    bracket_count += 1
                elif content[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            if end > start:
                content = content[start:end]
                logger.info(f"提取 JSON 数组，长度: {len(content)}")
            else:
                # 尝试提取 JSON 对象
                start = content.rfind('{')
                if start != -1:
                    bracket_count = 0
                    end = -1
                    for i in range(start, len(content)):
                        if content[i] == '{':
                            bracket_count += 1
                        elif content[i] == '}':
                            bracket_count -= 1
                            if bracket_count == 0:
                                end = i + 1
                                break
                    if end > start:
                        content = content[start:end]
                        logger.info(f"提取 JSON 对象，长度: {len(content)}")

    try:
        cases = json.loads(content)
        if isinstance(cases, list):
            # 过滤掉非字典元素
            valid_cases = [c for c in cases if isinstance(c, dict)]
            if len(valid_cases) < len(cases):
                logger.warning(f"过滤了 {len(cases) - len(valid_cases)} 个非字典元素")
            logger.info(f"成功解析 {len(valid_cases)} 个测试用例")
            return valid_cases
        elif isinstance(cases, dict):
            logger.info("解析到单个测试用例对象，转换为列表")
            return [cases]
        logger.warning(f"解析结果不是列表或字典: {type(cases)}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}, 内容预览: {content[:500]}")
        return []


def _save_generated_cases(cases_data: list, project_id: int, user, knowledge_base_id: str) -> list:
    """保存生成的测试用例"""
    saved_ids = []
    failed_count = 0

    # 验证 project_id 对应的项目存在
    from apps.projects.models import Project
    try:
        Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error(f"项目不存在: project_id={project_id}")
        return []

    for case_data in cases_data:
        try:
            case_name = case_data.get("apiname") or case_data.get("name") or case_data.get("title") or "未命名用例"
            test_case = ApiTestCase.objects.create(
                project_id=project_id,
                name=case_name,
                precondition=case_data.get("precondition", ""),
                testpoint=case_data.get("testpoint") or case_data.get("test_point", ""),
                expectation=case_data.get("expectation") or case_data.get("expected", ""),
                priority=_parse_priority(case_data.get("priority")),
                test_data=case_data.get("test_data", {}),
                run_list=case_data.get("run_list", []),
                status='draft',
                knowledge_base_id=knowledge_base_id,
                source='ai_generated',
                created_by=user,
                updated_by=user
            )
            saved_ids.append(test_case.id)
            logger.info(f"保存用例成功: id={test_case.id}, name={case_name}")

        except Exception as e:
            failed_count += 1
            logger.error(f"保存用例失败: {case_data}, error: {e}")

    if failed_count > 0:
        logger.warning(f"保存用例完成，成功 {len(saved_ids)} 条，失败 {failed_count} 条")
    else:
        logger.info(f"保存用例完成，全部成功，共 {len(saved_ids)} 条")

    return saved_ids


def _parse_priority(priority_str: str) -> str:
    """解析优先级"""
    if not priority_str:
        return 'p2'

    priority = str(priority_str).lower()
    mapping = {
        'p0': 'p0', '最高': 'p0', '紧急': 'p0',
        'p1': 'p1', '高': 'p1', '重要': 'p1',
        'p2': 'p2', '中': 'p2', '一般': 'p2',
        'p3': 'p3', '低': 'p3', '次要': 'p3',
    }

    return mapping.get(priority, 'p2')


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
        user_project_ids = ProjectMember.objects.filter(
            user=self.request.user
        ).values_list('project_id', flat=True)

        queryset = queryset.filter(
            test_case__project_id__in=user_project_ids
        )

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ApiTestRunListSerializer
        return ApiTestRunSerializer
