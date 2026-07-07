"""
知识库模块 - 测试

包含知识库模块的单元测试和集成测试。
由于知识库模块是外部 WeKnora 服务的代理，测试主要验证 Repository 层的 API 调用。
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.knowledge.services import KnowledgeBaseService, KnowledgeService
from apps.knowledge.repositories import WeKnoraRepository


class WeKnoraRepositoryTestCase(TestCase):
    """WeKnora Repository 测试"""

    def setUp(self):
        self.repository = WeKnoraRepository(
            base_url='http://test-api:3000/api/v1',
            api_key='test-key'
        )

    @patch('apps.knowledge.repositories.weknora_repository.requests.Session.request')
    def test_list_knowledge_bases(self, mock_request):
        """测试获取知识库列表"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'data': [
                {'id': 'kb1', 'name': 'Knowledge Base 1'},
                {'id': 'kb2', 'name': 'Knowledge Base 2'}
            ]
        }
        mock_request.return_value = mock_response

        result = self.repository.list_knowledge_bases()
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 2)

    @patch('apps.knowledge.repositories.weknora_repository.requests.Session.request')
    def test_create_knowledge_base(self, mock_request):
        """测试创建知识库"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'data': {'id': 'kb-new', 'name': 'New KB'}
        }
        mock_request.return_value = mock_response

        result = self.repository.create_knowledge_base({
            'name': 'New KB',
            'type': 'document'
        })
        self.assertTrue(result['success'])


class KnowledgeBaseServiceTestCase(TestCase):
    """知识库 Service 测试"""

    @patch('apps.knowledge.services.knowledge_base_service.weknora_repository.list_knowledge_bases')
    def test_list_knowledge_bases(self, mock_list):
        """测试获取知识库列表"""
        mock_list.return_value = {
            'success': True,
            'data': [{'id': 'kb1', 'name': 'KB 1'}]
        }
        result = KnowledgeBaseService.list_knowledge_bases()
        self.assertTrue(result['success'])

    @patch('apps.knowledge.services.knowledge_base_service.weknora_repository.create_knowledge_base')
    def test_create_knowledge_base_validation(self, mock_create):
        """测试创建知识库验证"""
        result = KnowledgeBaseService.create_knowledge_base({})
        self.assertFalse(result['success'])
        self.assertIn('名称', result['error'])


class KnowledgeServiceTestCase(TestCase):
    """知识文档 Service 测试"""

    @patch('apps.knowledge.services.knowledge_service.weknora_repository.create_url_knowledge')
    def test_create_url_knowledge_validation(self, mock_create):
        """测试从 URL 创建知识验证"""
        result = KnowledgeService.create_url_knowledge('kb1', '')
        self.assertFalse(result['success'])
        self.assertIn('URL', result['error'])

    @patch('apps.knowledge.services.knowledge_service.weknora_repository.create_manual_knowledge')
    def test_create_manual_knowledge_validation(self, mock_create):
        """测试创建手动知识验证"""
        result = KnowledgeService.create_manual_knowledge('kb1', '', 'content')
        self.assertFalse(result['success'])
        self.assertIn('标题', result['error'])