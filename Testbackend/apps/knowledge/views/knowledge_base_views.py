"""
知识库管理视图

视图层只负责：
1. 接收请求参数
2. 调用 Service 层处理业务逻辑
3. 返回响应
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.users.authentication import JWTAuthentication
from apps.core.response import StandardResponse
from apps.knowledge.services import KnowledgeBaseService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_knowledge_bases_view(request):
    """获取知识库列表"""
    result = KnowledgeBaseService.list_knowledge_bases()
    if result.get('success'):
        return StandardResponse(data=result.get('data', []), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_knowledge_base_view(request):
    """创建知识库"""
    result = KnowledgeBaseService.create_knowledge_base(request.data)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='创建成功')
    return StandardResponse(message=result.get('error', '创建失败'), code=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_knowledge_base_view(request, kb_id):
    """获取知识库详情"""
    result = KnowledgeBaseService.get_knowledge_base(kb_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=500)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_knowledge_base_view(request, kb_id):
    """更新知识库"""
    result = KnowledgeBaseService.update_knowledge_base(kb_id, request.data)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='更新成功')
    return StandardResponse(message=result.get('error', '更新失败'), code=500)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_knowledge_base_view(request, kb_id):
    """删除知识库"""
    result = KnowledgeBaseService.delete_knowledge_base(kb_id)
    if result.get('success'):
        return StandardResponse(message='删除成功')
    return StandardResponse(message=result.get('error', '删除失败'), code=500)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def copy_knowledge_base_view(request):
    """复制知识库"""
    source_id = request.data.get('source_id')
    name = request.data.get('name')
    result = KnowledgeBaseService.copy_knowledge_base(source_id, name)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='复制任务已创建')
    return StandardResponse(message=result.get('error', '复制失败'), code=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_copy_progress_view(request, task_id):
    """获取复制进度"""
    result = KnowledgeBaseService.get_copy_progress(task_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=500)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def pin_knowledge_base_view(request, kb_id):
    """置顶/取消置顶知识库"""
    result = KnowledgeBaseService.pin_knowledge_base(kb_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='操作成功')
    return StandardResponse(message=result.get('error', '操作失败'), code=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def hybrid_search_view(request, kb_id):
    """混合搜索（向量+关键词）"""
    query_text = request.query_params.get('query_text')

    kwargs = {}
    param_mappings = {
        'vector_threshold': float,
        'keyword_threshold': float,
        'match_count': int,
    }
    bool_params = ['disable_keywords_match', 'disable_vector_match']

    for param, converter in param_mappings.items():
        value = request.query_params.get(param)
        if value:
            kwargs[param] = converter(value)

    for param in bool_params:
        value = request.query_params.get(param)
        if value:
            kwargs[param] = value.lower() == 'true'

    result = KnowledgeBaseService.hybrid_search(kb_id, query_text, **kwargs)
    if result.get('success'):
        return StandardResponse(data=result.get('data', []), message='搜索成功')
    return StandardResponse(message=result.get('error', '搜索失败'), code=500)
