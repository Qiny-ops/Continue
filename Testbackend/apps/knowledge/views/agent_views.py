"""
Agent 视图

提供 Agent 对话和需求提炼的 HTTP 接口。
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.users.authentication import JWTAuthentication
from apps.core.response import StandardResponse
from apps.knowledge.services import AgentService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_session_view(request):
    """
    创建 Agent 会话

    请求体:
    {
        "knowledge_base_id": "知识库ID"
    }

    返回:
    {
        "code": 200,
        "message": "创建成功",
        "data": {"session_id": "会话ID"}
    }
    """
    knowledge_base_id = request.data.get('knowledge_base_id')
    if not knowledge_base_id:
        return StandardResponse(message='知识库 ID 不能为空', code=400)

    result = AgentService.create_session(knowledge_base_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='创建成功')
    return StandardResponse(message=result.get('error', '创建失败'), code=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def agent_chat_view(request, session_id):
    """
    Agent 对话

    请求体:
    {
        "query": "查询内容",
        "knowledge_base_ids": ["知识库ID1", "知识库ID2"],
        "knowledge_ids": ["文件ID1", "文件ID2"],
        "agent_id": "builtin-smart-reasoning",
        "web_search_enabled": false,
        "temperature": 0.3,
        "max_tokens": 4096,
        "kb_name_map": {"kb_id": "名称"},
        "file_name_map": {"file_id": "名称"}
    }

    返回:
    {
        "code": 200,
        "message": "操作成功",
        "data": {"content": "回答内容"}
    }
    """
    query = request.data.get('query')
    knowledge_base_ids = request.data.get('knowledge_base_ids', [])
    knowledge_ids = request.data.get('knowledge_ids', [])

    if not query:
        return StandardResponse(message='查询内容不能为空', code=400)

    result = AgentService.agent_chat(
        session_id=session_id,
        query=query,
        knowledge_base_ids=knowledge_base_ids,
        knowledge_ids=knowledge_ids,
        agent_id=request.data.get('agent_id', 'builtin-smart-reasoning'),
        web_search_enabled=request.data.get('web_search_enabled', False),
        temperature=float(request.data.get('temperature', 0.3)),
        max_tokens=int(request.data.get('max_tokens', 4096)),
        kb_name_map=request.data.get('kb_name_map'),
        file_name_map=request.data.get('file_name_map'),
    )

    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='操作成功')
    return StandardResponse(message=result.get('error', '操作失败'), code=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def extract_requirements_view(request):
    """
    需求提炼（一站式接口）

    如果未提供 session_id，会自动创建会话。

    请求体:
    {
        "query": "提问内容",
        "knowledge_base_ids": ["知识库ID1"],
        "knowledge_ids": ["文件ID1"],
        "session_id": "会话ID（可选）",
        "agent_id": "builtin-smart-reasoning",
        "web_search_enabled": false,
        "temperature": 0.3,
        "max_tokens": 4096,
        "kb_name_map": {"kb_id": "名称"},
        "file_name_map": {"file_id": "名称"}
    }

    返回:
    {
        "code": 200,
        "message": "提炼成功",
        "data": {
            "content": "提炼结果",
            "session_id": "会话ID"
        }
    }
    """
    query = request.data.get('query')
    knowledge_base_ids = request.data.get('knowledge_base_ids', [])
    knowledge_ids = request.data.get('knowledge_ids', [])

    if not query:
        return StandardResponse(message='查询内容不能为空', code=400)
    if not knowledge_base_ids:
        return StandardResponse(message='至少需要提供一个知识库 ID', code=400)

    result = AgentService.extract_requirements(
        query=query,
        knowledge_base_ids=knowledge_base_ids,
        knowledge_ids=knowledge_ids,
        session_id=request.data.get('session_id'),
        agent_id=request.data.get('agent_id', 'builtin-smart-reasoning'),
        web_search_enabled=request.data.get('web_search_enabled', False),
        temperature=float(request.data.get('temperature', 0.3)),
        max_tokens=int(request.data.get('max_tokens', 4096)),
        kb_name_map=request.data.get('kb_name_map'),
        file_name_map=request.data.get('file_name_map'),
    )

    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='提炼成功')
    return StandardResponse(message=result.get('error', '提炼失败'), code=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def generate_test_cases_from_knowledge_view(request):
    """
    从知识库生成测试用例（一站式接口）

    流程：
    1. 自动从知识库文件中提炼需求
    2. 将提炼结果调用 AI 测试用例生成微服务
    3. 实时将生成的测试用例写入数据库

    请求体:
    {
        "knowledge_base_ids": ["知识库ID1"],
        "knowledge_ids": ["文件ID1"],
        "version_id": "版本ID（必填）"
    }

    返回:
    {
        "code": 200,
        "message": "生成成功",
        "data": {
            "requirements": [...],      # 提炼的功能点
            "created_count": 10,        # 创建的用例数量
            "error_count": 0,           # 失败数量
            "session_id": "会话ID",
            "errors": []
        }
    }
    """
    from apps.testcase.services.ai_generation_service import AIGenerationService

    knowledge_base_ids = request.data.get('knowledge_base_ids', [])
    knowledge_ids = request.data.get('knowledge_ids', [])
    version_id = request.data.get('version_id')

    if not knowledge_base_ids:
        return StandardResponse(message='至少需要提供一个知识库 ID', code=400)
    if not version_id:
        return StandardResponse(message='version_id 不能为空', code=400)

    # 使用新的AIGenerationService
    service = AIGenerationService()
    result = service.generate_from_knowledge(
        knowledge_base_ids=knowledge_base_ids,
        knowledge_ids=knowledge_ids,
        version_id=version_id,
        user=request.user,
    )

    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='生成成功')
    return StandardResponse(message=result.get('error', '生成失败'), code=500)
