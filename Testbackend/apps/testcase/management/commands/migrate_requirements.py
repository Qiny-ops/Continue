"""
修复旧 requirement 文本值 → FK 关联

背景：TestCase.requirement 从 CharField 改为 ForeignKey(Requirement) 后，
      旧的文本值（如 "REQ-LOGIN-001"）在迁移中被丢弃，新 requirement_id 列为 NULL。

用法：
    # 预览：扫描 NULL 的 requirement_id，不修改
    python manage.py migrate_requirements --dry-run

    # 执行：为每个 NULL requirement 的记录创建 Requirement 并关联
    python manage.py migrate_requirements

    # 指定项目范围
    python manage.py migrate_requirements --project-id 1
"""
from django.core.management.base import BaseCommand
from apps.testcase.models import TestCase
from apps.requirement.models import Requirement


class Command(BaseCommand):
    help = '修复旧 requirement 文本值 → FK 关联（用于 CharField→FK 迁移后的数据恢复）'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际写入')
        parser.add_argument('--project-id', type=int, default=None, help='仅处理指定项目')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        project_id = options['project_id']

        # 查询 requirement_id 为 NULL 的测试用例
        qs = TestCase.objects.filter(requirement_id__isnull=True).select_related('version__repository__project')
        if project_id:
            qs = qs.filter(version__repository__project_id=project_id)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('所有测试用例已关联需求，无需修复。'))
            return

        self.stdout.write(f'发现 {total} 条 requirement_id 为 NULL 的测试用例')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 模式 — 仅扫描，不写入'))
            for tc in qs.order_by('id')[:20]:
                project_name = tc.version.repository.project.name if tc.version and tc.version.repository and tc.version.repository.project else '未知项目'
                self.stdout.write(f'  #{tc.id} | {tc.title[:40]:40s} | 项目: {project_name}')
            if total > 20:
                self.stdout.write(f'  ... 还有 {total - 20} 条')
            return

        # 执行修复：为每个项目创建默认需求并关联
        fixed = 0
        updated = 0
        project_requirements = {}  # cache: {project_id: Requirement}

        for tc in qs.order_by('id').iterator(chunk_size=100):
            project = None
            try:
                if tc.version and tc.version.repository:
                    project = tc.version.repository.project
            except Exception:
                pass

            if not project:
                self.stdout.write(self.style.WARNING(f'  #{tc.id} 无法确定关联项目，跳过'))
                continue

            # 获取或创建该项目的默认需求
            if project.id not in project_requirements:
                req, created = Requirement.objects.get_or_create(
                    title=f'{project.name} 默认需求',
                    project=project,
                    defaults={
                        'description': f'从旧系统迁移的需求（原 requirement 文本值已丢失）',
                        'priority': 'p2',
                        'status': 'active',
                        'source': 'manual',
                        'created_by': project.owner,
                        'updated_by': project.owner,
                    }
                )
                project_requirements[project.id] = req
                if created:
                    fixed += 1
                    self.stdout.write(f'  创建需求: "{req.title}" (项目: {project.name})')
                else:
                    self.stdout.write(f'  复用已有需求: "{req.title}" (项目: {project.name})')

            tc.requirement = project_requirements[project.id]
            tc.save(update_fields=['requirement'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'修复完成：创建 {fixed} 个需求，关联 {updated} 条测试用例'
        ))
