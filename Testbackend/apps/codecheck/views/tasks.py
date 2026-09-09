# -*- coding: utf-8 -*-
"""
代码检查任务 视图（JWT 鉴权）

- trigger: 手动触发（基于 project_code）
- list: 任务列表
- retrieve: 任务详情（自动 sync 微服务）
- sync: 强制回写
"""
import logging

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound

from django.db.models import Q

from apps.users.authentication import JWTAuthentication
from apps.codecheck.models import CodeCheckTask
from apps.codecheck.serializers import (
    CodeCheckTaskListSerializer, CodeCheckTaskDetailSerializer,
)
from apps.codecheck.services.codecheck_service import (
    sync_task, trigger_task,
)
from apps.codecheck.services.report_html import build_audit_report_html
from apps.projects.models import Project

logger = logging.getLogger(__name__)


class CodeCheckTaskViewSet(viewsets.GenericViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        任务列表

        支持：project / project_code、status、risk_level、conclusion、search 过滤
        传 page / page_size 时返回分页结构 {count, results}，否则返回数组（兼容旧调用）
        """
        qs = CodeCheckTask.objects.all().order_by("-created_at")

        project_id = request.query_params.get("project")
        project_code = request.query_params.get("project_code")
        if project_id:
            qs = qs.filter(project_id=project_id)
        if project_code:
            qs = qs.filter(project__code=project_code)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        risk_level = request.query_params.get("risk_level")
        if risk_level:
            qs = qs.filter(risk_level=risk_level)

        conclusion = request.query_params.get("conclusion")
        if conclusion:
            qs = qs.filter(conclusion=conclusion)

        keyword = (request.query_params.get("search") or "").strip()
        if keyword:
            qs = qs.filter(
                Q(repository_url__icontains=keyword)
                | Q(branch__icontains=keyword)
                | Q(commit_sha__icontains=keyword)
                | Q(project_name__icontains=keyword)
            )

        if request.query_params.get("page") or request.query_params.get("page_size"):
            page = self.paginate_queryset(qs)
            if page is not None:
                return self.get_paginated_response(
                    CodeCheckTaskListSerializer(page, many=True).data
                )
        return Response(CodeCheckTaskListSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        try:
            task = CodeCheckTask.objects.get(pk=pk)
        except CodeCheckTask.DoesNotExist:
            raise NotFound("任务不存在")
        if task.status in ("running", "pending"):
            sync_task(task)
        return Response(CodeCheckTaskDetailSerializer(task).data)

    def create(self, request):
        data = request.data or {}
        project_code = data.get("project_code", "").strip()
        if not project_code:
            raise ValidationError("project_code 必填")
        try:
            project = Project.objects.get(code=project_code)
        except Project.DoesNotExist:
            raise NotFound(f"项目不存在: {project_code}")

        case_source = data.get("case_source", "platform")
        if case_source not in ("platform", "inline", "file"):
            raise ValidationError("case_source 仅支持 platform/inline/file")

        trigger_source = data.get("trigger_source", "manual").strip() or "manual"
        if trigger_source not in ("manual", "webhook"):
            raise ValidationError("trigger_source 仅支持 manual/webhook")

        gate = data.get("gate")
        if isinstance(gate, dict) and gate.get("provider"):
            if gate["provider"] not in ("github", "gitlab"):
                raise ValidationError("gate.provider 仅支持 github/gitlab")
            for k in ("repo_ref", "commit_sha"):
                if not gate.get(k):
                    raise ValidationError(f"gate.{k} 必填")

        try:
            task = trigger_task(
                project=project,
                repository_url=data.get("repository_url", "").strip(),
                branch=data.get("branch", ""),
                commit_sha=data.get("commit_sha", ""),
                base_sha=data.get("base_sha", ""),
                case_source=case_source,
                project_code=project_code,
                test_case_file=data.get("test_case_file", ""),
                inline_test_cases=data.get("test_cases") or [],
                gate=gate,
                trigger_source=trigger_source,
                user=request.user,
            )
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            # AiCheckServiceError 等也归一为 400，避免冒泡 500
            raise ValidationError(f"触发代码检查失败: {e}")
        return Response(
            CodeCheckTaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        try:
            task = CodeCheckTask.objects.get(pk=pk)
        except CodeCheckTask.DoesNotExist:
            raise NotFound("任务不存在")
        sync_task(task)
        return Response(CodeCheckTaskDetailSerializer(task).data)

    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request, pk=None):
        """
        导出「自包含 HTML 审计报告」

        返回一份 CSS 全部内联、不依赖任何外部资源的 HTML 文件，
        可直接双击在浏览器打开、脱离平台转发 / 归档。
        """
        try:
            task = CodeCheckTask.objects.get(pk=pk)
        except CodeCheckTask.DoesNotExist:
            raise NotFound("任务不存在")
        # 生成报告前确保拉回最新结果（运行中/等待中的任务）
        if task.status in ("running", "pending"):
            try:
                sync_task(task)
            except Exception:
                pass
        html = build_audit_report_html(task)
        filename = f"ACR-{task.id:04d}.html"
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
        )
        return response
