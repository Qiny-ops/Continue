"""
知识文档管理视图

视图层只负责：
1. 接收请求参数
2. 调用 Service 层处理业务逻辑
3. 返回响应
"""

import logging
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.authentication import JWTAuthentication
from apps.core.response import StandardResponse
from apps.knowledge.services import KnowledgeService
from apps.knowledge.views.knowledge_base_views import _check_kb_project_permission, _check_kb_permission_by_knowledge

logger = logging.getLogger(__name__)

# 允许上传的文件扩展名白名单
ALLOWED_FILE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg',
    '.py', '.js', '.java', '.go', '.rs', '.ts', '.tsx', '.jsx',
    '.yaml', '.yml', '.toml', '.ini', '.cfg',
}
# 文件大小上限：50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def list_knowledge_view(request, kb_id):
    """获取知识库下的知识列表"""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    tag_id = request.query_params.get('tag_id')

    result = KnowledgeService.list_knowledge(kb_id, page, page_size, tag_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', []), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=result.get('http_status', 500))


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def upload_file_knowledge_view(request, kb_id):
    """上传文件知识"""
    _check_kb_project_permission(request, kb_id)
    file_obj = request.FILES.get('file')
    if not file_obj:
        return StandardResponse(message='文件不能为空', code=400)

    # 文件扩展名白名单校验
    file_name = file_obj.name
    ext = '.' + file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else ''
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return StandardResponse(
            message=f'不支持的文件类型: {ext}，允许的类型: {", ".join(sorted(ALLOWED_FILE_EXTENSIONS))}',
            code=400
        )

    # 文件大小校验
    if file_obj.size > MAX_FILE_SIZE:
        return StandardResponse(
            message=f'文件大小超过上限({MAX_FILE_SIZE // 1024 // 1024}MB)',
            code=400
        )

    file_content = file_obj.read()

    enable_multimodel = request.POST.get('enable_multimodel', 'true').lower() == 'true'
    metadata = request.POST.get('metadata')

    result = KnowledgeService.upload_file_knowledge(
        kb_id=kb_id,
        file_content=file_content,
        file_name=file_name,
        metadata={'raw': metadata} if metadata else None,
        enable_multimodel=enable_multimodel
    )

    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='上传成功')
    return StandardResponse(message=result.get('error', '上传失败'), code=result.get('http_status', 500))


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_url_knowledge_view(request, kb_id):
    """从 URL 创建知识"""
    _check_kb_project_permission(request, kb_id)
    url = request.data.get('url')
    enable_multimodel = request.data.get('enable_multimodel', True)

    result = KnowledgeService.create_url_knowledge(kb_id, url, enable_multimodel)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='创建成功')
    return StandardResponse(message=result.get('error', '创建失败'), code=result.get('http_status', 500))


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_manual_knowledge_view(request, kb_id):
    """创建手动 Markdown 知识"""
    _check_kb_project_permission(request, kb_id)
    title = request.data.get('title')
    content = request.data.get('content')
    tag_id = request.data.get('tag_id')

    result = KnowledgeService.create_manual_knowledge(kb_id, title, content, tag_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='创建成功')
    return StandardResponse(message=result.get('error', '创建失败'), code=result.get('http_status', 500))


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_knowledge_view(request, knowledge_id):
    """获取知识详情"""
    result = KnowledgeService.get_knowledge(knowledge_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=result.get('http_status', 500))


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_knowledge_view(request, knowledge_id):
    """更新知识"""
    _check_kb_permission_by_knowledge(request, knowledge_id)
    data = request.data
    result = KnowledgeService.update_knowledge(
        knowledge_id,
        title=data.get('title'),
        description=data.get('description'),
        tag_id=data.get('tag_id')
    )
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='更新成功')
    return StandardResponse(message=result.get('error', '更新失败'), code=result.get('http_status', 500))


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def update_manual_knowledge_view(request, knowledge_id):
    """更新手动 Markdown 知识"""
    _check_kb_permission_by_knowledge(request, knowledge_id)
    data = request.data
    result = KnowledgeService.update_manual_knowledge(
        knowledge_id,
        title=data.get('title'),
        content=data.get('content')
    )
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='更新成功')
    return StandardResponse(message=result.get('error', '更新失败'), code=result.get('http_status', 500))


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_knowledge_view(request, knowledge_id):
    """删除知识"""
    _check_kb_permission_by_knowledge(request, knowledge_id)
    result = KnowledgeService.delete_knowledge(knowledge_id)
    if result.get('success'):
        return StandardResponse(message='删除成功')
    return StandardResponse(message=result.get('error', '删除失败'), code=result.get('http_status', 500))


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def download_knowledge_view(request, knowledge_id):
    """下载知识文件"""
    _check_kb_permission_by_knowledge(request, knowledge_id)
    from django.http import HttpResponse

    response = KnowledgeService.download_knowledge(knowledge_id)

    # 处理错误情况
    if isinstance(response, dict):
        return StandardResponse(
            message=response.get('error', '下载失败'),
            code=500
        )

    # 使用 Django HttpResponse 直接返回二进制内容
    return HttpResponse(
        response.content,
        content_type=response.headers.get('Content-Type', 'application/octet-stream'),
        headers={
            'Content-Disposition': response.headers.get('Content-Disposition', '')
        }
    )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def reparse_knowledge_view(request, knowledge_id):
    """重新解析知识"""
    _check_kb_permission_by_knowledge(request, knowledge_id)
    result = KnowledgeService.reparse_knowledge(knowledge_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='重新解析已启动')
    return StandardResponse(message=result.get('error', '重解析失败'), code=result.get('http_status', 500))


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search_knowledge_view(request):
    """搜索/浏览知识项目"""
    keyword = request.query_params.get('keyword')
    offset = int(request.query_params.get('offset', 0))
    limit = int(request.query_params.get('limit', 20))
    file_types = request.query_params.get('file_types')
    agent_id = request.query_params.get('agent_id')

    file_types_list = file_types.split(',') if file_types else None

    result = KnowledgeService.search_knowledge(
        keyword=keyword,
        offset=offset,
        limit=limit,
        file_types=file_types_list,
        agent_id=agent_id
    )
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='搜索成功')
    return StandardResponse(message=result.get('error', '搜索失败'), code=result.get('http_status', 500))


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def move_knowledge_view(request):
    """迁移知识到另一个知识库"""
    data = request.data
    knowledge_ids = data.get('knowledge_ids', [])
    source_kb_id = data.get('source_kb_id')
    target_kb_id = data.get('target_kb_id')
    mode = data.get('mode', 'reuse_vectors')

    result = KnowledgeService.move_knowledge(knowledge_ids, source_kb_id, target_kb_id, mode)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='迁移任务已创建')
    return StandardResponse(message=result.get('error', '迁移失败'), code=result.get('http_status', 500))


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_move_progress_view(request, task_id):
    """获取知识迁移进度"""
    result = KnowledgeService.get_move_progress(task_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=result.get('http_status', 500))


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def preview_knowledge_view(request, knowledge_id):
    """预览知识文件"""
    import logging
    from django.http import HttpResponse
    logger = logging.getLogger(__name__)

    try:
        # 先尝试获取知识详情，使用 description 作为预览内容
        knowledge_result = KnowledgeService.get_knowledge(knowledge_id)

        if not knowledge_result.get('success'):
            return StandardResponse(
                message=knowledge_result.get('error', '获取知识失败'),
                code=404
            )

        knowledge_data = knowledge_result.get('data', {})
        description = knowledge_data.get('description', '')
        file_type = knowledge_data.get('file_type', '')
        file_name = knowledge_data.get('file_name', '') or knowledge_data.get('title', '')

        # 如果有解析后的描述内容，直接返回文本
        if description:
            # 返回文本内容
            return HttpResponse(
                description.encode('utf-8'),
                content_type='text/plain; charset=utf-8',
                headers={
                    'Content-Disposition': f'inline; filename="{file_name}.txt"'
                }
            )

        # 尝试调用 preview 接口获取原始文件
        response = KnowledgeService.preview_knowledge(knowledge_id)

        # 处理错误情况（返回字典而非 Response 对象）
        if isinstance(response, dict):
            return StandardResponse(
                message=response.get('error', '预览失败'),
                code=500
            )

        # 检查响应状态
        if response.status_code != 200:
            logger.error(f"Preview knowledge {knowledge_id} failed with status {response.status_code}")
            return StandardResponse(
                message='预览失败',
                code=response.status_code
            )

        content_type = response.headers.get('Content-Type', 'application/octet-stream')

        # 使用 Django HttpResponse 直接返回，绕过 DRF 渲染器
        return HttpResponse(
            response.content,
            content_type=content_type,
            headers={
                'Content-Disposition': response.headers.get('Content-Disposition', '')
            }
        )

    except Exception as e:
        logger.error(f"Preview knowledge {knowledge_id} error: {str(e)}", exc_info=True)
        return StandardResponse(
            message=f'预览失败: {str(e)}',
            code=500
        )


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_knowledge_content_view(request, knowledge_id):
    """获取知识内容"""
    result = KnowledgeService.get_knowledge_content(knowledge_id)
    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='获取成功')
    return StandardResponse(message=result.get('error', '获取失败'), code=result.get('http_status', 500))
