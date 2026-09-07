"""
测试用例模块 - 测试（异常风格）

Service 方法失败时抛出 BaseAPIException 子类，成功时只返回数据。
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.projects.services import ProjectService
from apps.testcase.services import RepositoryService, VersionService, TestCaseService
from apps.testcase.repositories import RepositoryRepository, TestModuleRepository

User = get_user_model()


class TestCaseRepositoryTestCase(TestCase):
    """Repository 层测试（直接代码，不涉及异常）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testtc1', email='tc1@test.com',
            password='testpass123', name='TC User 1'
        )
        self.project = ProjectService.create_project(self.user, {
            'name': 'Test Project', 'code': 'tc001'
        })
        self.repository = RepositoryRepository.create_repository(
            name='Test Repository', project=self.project, created_by=self.user
        )

    def test_get_repositories_by_project(self):
        repositories = RepositoryRepository.get_by_project(self.project)
        self.assertGreaterEqual(len(repositories), 1)
        self.assertTrue(repositories.filter(id=self.repository.id).exists())


class TestCaseServiceTestCase(TestCase):
    """测试用例 Service 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testtc2', email='tc2@test.com',
            password='testpass123', name='TC User 2'
        )
        self.project = ProjectService.create_project(self.user, {
            'name': 'Test Project', 'code': 'tc002'
        })
        self.repository = RepositoryService.create_repository(
            name='Test Repository', project=self.project, created_by=self.user
        )
        self.version = VersionService.create_version(
            name='v1.0', repository_id=self.repository.id, created_by=self.user
        )

    def test_create_test_case(self):
        test_case = TestCaseService.create_test_case({
            'title': 'Test Case 1', 'version': self.version, 'priority': 'p2'
        }, self.user)
        self.assertEqual(test_case.title, 'Test Case 1')

    def test_copy_test_case(self):
        original = TestCaseService.create_test_case({
            'title': 'Original Case', 'version': self.version, 'priority': 'p2'
        }, self.user)
        copied = TestCaseService.copy_test_case(original, self.user)
        self.assertEqual(copied.title, 'Original Case (复制)')
        self.assertNotEqual(copied.id, original.id)


class VersionServiceTestCase(TestCase):
    """版本 Service 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testtc3', email='tc3@test.com',
            password='testpass123', name='TC User 3'
        )
        self.project = ProjectService.create_project(self.user, {
            'name': 'Test Project', 'code': 'tc003'
        })
        self.repository = RepositoryService.create_repository(
            name='Test Repository', project=self.project, created_by=self.user
        )

    def test_create_version(self):
        version = VersionService.create_version(
            name='v1.0', repository_id=self.repository.id, created_by=self.user
        )
        self.assertEqual(version.name, 'v1.0')

    def test_set_default_version(self):
        version1 = VersionService.create_version(
            name='v1.0', repository_id=self.repository.id, created_by=self.user
        )
        version2 = VersionService.create_version(
            name='v2.0', repository_id=self.repository.id, created_by=self.user
        )
        VersionService.set_default(version2.id)
        version1.refresh_from_db()
        version2.refresh_from_db()
        self.assertFalse(version1.is_default)
        self.assertTrue(version2.is_default)
