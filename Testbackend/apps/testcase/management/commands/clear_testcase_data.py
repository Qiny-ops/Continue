"""
清理测试用例数据的管理命令
删除所有测试用例相关数据并重置ID序列
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.testcase.models import (
    TestCaseRepository, TestCaseVersion, TestModule,
    TestCase, TestStep
)
from apps.projects.models import Project, ProjectMember
from apps.users.models import User


class Command(BaseCommand):
    help = '清理测试用例数据并重置ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-code',
            type=str,
            default='FRONTEND_TEST',
            help='要清理的项目标识'
        )
        parser.add_argument(
            '--delete-user',
            action='store_true',
            help='同时删除测试用户'
        )

    def handle(self, *args, **options):
        project_code = options.get('project_code')
        delete_user = options.get('delete_user')
        
        self.stdout.write('开始清理测试用例数据...')
        
        self._clear_all_testcase_data()
        
        self._clear_project_data(project_code)
        
        if delete_user:
            deleted, _ = User.objects.filter(username='frontend_test_admin').delete()
            if deleted:
                self.stdout.write('删除测试用户: frontend_test_admin')
        
        self._reset_sequences()
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n清理完成！\n'
                '- 已删除所有测试用例相关数据\n'
                '- 已重置ID序列\n'
                '现在可以重新运行导入脚本'
            )
        )

    def _clear_all_testcase_data(self):
        """清理所有测试用例相关数据"""
        self.stdout.write('清理测试用例数据...')
        
        step_count = TestStep.objects.all().delete()[0]
        self.stdout.write(f'  删除 {step_count} 条测试步骤')
        
        case_count = TestCase.objects.all().delete()[0]
        self.stdout.write(f'  删除 {case_count} 个测试用例')
        
        module_count = TestModule.objects.all().delete()[0]
        self.stdout.write(f'  删除 {module_count} 个测试模块')
        
        version_count = TestCaseVersion.objects.all().delete()[0]
        self.stdout.write(f'  删除 {version_count} 个测试版本')
        
        repo_count = TestCaseRepository.objects.all().delete()[0]
        self.stdout.write(f'  删除 {repo_count} 个测试用例库')

    def _clear_project_data(self, project_code):
        """清理项目数据"""
        self.stdout.write('清理项目数据...')
        
        try:
            project = Project.objects.get(code=project_code)
            project_id = project.id
            ProjectMember.objects.filter(project_id=project_id).delete()
            project.delete()
            self.stdout.write(f'  删除项目: {project_code}')
        except Project.DoesNotExist:
            self.stdout.write(f'  项目 {project_code} 不存在，尝试直接清理项目表...')
        
        member_count = ProjectMember.objects.all().delete()[0]
        self.stdout.write(f'  删除 {member_count} 个项目成员记录')
        
        project_count = Project.objects.all().delete()[0]
        self.stdout.write(f'  删除 {project_count} 个项目记录')

    def _reset_sequences(self):
        """重置所有相关表的ID序列"""
        self.stdout.write('重置ID序列...')

        # 表名白名单，防止 SQL 注入
        allowed_tables = {
            'testcase_testcaserepository',
            'testcase_testcaseversion',
            'testcase_testmodule',
            'testcase_testcase',
            'testcase_teststep',
            'projects_project',
            'projects_projectmember',
        }

        with connection.cursor() as cursor:
            for table in allowed_tables:
                try:
                    # 使用参数化查询，安全地执行 SQL
                    cursor.execute(
                        "DELETE FROM sqlite_sequence WHERE name=%s",
                        [table]
                    )
                except Exception as e:
                    self.stdout.write(f'  警告: 重置 {table} 序列失败 - {e}')

        self.stdout.write('ID序列重置完成')
