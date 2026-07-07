"""
清理过期的 Token 黑名单记录

使用方法:
    python manage.py cleanup_token_blacklist

可以添加到 crontab 定时执行:
    0 * * * * cd /path/to/project && python manage.py cleanup_token_blacklist
"""

from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.users.models import TokenBlacklist


class Command(BaseCommand):
    help = '清理过期的 Token 黑名单记录'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='仅显示将被删除的记录数量，不实际删除',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            count = TokenBlacklist.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] 将删除 {count} 条过期的黑名单记录')
            )
        else:
            deleted_count, _ = TokenBlacklist.cleanup_expired()
            self.stdout.write(
                self.style.SUCCESS(f'成功清理 {deleted_count} 条过期的黑名单记录')
            )
