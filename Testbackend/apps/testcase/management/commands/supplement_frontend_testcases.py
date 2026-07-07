"""
补充前端功能测试用例的管理命令
补充忘记密码、接口测试、导入导出等缺失的测试用例
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User
from apps.testcase.models import (
    TestCaseRepository, TestCaseVersion, TestModule,
    TestCase, TestStep
)


class Command(BaseCommand):
    help = '补充前端功能测试用例'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            required=True,
            help='指定项目ID'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='指定用户ID作为创建者'
        )

    def handle(self, *args, **options):
        self.stdout.write('开始补充前端功能测试用例...')
        
        project_id = options.get('project_id')
        user_id = options.get('user_id')
        
        with transaction.atomic():
            user = User.objects.get(id=user_id)
            repository = TestCaseRepository.objects.get(project_id=project_id)
            version = TestCaseVersion.objects.get(repository=repository, is_default=True)
            
            modules = self._create_modules(version)
            
            test_cases_count = self._create_test_cases(version, modules, user)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n补充完成！\n'
                    f'- 新增模块数: {len(modules)}\n'
                    f'- 新增测试用例数: {test_cases_count}'
                )
            )

    def _create_modules(self, version):
        modules_config = [
            ('用户认证模块', [
                ('忘记密码', None),
                ('用户信息组件', None),
            ]),
            ('项目管理模块', [
                ('接口测试', None),
                ('项目导航', None),
            ]),
            ('测试用例管理模块', [
                ('用例筛选', None),
                ('批量操作', None),
                ('导入导出', None),
            ]),
        ]
        
        modules = {}
        sort_order = TestModule.objects.filter(version=version).count()
        
        for item in modules_config:
            if isinstance(item[1], list):
                parent_name, children = item
                parent, created = TestModule.objects.get_or_create(
                    version=version,
                    name=parent_name,
                    defaults={'sort_order': sort_order}
                )
                if not created:
                    parent.sort_order = sort_order
                    parent.save()
                modules[parent_name] = parent
                sort_order += 1
                
                for child_name, _ in children:
                    child, created = TestModule.objects.get_or_create(
                        version=version,
                        name=child_name,
                        parent=parent,
                        defaults={'sort_order': sort_order}
                    )
                    if not created:
                        child.sort_order = sort_order
                        child.save()
                    modules[f"{parent_name}-{child_name}"] = child
                    sort_order += 1
        
        return modules

    def _create_test_cases(self, version, modules, user):
        test_cases_data = self._get_test_cases_data()
        
        count = 0
        for module_key, test_cases in test_cases_data:
            module = modules.get(module_key)
            if not module:
                continue
            
            for tc_data in test_cases:
                tc, created = TestCase.objects.get_or_create(
                    title=tc_data['title'],
                    version=version,
                    module=module,
                    defaults={
                        'priority': tc_data.get('priority', 'p2'),
                        'precondition': tc_data.get('precondition', ''),
                        'tags': tc_data.get('tags', []),
                        'created_by': user
                    }
                )
                
                if created:
                    for idx, (step_desc, expected) in enumerate(tc_data.get('steps', []), 1):
                        TestStep.objects.create(
                            test_case=tc,
                            step_number=idx,
                            description=step_desc,
                            expected_result=expected
                        )
                    count += 1
        
        return count

    def _get_test_cases_data(self):
        return [
            ('用户认证模块-忘记密码', [
                {
                    'title': '忘记密码-页面加载-正常显示',
                    'priority': 'p0',
                    'precondition': '用户访问忘记密码页面',
                    'steps': [
                        ('打开忘记密码页面URL', '页面加载完成'),
                        ('检查页面元素', '显示Logo、邮箱输入框、发送按钮、返回登录链接'),
                    ],
                    'tags': ['忘记密码', 'UI'],
                },
                {
                    'title': '忘记密码-输入已注册邮箱-发送成功',
                    'priority': 'p0',
                    'precondition': '邮箱已注册',
                    'steps': [
                        ('打开忘记密码页面', '页面正常显示'),
                        ('输入已注册的邮箱地址', '邮箱输入框显示输入内容'),
                        ('点击发送按钮', '显示成功提示"重置密码链接已发送到您的邮箱"'),
                    ],
                    'tags': ['忘记密码', '正向'],
                },
                {
                    'title': '忘记密码-输入未注册邮箱-显示错误提示',
                    'priority': 'p1',
                    'precondition': '邮箱未注册',
                    'steps': [
                        ('打开忘记密码页面', '页面正常显示'),
                        ('输入未注册的邮箱地址', '邮箱输入框显示输入内容'),
                        ('点击发送按钮', '显示错误提示"邮箱未注册"'),
                    ],
                    'tags': ['忘记密码', '逆向'],
                },
                {
                    'title': '忘记密码-邮箱格式错误-显示错误提示',
                    'priority': 'p1',
                    'precondition': '无前置条件',
                    'steps': [
                        ('打开忘记密码页面', '页面正常显示'),
                        ('输入无效格式的邮箱(如invalid-email)', '邮箱输入框显示输入内容'),
                        ('点击发送按钮', '显示错误提示"邮箱格式不正确"'),
                    ],
                    'tags': ['忘记密码', '逆向'],
                },
                {
                    'title': '忘记密码-邮箱为空-显示错误提示',
                    'priority': 'p1',
                    'precondition': '无前置条件',
                    'steps': [
                        ('打开忘记密码页面', '页面正常显示'),
                        ('邮箱输入框留空', '邮箱输入框为空'),
                        ('点击发送按钮', '显示错误提示"邮箱不能为空"'),
                    ],
                    'tags': ['忘记密码', '逆向'],
                },
                {
                    'title': '忘记密码-点击返回登录-跳转登录页面',
                    'priority': 'p2',
                    'precondition': '无前置条件',
                    'steps': [
                        ('打开忘记密码页面', '页面正常显示'),
                        ('点击"返回登录"链接', '页面跳转'),
                        ('检查跳转结果', '跳转到登录页面'),
                    ],
                    'tags': ['忘记密码', '导航'],
                },
            ]),
            ('用户认证模块-用户信息组件', [
                {
                    'title': '用户信息组件-显示用户信息',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('查看右上角用户信息区域', '显示用户头像和用户名'),
                    ],
                    'tags': ['用户信息', 'UI'],
                },
                {
                    'title': '用户信息组件-点击头像展开下拉菜单',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('点击用户头像', '显示下拉菜单'),
                        ('检查菜单项', '显示个人中心、账户设置、退出登录选项'),
                    ],
                    'tags': ['用户信息', '交互'],
                },
                {
                    'title': '用户信息组件-点击个人中心-跳转个人账户页面',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('点击用户头像', '显示下拉菜单'),
                        ('点击"个人中心"', '页面跳转'),
                        ('检查跳转结果', '跳转到个人账户页面'),
                    ],
                    'tags': ['用户信息', '导航'],
                },
                {
                    'title': '用户信息组件-点击退出登录-退出成功',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('点击用户头像', '显示下拉菜单'),
                        ('点击"退出登录"', '退出成功'),
                        ('检查页面跳转', '跳转到登录页面'),
                    ],
                    'tags': ['用户信息', '登出'],
                },
                {
                    'title': '用户信息组件-未登录状态-不显示用户信息',
                    'priority': 'p1',
                    'precondition': '用户未登录',
                    'steps': [
                        ('访问任意页面（未登录状态）', '页面正常显示'),
                        ('检查右上角', '不显示用户头像和用户名'),
                    ],
                    'tags': ['用户信息', '状态'],
                },
            ]),
            ('项目管理模块-接口测试', [
                {
                    'title': '接口测试-页面加载-正常显示',
                    'priority': 'p0',
                    'precondition': '用户已登录且是项目成员',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('进入项目的接口测试页面', '页面加载完成'),
                        ('检查页面元素', '显示接口集合树、请求编辑器、响应区域'),
                    ],
                    'tags': ['接口测试', 'UI'],
                },
                {
                    'title': '接口测试-创建接口集合成功',
                    'priority': 'p1',
                    'precondition': '用户有创建权限',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('点击新建集合按钮', '显示创建对话框'),
                        ('输入集合名称', '名称输入正确'),
                        ('点击确认按钮', '集合创建成功，树更新'),
                    ],
                    'tags': ['接口测试', '集合管理'],
                },
                {
                    'title': '接口测试-发送GET请求成功',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('选择GET方法', '方法选择正确'),
                        ('输入有效的请求URL', 'URL输入正确'),
                        ('点击发送按钮', '请求发送成功'),
                        ('检查响应区域', '显示响应状态码和响应体'),
                    ],
                    'tags': ['接口测试', '请求'],
                },
                {
                    'title': '接口测试-发送POST请求成功',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('选择POST方法', '方法选择正确'),
                        ('输入请求URL', 'URL输入正确'),
                        ('填写请求体(JSON格式)', '请求体填写正确'),
                        ('点击发送按钮', '请求发送成功'),
                        ('检查响应区域', '显示响应状态码和响应体'),
                    ],
                    'tags': ['接口测试', '请求'],
                },
                {
                    'title': '接口测试-请求超时处理',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('输入会超时的URL', 'URL输入正确'),
                        ('点击发送按钮', '请求发送'),
                        ('等待超时', '显示请求超时错误提示'),
                    ],
                    'tags': ['接口测试', '错误处理'],
                },
                {
                    'title': '接口测试-添加断言成功',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('切换到断言标签', '显示断言编辑区域'),
                        ('添加状态码断言(如200)', '断言添加成功'),
                        ('点击保存按钮', '断言保存成功'),
                    ],
                    'tags': ['接口测试', '断言'],
                },
                {
                    'title': '接口测试-断言验证失败',
                    'priority': 'p1',
                    'precondition': '已配置断言',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('发送请求', '请求返回'),
                        ('检查断言结果', '断言验证失败，显示失败原因'),
                    ],
                    'tags': ['接口测试', '断言', '逆向'],
                },
                {
                    'title': '接口测试-关联测试用例成功',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('选择一个接口', '接口选中'),
                        ('点击关联用例按钮', '显示用例选择对话框'),
                        ('选择要关联的用例', '用例选中'),
                        ('点击确认按钮', '关联成功'),
                    ],
                    'tags': ['接口测试', '关联'],
                },
                {
                    'title': '接口测试-删除接口集合成功',
                    'priority': 'p1',
                    'precondition': '用户有删除权限',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('右键点击要删除的集合', '显示上下文菜单'),
                        ('点击删除按钮', '显示确认对话框'),
                        ('点击确认按钮', '集合删除成功'),
                    ],
                    'tags': ['接口测试', '集合管理'],
                },
                {
                    'title': '接口测试-删除有子项的集合-显示错误提示',
                    'priority': 'p2',
                    'precondition': '集合下有接口或子集合',
                    'steps': [
                        ('进入接口测试页面', '页面正常显示'),
                        ('右键点击有子项的集合', '显示上下文菜单'),
                        ('点击删除按钮', '显示错误提示"请先删除子项"'),
                    ],
                    'tags': ['接口测试', '集合管理', '逆向'],
                },
            ]),
            ('项目管理模块-项目导航', [
                {
                    'title': '项目导航-显示导航菜单',
                    'priority': 'p0',
                    'precondition': '用户已登录且是项目成员',
                    'steps': [
                        ('登录系统', '登录成功'),
                        ('进入项目详情页面', '页面加载完成'),
                        ('检查左侧导航', '显示测试用例、接口测试、测试计划、测试报告等菜单项'),
                    ],
                    'tags': ['项目导航', 'UI'],
                },
                {
                    'title': '项目导航-菜单项点击跳转',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入项目详情页面', '页面加载完成'),
                        ('点击"测试用例"菜单', '跳转到测试用例页面'),
                        ('点击"接口测试"菜单', '跳转到接口测试页面'),
                        ('点击"成员管理"菜单', '跳转到成员管理页面'),
                    ],
                    'tags': ['项目导航', '导航'],
                },
                {
                    'title': '项目导航-当前页面高亮',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入项目详情页面', '页面加载完成'),
                        ('点击"测试用例"菜单', '跳转到测试用例页面'),
                        ('检查导航菜单', '"测试用例"菜单项高亮显示'),
                    ],
                    'tags': ['项目导航', '状态'],
                },
                {
                    'title': '项目导航-权限不足隐藏菜单项',
                    'priority': 'p1',
                    'precondition': '用户权限不足',
                    'steps': [
                        ('以普通成员身份登录', '登录成功'),
                        ('进入项目详情页面', '页面加载完成'),
                        ('检查左侧导航', '管理功能菜单项隐藏'),
                    ],
                    'tags': ['项目导航', '权限'],
                },
            ]),
            ('测试用例管理模块-用例筛选', [
                {
                    'title': '用例筛选-关键词搜索成功',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('在搜索框输入关键词', '搜索框显示输入内容'),
                        ('检查用例列表', '显示匹配关键词的用例'),
                    ],
                    'tags': ['用例筛选', '搜索'],
                },
                {
                    'title': '用例筛选-关键词搜索无结果',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('在搜索框输入不存在的关键词', '搜索框显示输入内容'),
                        ('检查用例列表', '显示空状态提示'),
                    ],
                    'tags': ['用例筛选', '搜索', '逆向'],
                },
                {
                    'title': '用例筛选-按优先级筛选',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择优先级筛选条件(P0)', '筛选条件设置成功'),
                        ('检查用例列表', '只显示P0优先级的用例'),
                    ],
                    'tags': ['用例筛选', '筛选'],
                },
                {
                    'title': '用例筛选-按状态筛选',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择状态筛选条件', '筛选条件设置成功'),
                        ('检查用例列表', '只显示对应状态的用例'),
                    ],
                    'tags': ['用例筛选', '筛选'],
                },
                {
                    'title': '用例筛选-重置筛选条件',
                    'priority': 'p1',
                    'precondition': '已设置筛选条件',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('设置多个筛选条件', '筛选条件设置成功'),
                        ('点击重置按钮', '所有筛选条件清空'),
                        ('检查用例列表', '显示全部用例'),
                    ],
                    'tags': ['用例筛选', '重置'],
                },
            ]),
            ('测试用例管理模块-批量操作', [
                {
                    'title': '批量操作-显示批量操作工具栏',
                    'priority': 'p0',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('勾选多个用例', '用例被选中'),
                        ('检查页面底部', '显示批量操作工具栏'),
                    ],
                    'tags': ['批量操作', 'UI'],
                },
                {
                    'title': '批量操作-批量修改优先级成功',
                    'priority': 'p0',
                    'precondition': '用户已选择多个用例',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择多个用例', '用例被选中'),
                        ('点击批量修改按钮', '显示批量修改对话框'),
                        ('选择新优先级(P0)', '优先级选择正确'),
                        ('点击确认按钮', '批量修改成功'),
                    ],
                    'tags': ['批量操作', '修改'],
                },
                {
                    'title': '批量操作-批量修改状态成功',
                    'priority': 'p1',
                    'precondition': '用户已选择多个用例',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择多个用例', '用例被选中'),
                        ('点击批量修改按钮', '显示批量修改对话框'),
                        ('选择新状态', '状态选择正确'),
                        ('点击确认按钮', '批量修改成功'),
                    ],
                    'tags': ['批量操作', '修改'],
                },
                {
                    'title': '批量操作-批量复制成功',
                    'priority': 'p1',
                    'precondition': '用户已选择多个用例',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择多个用例', '用例被选中'),
                        ('点击批量复制按钮', '显示目标模块选择对话框'),
                        ('选择目标模块', '模块选择正确'),
                        ('点击确认按钮', '批量复制成功'),
                    ],
                    'tags': ['批量操作', '复制'],
                },
                {
                    'title': '批量操作-取消选择',
                    'priority': 'p1',
                    'precondition': '用户已选择多个用例',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择多个用例', '用例被选中'),
                        ('点击取消选择按钮', '选择状态清空'),
                        ('检查批量操作工具栏', '工具栏隐藏'),
                    ],
                    'tags': ['批量操作', '取消'],
                },
            ]),
            ('测试用例管理模块-导入导出', [
                {
                    'title': '导入导出-选择有效文件-文件上传成功',
                    'priority': 'p0',
                    'precondition': '用户有导入权限',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('点击导入按钮', '显示导入对话框'),
                        ('选择有效的Excel/CSV文件', '文件选择成功'),
                        ('检查文件预览', '显示文件数据预览'),
                    ],
                    'tags': ['导入导出', '导入'],
                },
                {
                    'title': '导入导出-文件格式错误-显示错误提示',
                    'priority': 'p1',
                    'precondition': '用户有导入权限',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('点击导入按钮', '显示导入对话框'),
                        ('选择不支持格式的文件(如.txt)', '文件选择成功'),
                        ('检查错误提示', '显示"不支持的文件格式"错误提示'),
                    ],
                    'tags': ['导入导出', '导入', '逆向'],
                },
                {
                    'title': '导入导出-文件过大-显示错误提示',
                    'priority': 'p1',
                    'precondition': '用户有导入权限',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('点击导入按钮', '显示导入对话框'),
                        ('选择超过大小限制的文件', '文件选择成功'),
                        ('检查错误提示', '显示"文件大小超过限制"错误提示'),
                    ],
                    'tags': ['导入导出', '导入', '逆向'],
                },
                {
                    'title': '导入导出-字段映射-自动映射成功',
                    'priority': 'p1',
                    'precondition': '已选择有效文件',
                    'steps': [
                        ('进入导入对话框', '对话框显示'),
                        ('上传文件后', '自动进行字段映射'),
                        ('检查映射结果', '字段正确映射到系统字段'),
                    ],
                    'tags': ['导入导出', '导入'],
                },
                {
                    'title': '导入导出-确认导入-导入成功',
                    'priority': 'p0',
                    'precondition': '已选择文件并完成映射',
                    'steps': [
                        ('进入导入对话框', '对话框显示'),
                        ('确认字段映射正确', '映射正确'),
                        ('点击确认导入按钮', '开始导入'),
                        ('检查导入结果', '显示导入成功数量，用例列表更新'),
                    ],
                    'tags': ['导入导出', '导入'],
                },
                {
                    'title': '导入导出-导出用例成功',
                    'priority': 'p0',
                    'precondition': '用户有导出权限',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('点击导出按钮', '显示导出选项'),
                        ('选择导出格式(Excel)', '格式选择正确'),
                        ('点击确认按钮', '文件下载成功'),
                    ],
                    'tags': ['导入导出', '导出'],
                },
                {
                    'title': '导入导出-导出选中用例成功',
                    'priority': 'p1',
                    'precondition': '用户已选择用例',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('选择要导出的用例', '用例被选中'),
                        ('点击导出选中按钮', '显示导出选项'),
                        ('点击确认按钮', '选中用例导出成功'),
                    ],
                    'tags': ['导入导出', '导出'],
                },
                {
                    'title': '导入导出-下载导入模板成功',
                    'priority': 'p1',
                    'precondition': '用户已登录',
                    'steps': [
                        ('进入测试用例页面', '页面加载完成'),
                        ('点击导入按钮', '显示导入对话框'),
                        ('点击下载模板链接', '模板文件下载成功'),
                    ],
                    'tags': ['导入导出', '模板'],
                },
            ]),
        ]
