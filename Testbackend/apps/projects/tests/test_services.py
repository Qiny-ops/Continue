"""
项目模块 - 测试

全部使用异常风格：Service 方法失败时抛出 BaseAPIException 子类，
由 DRF 异常处理器统一转为 HTTP 响应。成功时只返回数据（非元组）。
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.projects.services import ProjectService, ProjectMemberService
from apps.projects.repositories import ProjectRepository, ProjectMemberRepository
from apps.core.exceptions import BusinessError, ValidationError, NotFoundError, PermissionDenied

User = get_user_model()


class ProjectRepositoryTestCase(TestCase):
    """项目 Repository 测试（Repository 层不抛业务异常，仍保持原始行为）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testreposvc', email='repo@test.com',
            password='testpass123', name='Repo User'
        )

    def test_create_project(self):
        project = ProjectRepository.create_project(name='Test Project', code='test001', owner=self.user)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.code, 'test001')

    def test_get_by_identifier(self):
        project = ProjectRepository.create_project(name='Test Project', code='test002', owner=self.user)
        found = ProjectRepository.get_by_identifier('TEST002')
        self.assertIsNotNone(found)
        self.assertEqual(found.id, project.id)


class ProjectServiceTestCase(TestCase):
    """项目 Service 测试（异常风格）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testproj', email='proj@test.com',
            password='testpass123', name='Proj User'
        )

    def test_create_project_success(self):
        project = ProjectService.create_project(self.user, {
            'name': 'Test Project', 'code': 'test003', 'type': 'web'
        })
        self.assertIsNotNone(project)
        self.assertEqual(project.name, 'Test Project')

    def test_create_project_missing_name(self):
        with self.assertRaises(ValidationError):
            ProjectService.create_project(self.user, {'code': 'test'})

    def test_create_project_missing_code(self):
        with self.assertRaises(ValidationError):
            ProjectService.create_project(self.user, {'name': 'test'})

    def test_create_project_invalid_type(self):
        with self.assertRaises(ValidationError):
            ProjectService.create_project(self.user, {'name': 'test', 'code': 't01', 'type': 'software'})

    def test_create_project_duplicate_code(self):
        ProjectService.create_project(self.user, {'name': 'P1', 'code': 'test004'})
        with self.assertRaises(BusinessError):
            ProjectService.create_project(self.user, {'name': 'P2', 'code': 'test004'})


class ProjectMemberServiceTestCase(TestCase):
    """项目成员 Service 测试"""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner2', email='owner2@test.com',
            password='testpass123', name='Owner'
        )
        self.member = User.objects.create_user(
            username='member2', email='member2@test.com',
            password='testpass123', name='Member'
        )
        self.project = ProjectService.create_project(self.owner, {
            'name': 'Test Project', 'code': 'test005'
        })

    def test_add_member(self):
        member_data = ProjectMemberService.add_member(
            project_identifier='test005', operator=self.owner,
            user_id=self.member.id, role='viewer'
        )
        self.assertEqual(member_data['name'], 'Member')

    def test_toggle_favorite(self):
        is_favorite = ProjectMemberService.toggle_favorite('test005', self.owner)
        self.assertTrue(is_favorite)
