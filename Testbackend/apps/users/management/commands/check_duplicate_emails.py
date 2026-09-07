"""
检查并修复重复邮箱地址

背景：User.email 新增 unique=True 约束。如果数据库中已存在重复邮箱，migrate 会失败。

用法：
    # 仅检查（不修改）
    python manage.py check_duplicate_emails

    # 自动修复：保留最早创建的用户，将后续重复用户的 email 设为空
    python manage.py check_duplicate_emails --fix
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.users.models import User


class Command(BaseCommand):
    help = '检查并修复重复邮箱地址（迁移前必做）'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='自动修复重复邮箱')

    def handle(self, *args, **options):
        do_fix = options['fix']

        # 找出有重复邮箱的记录
        duplicates = (
            User.objects
            .exclude(email__isnull=True)
            .exclude(email='')
            .values('email')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
            .order_by('-cnt')
        )

        total_dup = duplicates.count()
        if total_dup == 0:
            self.stdout.write(self.style.SUCCESS('无重复邮箱，迁移安全。'))
            return

        affected_users = sum(d['cnt'] for d in duplicates)
        self.stdout.write(self.style.WARNING(
            f'发现 {total_dup} 个重复邮箱，影响 {affected_users} 个用户：'
        ))

        for dup in duplicates:
            email = dup['email']
            users = User.objects.filter(email=email).order_by('created_at')
            kept = users.first()
            to_fix = users[1:]
            self.stdout.write(
                f'  📧 {email}: {users.count()} 个用户'
                f'  → 保留: #{kept.id} {kept.username} (创建于 {kept.created_at})'
            )
            for u in to_fix:
                self.stdout.write(f'     重复: #{u.id} {u.username} (创建于 {u.created_at})')

        if not do_fix:
            self.stdout.write(
                f'\n使用 --fix 参数自动修复：保留最早的用户，清空重复用户的 email'
            )
            return

        # 执行修复
        fixed = 0
        for dup in duplicates:
            email = dup['email']
            users = User.objects.filter(email=email).order_by('created_at')
            for u in users[1:]:
                u.email = ''
                u.save(update_fields=['email'])
                fixed += 1

        self.stdout.write(self.style.SUCCESS(
            f'修复完成：清空了 {fixed} 个重复用户的 email 地址'
        ))
        self.stdout.write('现在可以安全执行 migrate 了。')
