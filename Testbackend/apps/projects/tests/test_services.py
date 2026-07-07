"""
项目模块 - 测试

包含项目模块的单元测试和集成测试。
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.projects.services import ProjectService, ProjectMemberService
from apps.projects.repositories import ProjectRepository, ProjectMemberRepository

User = get_user_model()


class ProjectRepositoryTestCase(TestCase):
    """项目 Repository 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

    def test_create_project(self):
        """测试创建项目"""
        project = ProjectRepository.create(
            name='Test Project',
            identifier='TEST001',
            type='software',
            owner=self.user
        )
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.identifier, 'TEST001')

    def test_get_by_identifier(self):
        """测试根据标识符获取项目"""
        project = ProjectRepository.create(
            name='Test Project',
            identifier='TEST002',
            type='software',
            owner=self.user
        )
        found = ProjectRepository.get_by_identifier('TEST002')
        self.assertEqual(found.id, project.id)


class ProjectServiceTestCase(TestCase):
    """项目 Service 测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

    def test_create_project_success(self):
        """测试成功创建项目"""
        project, error = ProjectService.create_project(self.user, {
            'name': 'Test Project',
            'identifier':TEST003',
            'type': 'software'
        })
        self.assertIsNone(error)
        self.assertEqual(project.name, 'Test Project')

    def test_create_project_duplicate_identifier(self):
        """测试创建重复标识符的项目"""
        ProjectService.create_project(self.user, {
            'name': 'Project 1',
            'identifier': 'TEST004'
        })
        project, error = ProjectService.create_project(self.user, {
            'name': 'Project 2',
            'identifier': 'TEST004'
        })
        self.assertIsNotNone(error)


class ProjectMemberServiceTestCase(TestCase):
    """项目成员 Service 测试"""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123',
            name='Owner'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123',
            name='Member'
        )
        self.project, _ = ProjectService.create_project(self.owner, {
            'name': 'Test Project',
            'identifier': 'TEST005'
        })

    def test_add_member(self):
        """测试添加成员"""
        member_data, error = ProjectMemberService.add_member(
            project_identifier='TEST005',
            operator=self.owner,
            user_id=self.member.id,
            role='viewer'
        )
        self.assertIsNone(error)
        self.assertEqual(member_data['username'], 'member')

    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        is_favorite, error = ProjectMemberService.toggle_favorite(
            'TEST005',
            self.owner
        )
        self.assertIsNone(error)
        self.assertTrue(is_favorite)