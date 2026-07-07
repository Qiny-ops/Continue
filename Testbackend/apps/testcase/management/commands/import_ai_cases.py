"""
导入AI生成的测试用例

将AI生成的JSON格式测试用例导入数据库
"""

import json
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.testcase.models import (
    TestCaseVersion, TestModule, TestCase
)


PRIORITY_MAP = {
    '高': 'p1',
    '中': 'p2',
    '低': 'p3',
}


AI_CASES = [
    {"testpoint": "请假原因必填验证 - 不输入请假原因", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、不输入请假原因，直接点击提交", "expectation": "系统提示'请输入请假理由'，提交失败"},
    {"testpoint": "请假原因必填验证 - 输入空格", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入一个或多个空格\n4、点击提交", "expectation": "系统提示'请输入请假理由'，提交失败"},
    {"testpoint": "请假原因最大长度验证 - 输入34个汉字", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入34个汉字\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "请假原因最大长度验证 - 输入35个汉字", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入35个汉字\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "请假原因最大长度验证 - 输入36个汉字", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入36个汉字\n4、点击提交", "expectation": "系统提示'请假原因仅支持35个汉字'，提交失败"},
    {"testpoint": "字符计算规则验证 - 34个汉字+1个英文字符", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入34个汉字和1个英文字符\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "字符计算规则验证 - 35个英文字符", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入35个英文字符\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "字符计算规则验证 - 35个数字", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入35个数字\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "混合字符测试 - 汉字、英文、数字混合", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入包含汉字、英文、数字的混合内容，总字符数不超过35个汉字\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "特殊字符测试 - 包含标点符号", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入包含标点符号的内容，总字符数不超过35个汉字\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "复制粘贴测试 - 从外部复制35个汉字", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、从外部文档复制35个汉字到请假原因输入框\n4、点击提交", "expectation": "提交成功，系统提示请假申请已提交"},
    {"testpoint": "复制粘贴测试 - 从外部复制36个汉字", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、从外部文档复制36个汉字到请假原因输入框\n4、点击提交", "expectation": "系统提示'请假原因仅支持35个汉字'，提交失败"},
    {"testpoint": "前后空格处理 - 输入内容前后有空格", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入'   请假原因内容   '（前后有空格）\n4、点击提交", "expectation": "提交成功，系统自动去除前后空格后存储"},
    {"testpoint": "换行符处理 - 输入内容包含换行符", "priority": "中", "steps": "1、登录成功后进入请假页面\n2、选择请假日期为当前日期\n3、请假原因输入包含换行符的内容\n4、点击提交", "expectation": "提交成功，换行符被正确处理"},
    {"testpoint": "界面交互 - 实时字数展示", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、在请假原因输入框中输入内容\n3、观察输入框下方的字数提示", "expectation": "实时显示已输入字符数/35，汉字按1个字符计算"},
    {"testpoint": "界面交互 - 超过限制时提示", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、在请假原因输入框中输入超过35个汉字\n3、观察输入框状态", "expectation": "输入框显示警告样式，提示字符数已超出限制"},
    {"testpoint": "错误提示测试 - 超过长度限制的提示语", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、输入超过35个汉字的请假原因\n3、点击提交", "expectation": "提示语明确：'请假原因仅支持35个汉字'"},
    {"testpoint": "错误提示测试 - 必填验证的提示语", "priority": "高", "steps": "1、登录成功后进入请假页面\n2、不输入请假原因\n3、点击提交", "expectation": "提示语明确：'请输入请假理由'"},
]


class Command(BaseCommand):
    help = '导入AI生成的请假原因验证测试用例'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ver',
            type=str,
            default='oa-system_V2.0',
            help='版本标识 (默认: oa-system_V2.0)',
        )
        parser.add_argument(
            '--mod',
            type=str,
            default='oa-system_V2.0_请假功能',
            help='模块标识 (默认: oa-system_V2.0_请假功能)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='lisi',
            help='创建者用户名 (默认: lisi)',
        )

    def handle(self, *args, **options):
        version_key = options['ver']
        module_key = options['mod']
        username = options['user']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f'用户不存在: {username}')
            return

        version = TestCaseVersion.objects.filter(
            repository__project__code=version_key.split('_')[0],
            name='_'.join(version_key.split('_')[1:])
        ).first()
        if not version:
            self.stderr.write(f'版本不存在: {version_key}')
            return

        module = TestModule.objects.filter(
            version=version,
            name=module_key.split('_')[-1]
        ).first()
        if not module:
            self.stderr.write(f'模块不存在: {module_key}')
            return

        self.stdout.write(f'目标版本: {version.name}')
        self.stdout.write(f'目标模块: {module.name}')
        self.stdout.write(f'创建者: {user.name}')
        self.stdout.write(f'待导入用例: {len(AI_CASES)} 条')
        self.stdout.write('')

        created_count = 0
        skipped_count = 0

        for i, case_data in enumerate(AI_CASES, 1):
            title = case_data.get('testpoint', f'AI生成用例_{i}')
            priority = PRIORITY_MAP.get(case_data.get('priority', '中'), 'p2')
            steps = case_data.get('steps', '')
            expected_result = case_data.get('expectation', '')

            existing = TestCase.objects.filter(
                title=title,
                version=version,
                module=module,
            ).first()

            if existing:
                self.stdout.write(f'  [{i}] 跳过(已存在): {title}')
                skipped_count += 1
                continue

            TestCase.objects.create(
                title=title,
                module=module,
                version=version,
                priority=priority,
                precondition='1. 已登录OA系统\n2. 进入请假申请页面',
                steps=steps,
                expected_result=expected_result,
                tags=['请假', 'AI生成'],
                automation_status='not_analyzed',
                review_status='pending',
                generation_source='ai_generated',
                ai_request_id='REQ-AI-20260515-LEAVE-VALIDATION',
                ai_model_version='gpt-4o',
                ai_confidence=0.80,
                created_by=user,
                updated_by=user,
            )
            self.stdout.write(f'  [{i}] 创建成功: {title}')
            created_count += 1

        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(f'导入完成: 创建 {created_count} 条, 跳过 {skipped_count} 条')
        self.stdout.write(f'当前模块用例总数: {TestCase.objects.filter(module=module).count()} 条')
