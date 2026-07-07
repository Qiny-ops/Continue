"""
知识文档服务

提供知识文档管理的业务逻辑。
"""

import logging
from typing import Dict, Any, List, Optional
from apps.knowledge.repositories import weknora_repository

logger = logging.getLogger(__name__)


class KnowledgeService:
    """知识文档服务"""

    @staticmethod
    def list_knowledge(kb_id: str, page: int = 1, page_size: int = 20, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """获取知识列表"""
        try:
            return weknora_repository.list_knowledge(kb_id, page, page_size, tag_id)
        except Exception as e:
            logger.error(f'获取知识列表失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def upload_file_knowledge(kb_id: str, file_content: bytes, file_name: str, metadata: Optional[Dict] = None, enable_multimodel: bool = True) -> Dict[str, Any]:
        """上传文件知识"""
        try:
            return weknora_repository.upload_file_knowledge_raw(
                kb_id=kb_id,
                file_content=file_content,
                file_name=file_name,
                metadata=metadata,
                enable_multimodel=enable_multimodel
            )
        except Exception as e:
            logger.error(f'上传文件知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_url_knowledge(kb_id: str, url: str, enable_multimodel: bool = True) -> Dict[str, Any]:
        """从 URL 创建知识"""
        try:
            if not url:
                return {'success': False, 'error': 'URL 不能为空'}
            return weknora_repository.create_url_knowledge(kb_id, url, enable_multimodel)
        except Exception as e:
            logger.error(f'从 URL 创建知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_manual_knowledge(kb_id: str, title: str, content: str, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """创建手动 Markdown 知识"""
        try:
            if not title or not content:
                return {'success': False, 'error': '标题和内容不能为空'}
            return weknora_repository.create_manual_knowledge(kb_id, title, content, tag_id)
        except Exception as e:
            logger.error(f'创建手动知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_knowledge(knowledge_id: str) -> Dict[str, Any]:
        """获取知识详情"""
        try:
            return weknora_repository.get_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f'获取知识详情失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_knowledge(knowledge_id: str, title: Optional[str] = None, description: Optional[str] = None, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """更新知识"""
        try:
            return weknora_repository.update_knowledge(knowledge_id, title, description, tag_id)
        except Exception as e:
            logger.error(f'更新知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_manual_knowledge(knowledge_id: str, title: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """更新手动 Markdown 知识"""
        try:
            return weknora_repository.update_manual_knowledge(knowledge_id, title, content)
        except Exception as e:
            logger.error(f'更新手动知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def delete_knowledge(knowledge_id: str) -> Dict[str, Any]:
        """删除知识"""
        try:
            return weknora_repository.delete_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f'删除知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def download_knowledge(knowledge_id: str):
        """下载知识文件"""
        return weknora_repository.download_knowledge(knowledge_id)

    @staticmethod
    def reparse_knowledge(knowledge_id: str) -> Dict[str, Any]:
        """重新解析知识"""
        try:
            return weknora_repository.reparse_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f'重新解析知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def search_knowledge(keyword: Optional[str] = None, offset: int = 0, limit: int = 20, file_types: Optional[List[str]] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """搜索知识"""
        try:
            return weknora_repository.search_knowledge(keyword, offset, limit, file_types, agent_id)
        except Exception as e:
            logger.error(f'搜索知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def move_knowledge(knowledge_ids: List[str], source_kb_id: str, target_kb_id: str, mode: str = 'reuse_vectors') -> Dict[str, Any]:
        """迁移知识"""
        try:
            if not knowledge_ids or not source_kb_id or not target_kb_id:
                return {'success': False, 'error': '参数不完整'}
            return weknora_repository.move_knowledge(knowledge_ids, source_kb_id, target_kb_id, mode)
        except Exception as e:
            logger.error(f'迁移知识失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_move_progress(task_id: str) -> Dict[str, Any]:
        """获取迁移进度"""
        try:
            return weknora_repository.get_move_progress(task_id)
        except Exception as e:
            logger.error(f'获取迁移进度失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def preview_knowledge(knowledge_id: str):
        """预览知识文件"""
        return weknora_repository.preview_knowledge(knowledge_id)

    @staticmethod
    def get_knowledge_content(knowledge_id: str) -> Dict[str, Any]:
        """获取知识内容"""
        try:
            return weknora_repository.get_knowledge(knowledge_id)
        except Exception as e:
            logger.error(f'获取知识内容失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
