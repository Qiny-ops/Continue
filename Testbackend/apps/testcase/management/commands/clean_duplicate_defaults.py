"""
清理同项目下的重复默认用例库/版本

保持最早创建的为默认，其余设为 is_default=False。
用法：
    python manage.py clean_duplicate_defaults [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.testcase.models import TestCaseRepository, TestCaseVersion


class Command(BaseCommand):
    help = '清理同项目下重复的默认用例库和版本'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='仅预览')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # 清理重复默认用例库
        dups = (
            TestCaseRepository.objects
            .filter(is_default=True)
            .values('project_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )
        repo_count = sum(d['cnt'] - 1 for d in dups)

        for d in dups:
            repos = TestCaseRepository.objects.filter(
                project_id=d['project_id'], is_default=True
            ).order_by('created_at')
            kept = repos.first()
            to_unset_ids = list(repos.values_list('id', flat=True)[1:])
            self.stdout.write(
                f'用例库 | 项目 #{d["project_id"]} → '
                f'保留: #{kept.id} {kept.name} | '
                f'清理: {", ".join(f"#{r}" for r in to_unset_ids)}'
            )
            if not dry_run:
                TestCaseRepository.objects.filter(id__in=to_unset_ids).update(is_default=False)

        # 清理重复默认版本
        ver_dups = (
            TestCaseVersion.objects
            .filter(is_default=True)
            .values('repository_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )
        ver_count = sum(d['cnt'] - 1 for d in ver_dups)

        for d in ver_dups:
            vers = TestCaseVersion.objects.filter(
                repository_id=d['repository_id'], is_default=True
            ).order_by('created_at')
            kept = vers.first()
            to_unset_ids = list(vers.values_list('id', flat=True)[1:])
            self.stdout.write(
                f'版本 | 用例库 #{d["repository_id"]} → '
                f'保留: #{kept.id} {kept.name} | '
                f'清理: {", ".join(f"#{v}" for v in to_unset_ids)}'
            )
            if not dry_run:
                TestCaseVersion.objects.filter(id__in=to_unset_ids).update(is_default=False)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN: 将清理 {repo_count} 个重复默认用例库 + {ver_count} 个重复默认版本'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'完成: 清理 {repo_count} 个重复默认用例库 + {ver_count} 个重复默认版本'
            ))
