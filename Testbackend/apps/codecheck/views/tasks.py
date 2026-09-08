# -*- coding: utf-8 -*-
"""
代码检查任务 视图（JWT 鉴权）

- trigger: 手动触发（基于 project_code）
- list: 任务列表
- retrieve: 任务详情（自动 sync 微服务）
- sync: 强制回写
"""
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound

from apps.users.authentication import JWTAuthentication
from apps.codecheck.models import CodeCheckTask
from apps.codecheck.serializers import (
    CodeCheckTaskListSerializer, CodeCheckTaskDetailSerializer,
)
from apps.codecheck.services.codecheck_service import (
    sync_task, trigger_task,
)
from apps.projects.models import Project

logger = logging.getLogger(__name__)


class CodeCheckTaskViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        qs = CodeCheckTask.objects.all().order_by("-created_at")
        project_id = request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
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
                case_source=case_source,
                project_code=project_code,
                test_case_file=data.get("test_case_file", ""),
                gate=gate,
                trigger_source="manual",
                user=request.user,
            )
        except ValueError as e:
            raise ValidationError(str(e))
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
