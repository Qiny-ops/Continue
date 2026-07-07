"""
测试用例模块 - 测试

包含测试用例模块的单元测试和集成测试。
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.projects.services import ProjectService
from apps.testcase.services import RepositoryService, VersionService, TestCaseService
from apps.testcase.repositories import TestCaseRepository, TestModuleRepository

User = get_user_model()


class TestCaseRepositoryTestCase(TestCase):
    """测试用例 Repository 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.project, _ = ProjectService.create_project(self.user, {
            'name': 'Test Project',
            'identifier': 'TC001'
        })
        self.repository = TestCaseRepository.create(
            name='Test Repository',
            project=self.project,
            created_by=self.user
        )

    def test_get_repositories_by_project(self):
        """测试根据项目获取用例库列表"""
        repositories = TestCaseRepository.get_by_project(self.project.id)
        self.assertEqual(len(repositories), 1)


class TestCaseServiceTestCase(TestCase):
    """测试用例 Service 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.project, _ = ProjectService.create_project(self.user, {
            'name': 'Test Project',
            'identifier': 'TC002'
        })
        self.repository = RepositoryService.create_repository(
            name='Test Repository',
            project_id=self.project.id,
            created_by=self.user
        )
        self.version = VersionService.create_version(
            name='v1.0',
            repository_id=self.repository.id,
            created_by=self.user
        )

    def test_create_test_case(self):
        """测试创建测试用例"""
        test_case = TestCaseService.create_test_case({
            'title': 'Test Case 1',
            'version_id': self.version.id,
            'priority': 'high'
        }, self.user)
        self.assertEqual(test_case.title, 'Test Case 1')

    def test_copy_test_case(self):
        """测试复制测试用例"""
        original = TestCaseService.create_test_case({
            'title': 'Original Case',
            'version_id': self.version.id,
            'priority': 'medium'
        }, self.user)
        copied = TestCaseService.copy_test_case(original, self.user)
        self.assertEqual(copied.title, 'Original Case (副本)')
        self.assertNotEqual(copied.id, original.id)


class VersionServiceTestCase(TestCase):
    """版本 Service 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.project, _ = ProjectService.create_project(self.user, {
            'name': 'Test Project',
            'identifier': 'TC003'
        })
        self.repository = RepositoryService.create_repository(
            name='Test Repository',
            project_id=self.project.id,
            created_by=self.user
        )

    def test_create_version(self):
        """测试创建版本"""
        version = VersionService.create_version(
            name='v1.0',
            repository_id=self.repository.id,
            created_by=self.user
        )
        self.assertEqual(version.name, 'v1.0')

    def test_set_default_version(self):
        """测试设置默认版本"""
        version1 = VersionService.create_version(
            name='v1.0',
            repository_id=self.repository.id,
            created_by=self.user
        )
        version2 = VersionService.create_version(
            name='v2.0',
            repository_id=self.repository.id,
            created_by=self.user
        )
        VersionService.set_default(version2.id)
        version1.refresh_from_db()
        version2.refresh_from_db()
        self.assertFalse(version1.is_default)
        self.assertTrue(version2.is_default)