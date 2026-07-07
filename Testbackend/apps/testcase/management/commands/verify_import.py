"""
验证导入结果的管理命令
"""
from django.core.management.base import BaseCommand
from apps.testcase.models import TestCase, TestStep, TestModule
from apps.projects.models import Project


class Command(BaseCommand):
    help = '验证平台功能测试用例导入结果'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('平台功能测试用例导入统计')
        self.stdout.write('=' * 50)
        
        project_count = Project.objects.filter(code='PLATFORM_TEST').count()
        self.stdout.write(f'项目数: {project_count}')
        
        module_count = TestModule.objects.count()
        self.stdout.write(f'模块数: {module_count}')
        
        tc_count = TestCase.objects.count()
        self.stdout.write(f'测试用例数: {tc_count}')
        
        step_count = TestStep.objects.count()
        self.stdout.write(f'测试步骤数: {step_count}')
        
        self.stdout.write('=' * 50)
        
        self.stdout.write('\n模块分布:')
        modules = TestModule.objects.filter(parent__isnull=True)
        for m in modules:
            child_count = TestModule.objects.filter(parent=m).count()
            tc_count = TestCase.objects.filter(module__parent=m).count()
            self.stdout.write(f'  {m.name}: {child_count}个子模块, {tc_count}个用例')
        
        self.stdout.write('\n优先级分布:')
        for p in ['p0', 'p1', 'p2', 'p3']:
            count = TestCase.objects.filter(priority=p).count()
            self.stdout.write(f'  {p.upper()}: {count}个用例')
        
        self.stdout.write('\n标签分布:')
        tags_count = {}
        for tc in TestCase.objects.all():
            for tag in tc.tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1
        for tag, count in sorted(tags_count.items(), key=lambda x: -x[1])[:10]:
            self.stdout.write(f'  {tag}: {count}个用例')
