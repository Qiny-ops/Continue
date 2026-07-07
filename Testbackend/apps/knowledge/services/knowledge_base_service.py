"""
知识库服务

提供知识库管理的业务逻辑。
"""

import logging
from typing import Dict, Any, Optional
from apps.knowledge.repositories import weknora_repository

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库服务"""

    @staticmethod
    def list_knowledge_bases() -> Dict[str, Any]:
        """获取知识库列表"""
        try:
            return weknora_repository.list_knowledge_bases()
        except Exception as e:
            logger.error(f'获取知识库列表失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_knowledge_base(data: Dict[str, Any]) -> Dict[str, Any]:
        """创建知识库"""
        try:
            name = data.get('name')
            if not name:
                return {'success': False, 'error': '知识库名称不能为空'}

            kb_data = {
                'name': name,
                'description': data.get('description', ''),
                'type': data.get('type', 'document'),
                'is_temporary': data.get('is_temporary', False),
            }

            optional_fields = [
                'chunking_config', 'embedding_model_id', 'summary_model_id',
                'storage_provider_config', 'storage_config', 'vlm_config',
                'asr_config', 'question_generation_config'
            ]
            for field in optional_fields:
                if field in data:
                    kb_data[field] = data[field]

            return weknora_repository.create_knowledge_base(kb_data)
        except Exception as e:
            logger.error(f'创建知识库失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_knowledge_base(kb_id: str) -> Dict[str, Any]:
        """获取知识库详情"""
        try:
            return weknora_repository.get_knowledge_base(kb_id)
        except Exception as e:
            logger.error(f'获取知识库详情失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_knowledge_base(kb_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识库"""
        try:
            return weknora_repository.update_knowledge_base(kb_id, data)
        except Exception as e:
            logger.error(f'更新知识库失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_knowledge_base(kb_id: str) -> Dict[str, Any]:
        """删除知识库"""
        try:
            return weknora_repository.delete_knowledge_base(kb_id)
        except Exception as e:
            logger.error(f'删除知识库失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def copy_knowledge_base(source_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """复制知识库"""
        try:
            if not source_id:
                return {'success': False, 'error': '源知识库ID不能为空'}
            return weknora_repository.copy_knowledge_base(source_id, name)
        except Exception as e:
            logger.error(f'复制知识库失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_copy_progress(task_id: str) -> Dict[str, Any]:
        """获取复制进度"""
        try:
            return weknora_repository.get_copy_progress(task_id)
        except Exception as e:
            logger.error(f'获取复制进度失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def pin_knowledge_base(kb_id: str) -> Dict[str, Any]:
        """置顶/取消置顶知识库"""
        try:
            return weknora_repository.pin_knowledge_base(kb_id)
        except Exception as e:
            logger.error(f'置顶知识库失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def hybrid_search(kb_id: str, query_text: str, **kwargs) -> Dict[str, Any]:
        """混合搜索（向量+关键词）"""
        try:
            if not query_text:
                return {'success': False, 'error': '查询文本不能为空'}
            return weknora_repository.hybrid_search(kb_id, query_text, **kwargs)
        except Exception as e:
            logger.error(f'混合搜索失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
