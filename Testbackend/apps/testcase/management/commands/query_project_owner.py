"""
查询项目创建者的管理命令
"""
from django.core.management.base import BaseCommand
from apps.projects.models import Project


class Command(BaseCommand):
    help = '查询项目创建者信息'

    def add_arguments(self, parser):
        parser.add_argument('--code', type=str, default='PLATFORM_TEST', help='项目标识')

    def handle(self, *args, **options):
        code = options.get('code')
        try:
            p = Project.objects.get(code=code)
            self.stdout.write('=' * 50)
            self.stdout.write(f'项目名称: {p.name}')
            self.stdout.write(f'项目标识: {p.code}')
            self.stdout.write('=' * 50)
            if p.owner:
                self.stdout.write(f'创建者用户名: {p.owner.username}')
                self.stdout.write(f'创建者ID: {p.owner.id}')
                self.stdout.write(f'创建者姓名: {p.owner.name}')
                self.stdout.write(f'创建者邮箱: {p.owner.email}')
                if p.owner.system_role:
                    self.stdout.write(f'创建者角色: {p.owner.system_role.name}')
            else:
                self.stdout.write('创建者: 无')
            self.stdout.write(f'创建时间: {p.created_at}')
            self.stdout.write(f'项目状态: {p.get_status_display()}')
        except Project.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'项目不存在: {code}'))
