"""将 ApiTestCase.version 同步为所属 module.version（修复跨类型统计口径不一致）。

业务逻辑审计 #10：接口用例与手工用例共享同一套版本/模块体系，但 ApiTestCase 此前
缺少 save() 级别的版本同步，导致同一模块下两者 version 漂移、按版本统计对不上。
本命令对历史数据做一次性回填；新数据由 ApiTestCase.save() 自动保证一致。
"""
from django.core.management.base import BaseCommand
from django.db.models import F

from apps.apitest.models import ApiTestCase


class Command(BaseCommand):
    help = '将 ApiTestCase.version 同步为所属 module.version（修复版本口径不一致，#10）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只统计需要同步的用例数，不实际修改',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # 仅取 module 已设置、且 version 与 module.version 不一致（含 version 为空）的用例
        mismatched = (
            ApiTestCase.objects
            .filter(module__isnull=False)
            .exclude(module__version=F('version'))
        )

        total = mismatched.count()
        prefix = '[dry-run] ' if dry_run else ''
        self.stdout.write(f"{prefix}待同步 ApiTestCase（module 已设且 version 不一致）：{total} 条")

        if dry_run or total == 0:
            return

        synced = 0
        for case in mismatched.select_related('module'):
            if case.module and case.module.version_id:
                case.version_id = case.module.version_id
                case.save(update_fields=['version'])
                synced += 1

        self.stdout.write(self.style.SUCCESS(f"已同步 {synced} 条 ApiTestCase 的 version"))
