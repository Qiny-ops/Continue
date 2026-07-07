"""
生成测试数据

数据关系：
  Role -> User (system_role)
  User -> Project (owner, created_by)
  Project -> ProjectMember (project)
  Project -> ProjectRole (project)
  Project -> TestCaseRepository (project)
  TestCaseRepository -> TestCaseVersion (repository)
  TestCaseVersion -> TestModule (version, parent自引用)
  TestModule -> TestCase (module)
  TestCaseVersion -> TestCase (version)
  TestCase -> TestCaseReview (test_case)
  TestCase -> TestCaseExecution (test_case)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import Role, User
from apps.projects.models import Project, ProjectMember, ProjectRole
from apps.testcase.models import (
    TestCaseRepository, TestCaseVersion, TestModule,
    TestCase, TestCaseReview, TestCaseExecution
)


class Command(BaseCommand):
    help = '生成测试数据'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('开始生成测试数据')
        self.stdout.write('=' * 50)

        roles = self._create_roles()
        users = self._create_users(roles)
        projects = self._create_projects(users)
        self._create_project_members(projects, users)
        self._create_project_roles(projects)
        repos, versions = self._create_repos_versions(projects, users)
        modules = self._create_modules(versions)
        cases = self._create_test_cases(versions, modules, users)
        self._create_reviews(cases, users)
        self._create_executions(cases, users)

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('测试数据生成完成！')
        self.stdout.write('=' * 50)
        self.stdout.write(f'\n数据统计:')
        self.stdout.write(f'  角色: {Role.objects.count()} 条')
        self.stdout.write(f'  用户: {User.objects.count()} 条')
        self.stdout.write(f'  项目: {Project.objects.count()} 条')
        self.stdout.write(f'  项目成员: {ProjectMember.objects.count()} 条')
        self.stdout.write(f'  项目角色: {ProjectRole.objects.count()} 条')
        self.stdout.write(f'  用例库: {TestCaseRepository.objects.count()} 条')
        self.stdout.write(f'  版本: {TestCaseVersion.objects.count()} 条')
        self.stdout.write(f'  模块: {TestModule.objects.count()} 条')
        self.stdout.write(f'  测试用例: {TestCase.objects.count()} 条')
        self.stdout.write(f'  评审记录: {TestCaseReview.objects.count()} 条')
        self.stdout.write(f'  执行记录: {TestCaseExecution.objects.count()} 条')

    def _create_roles(self):
        self.stdout.write('\n[1/8] 创建角色...')
        roles = {}
        role_data = [
            ('admin', '系统管理员', 'system', '系统最高权限角色'),
            ('tester', '测试人员', 'default', '负责测试执行和用例编写'),
            ('developer', '开发人员', 'default', '负责功能开发'),
            ('viewer', '访客', 'default', '只读查看权限'),
        ]
        for code, name, rtype, desc in role_data:
            role, _ = Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'type': rtype, 'description': desc, 'status': 'active'}
            )
            roles[code] = role
        self.stdout.write(f'  创建角色: {list(roles.keys())}')
        return roles

    def _create_users(self, roles):
        self.stdout.write('\n[2/8] 创建用户...')
        users = {}
        user_data = [
            ('admin', 'admin@example.com', 'Admin123!', '张管理', '测试总监', 'admin'),
            ('zhangsan', 'zhangsan@example.com', 'Test1234!', '张三', '高级测试工程师', 'tester'),
            ('lisi', 'lisi@example.com', 'Test1234!', '李四', '测试工程师', 'tester'),
            ('wangwu', 'wangwu@example.com', 'Dev12345!', '王五', '前端开发工程师', 'developer'),
            ('zhaoliu', 'zhaoliu@example.com', 'View1234!', '赵六', '产品经理', 'viewer'),
        ]
        for username, email, password, name, title, role_code in user_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'name': name,
                    'title': title,
                    'system_role': roles[role_code],
                    'status': 'active',
                }
            )
            if created:
                user.set_password(password)
                user.save()
            users[username] = user
        self.stdout.write(f'  创建用户: {list(users.keys())}')
        return users

    def _create_projects(self, users):
        self.stdout.write('\n[3/8] 创建项目...')
        projects = {}
        project_data = [
            ('电商平台', 'ecommerce', 'web', '大型B2C电商平台，包含用户、商品、订单、支付等模块'),
            ('OA办公系统', 'oa-system', 'web', '企业内部办公自动化系统，包含考勤、审批、文档等模块'),
        ]
        for name, code, ptype, desc in project_data:
            project, _ = Project.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'identifier': code,
                    'description': desc,
                    'type': ptype,
                    'status': 'active',
                    'visibility': 'private',
                    'icon': 'Folder',
                    'icon_color': '#409EFF',
                    'owner': users['admin'],
                    'created_by': users['admin'],
                }
            )
            projects[code] = project
        self.stdout.write(f'  创建项目: {list(projects.keys())}')
        return projects

    def _create_project_members(self, projects, users):
        self.stdout.write('\n[4/8] 创建项目成员和角色权限...')
        member_data = [
            ('ecommerce', 'admin', 'admin'),
            ('ecommerce', 'zhangsan', 'tester'),
            ('ecommerce', 'lisi', 'tester'),
            ('ecommerce', 'wangwu', 'developer'),
            ('ecommerce', 'zhaoliu', 'viewer'),
            ('oa-system', 'admin', 'admin'),
            ('oa-system', 'zhangsan', 'tester'),
            ('oa-system', 'lisi', 'tester'),
        ]
        count = 0
        for project_code, username, role in member_data:
            _, created = ProjectMember.objects.get_or_create(
                project=projects[project_code],
                user=users[username],
                defaults={'role': role, 'status': 'active'}
            )
            if created:
                count += 1
        self.stdout.write(f'  创建项目成员: {count} 条')

    def _create_project_roles(self, projects):
        role_permissions = {
            'admin': ['project_manage', 'testcase_manage', 'testcase_view', 'execution_manage', 'member_manage'],
            'developer': ['testcase_view', 'execution_view'],
            'tester': ['testcase_manage', 'testcase_view', 'execution_manage', 'execution_view'],
            'viewer': ['testcase_view', 'execution_view'],
        }
        count = 0
        for project in projects.values():
            for role_key, perms in role_permissions.items():
                _, created = ProjectRole.objects.get_or_create(
                    project=project,
                    role_key=role_key,
                    defaults={'permissions': perms}
                )
                if created:
                    count += 1
        self.stdout.write(f'  创建项目角色权限: {count} 条')

    def _create_repos_versions(self, projects, users):
        self.stdout.write('\n[5/8] 创建用例库和版本...')
        repos = {}
        versions = {}
        repo_data = [
            ('ecommerce', '电商平台-用例库', '电商平台全量测试用例库'),
            ('oa-system', 'OA系统-用例库', 'OA办公系统全量测试用例库'),
        ]
        for project_code, name, desc in repo_data:
            repo, _ = TestCaseRepository.objects.get_or_create(
                name=name,
                defaults={
                    'project': projects[project_code],
                    'description': desc,
                    'is_default': True,
                    'created_by': users['admin'],
                }
            )
            repos[project_code] = repo

        version_data = [
            ('ecommerce', 'V3.2', '当前开发版本', True, 'active'),
            ('ecommerce', 'V3.1', '已发布稳定版本', False, 'active'),
            ('oa-system', 'V2.0', '当前开发版本', True, 'active'),
            ('oa-system', 'V1.5', '已归档版本', False, 'archived'),
        ]
        for project_code, name, desc, is_default, status in version_data:
            version, _ = TestCaseVersion.objects.get_or_create(
                repository=repos[project_code],
                name=name,
                defaults={
                    'description': desc,
                    'is_default': is_default,
                    'status': status,
                    'created_by': users['admin'],
                }
            )
            versions[f'{project_code}_{name}'] = version
        self.stdout.write(f'  创建用例库: {len(repos)} 个, 版本: {len(versions)} 个')
        return repos, versions

    def _create_modules(self, versions):
        self.stdout.write('\n[6/8] 创建模块...')
        modules = {}
        module_data = [
            ('ecommerce_V3.2', None, '用户模块', 1),
            ('ecommerce_V3.2', None, '商品模块', 2),
            ('ecommerce_V3.2', None, '订单模块', 3),
            ('ecommerce_V3.2', None, '支付模块', 4),
            ('ecommerce_V3.2', '用户模块', '注册登录', 1),
            ('ecommerce_V3.2', '用户模块', '个人信息', 2),
            ('ecommerce_V3.2', '商品模块', '商品搜索', 1),
            ('ecommerce_V3.2', '商品模块', '商品详情', 2),
            ('ecommerce_V3.2', '订单模块', '下单流程', 1),
            ('ecommerce_V3.2', '订单模块', '订单管理', 2),
            ('oa-system_V2.0', None, '考勤模块', 1),
            ('oa-system_V2.0', None, '审批模块', 2),
            ('oa-system_V2.0', None, '文档模块', 3),
            ('oa-system_V2.0', '考勤模块', '打卡功能', 1),
            ('oa-system_V2.0', '考勤模块', '请假功能', 2),
            ('oa-system_V2.0', '审批模块', '请假审批', 1),
            ('oa-system_V2.0', '审批模块', '报销审批', 2),
        ]

        parent_modules = {}
        for version_key, parent_name, name, sort_order in module_data:
            version = versions[version_key]
            parent = parent_modules.get(f'{version_key}_{parent_name}') if parent_name else None
            module, _ = TestModule.objects.get_or_create(
                version=version,
                name=name,
                parent=parent,
                defaults={'sort_order': sort_order}
            )
            modules[f'{version_key}_{name}'] = module
            if not parent_name:
                parent_modules[f'{version_key}_{name}'] = module
        self.stdout.write(f'  创建模块: {len(modules)} 个')
        return modules

    def _create_test_cases(self, versions, modules, users):
        self.stdout.write('\n[7/8] 创建测试用例...')
        cases = []
        case_data = [
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_注册登录',
                'title': '用户名密码正常登录',
                'priority': 'p0',
                'precondition': '1. 系统已部署\n2. 测试账号已创建: testuser/Test1234',
                'steps': '1. 打开登录页面\n2. 输入用户名: testuser\n3. 输入密码: Test1234\n4. 点击「登录」按钮',
                'expected_result': '1. 登录页面正常展示\n2. 用户名输入框可正常输入\n3. 密码输入框以密文形式显示\n4. 登录成功，跳转至首页，右上角显示用户头像和昵称',
                'tags': ['登录', '冒烟测试'],
                'automation_status': 'automated',
                'automation_case_id': 'TC-AUTO-001',
                'requirement': 'REQ-LOGIN-001',
                'estimated_hours': 0.50,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_注册登录',
                'title': '密码错误登录失败',
                'priority': 'p1',
                'precondition': '1. 系统已部署\n2. 测试账号已创建: testuser/Test1234',
                'steps': '1. 打开登录页面\n2. 输入用户名: testuser\n3. 输入错误密码: WrongPass\n4. 点击「登录」按钮',
                'expected_result': '1. 登录页面正常展示\n2. 用户名输入框可正常输入\n3. 密码输入框以密文形式显示\n4. 登录失败，提示"用户名或密码错误"',
                'tags': ['登录', '异常测试'],
                'automation_status': 'automated',
                'automation_case_id': 'TC-AUTO-002',
                'requirement': 'REQ-LOGIN-002',
                'estimated_hours': 0.25,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_注册登录',
                'title': '登录密码连续错误3次锁定账户',
                'priority': 'p1',
                'precondition': '1. 系统已部署\n2. 测试账号已创建: lockuser/Test1234\n3. 账户未被锁定',
                'steps': '1. 打开登录页面\n2. 输入用户名: lockuser，输入错误密码，点击登录\n3. 再次输入错误密码，点击登录\n4. 第三次输入错误密码，点击登录\n5. 使用正确密码尝试登录',
                'expected_result': '1. 第一次错误提示"用户名或密码错误"\n2. 第二次错误提示"用户名或密码错误，还剩1次机会"\n3. 第三次错误提示"账户已锁定，请30分钟后重试"\n4. 使用正确密码也无法登录，提示"账户已锁定"',
                'tags': ['登录', '异常测试', '安全'],
                'automation_status': 'not_automated',
                'requirement': 'REQ-LOGIN-003',
                'estimated_hours': 1.00,
                'created_by': 'zhangsan',
                'updated_by': 'lisi',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_个人信息',
                'title': '个人中心下拉菜单显示验证',
                'priority': 'p1',
                'precondition': '1. 已登录系统\n2. 用户有个人中心权限',
                'steps': '1. 登录系统\n2. 进入个人中心页面\n3. 点击个人中心下拉菜单\n4. 检查菜单选项',
                'expected_result': '1. 登录成功，跳转至首页\n2. 个人中心页面正常展示\n3. 下拉菜单成功展开\n4. 菜单包含"我要请假"选项，文字清晰可点击',
                'tags': ['个人中心'],
                'automation_status': 'not_analyzed',
                'requirement': 'REQ-PROFILE-001',
                'estimated_hours': 0.25,
                'created_by': 'lisi',
                'updated_by': 'lisi',
                'review_status': 'pending',
                'generation_source': 'ai_generated',
                'ai_request_id': 'REQ-AI-20260515-001',
                'ai_model_version': 'gpt-4o',
                'ai_confidence': 0.72,
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_商品搜索',
                'title': '关键词搜索商品',
                'priority': 'p0',
                'precondition': '1. 已登录系统\n2. 商品库中有测试数据',
                'steps': '1. 进入商品列表页\n2. 在搜索框输入"iPhone 15"\n3. 点击搜索按钮\n4. 查看搜索结果',
                'expected_result': '1. 商品列表页正常展示\n2. 搜索框可正常输入\n3. 触发搜索请求\n4. 结果列表展示包含"iPhone 15"关键词的商品，按相关度排序',
                'tags': ['商品', '搜索', '冒烟测试'],
                'automation_status': 'automated',
                'automation_case_id': 'TC-AUTO-003',
                'requirement': 'REQ-SEARCH-001',
                'estimated_hours': 0.50,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_商品详情',
                'title': '商品详情页展示验证',
                'priority': 'p1',
                'precondition': '1. 已登录系统\n2. 商品库中有测试商品',
                'steps': '1. 进入商品列表页\n2. 点击任意商品卡片\n3. 检查商品详情页各区域',
                'expected_result': '1. 商品列表正常展示\n2. 跳转至商品详情页\n3. 商品图片、名称、价格、库存、描述、规格参数均正常展示',
                'tags': ['商品'],
                'automation_status': 'not_automated',
                'requirement': 'REQ-PRODUCT-001',
                'estimated_hours': 0.50,
                'created_by': 'lisi',
                'updated_by': 'lisi',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_下单流程',
                'title': '正常下单流程',
                'priority': 'p0',
                'precondition': '1. 已登录系统\n2. 购物车中有商品\n3. 收货地址已配置',
                'steps': '1. 进入购物车页面\n2. 勾选要购买的商品\n3. 点击"去结算"\n4. 确认收货地址\n5. 选择支付方式\n6. 提交订单',
                'expected_result': '1. 购物车页面正常展示\n2. 商品可勾选\n3. 跳转至订单确认页\n4. 收货地址正确展示\n5. 支付方式可选\n6. 订单创建成功，跳转至支付页面',
                'tags': ['订单', '冒烟测试'],
                'automation_status': 'not_automated',
                'requirement': 'REQ-ORDER-001',
                'estimated_hours': 1.00,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'ecommerce_V3.2',
                'module_key': 'ecommerce_V3.2_订单管理',
                'title': '订单列表筛选和分页',
                'priority': 'p2',
                'precondition': '1. 已登录系统\n2. 有历史订单数据',
                'steps': '1. 进入"我的订单"页面\n2. 选择"待发货"状态筛选\n3. 切换到第2页\n4. 按下单时间排序',
                'expected_result': '1. 订单列表正常展示\n2. 仅显示待发货状态的订单\n3. 第2页数据正常加载\n4. 订单按时间倒序排列',
                'tags': ['订单'],
                'automation_status': 'not_analyzed',
                'requirement': 'REQ-ORDER-002',
                'estimated_hours': 0.50,
                'created_by': 'lisi',
                'updated_by': 'lisi',
                'review_status': 'pending',
                'generation_source': 'manual',
            },
            {
                'version_key': 'oa-system_V2.0',
                'module_key': 'oa-system_V2.0_打卡功能',
                'title': '上班打卡-正常打卡',
                'priority': 'p0',
                'precondition': '1. 已登录OA系统\n2. 当前时间在工作时间内\n3. 当天未打卡',
                'steps': '1. 进入考勤打卡页面\n2. 点击"上班打卡"按钮\n3. 确认打卡信息',
                'expected_result': '1. 考勤页面正常展示，显示当前时间和打卡状态\n2. 打卡成功，显示打卡时间\n3. 打卡记录保存成功，状态显示"正常"',
                'tags': ['考勤', '冒烟测试'],
                'automation_status': 'automated',
                'automation_case_id': 'TC-AUTO-OA-001',
                'requirement': 'REQ-ATT-001',
                'estimated_hours': 0.25,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'oa-system_V2.0',
                'module_key': 'oa-system_V2.0_请假功能',
                'title': '提交请假申请',
                'priority': 'p1',
                'precondition': '1. 已登录OA系统\n2. 有剩余年假天数',
                'steps': '1. 进入请假申请页面\n2. 选择请假类型: 年假\n3. 选择开始日期和结束日期\n4. 填写请假原因\n5. 点击提交',
                'expected_result': '1. 请假页面正常展示\n2. 请假类型下拉可选\n3. 日期选择器正常工作\n4. 请假原因可正常输入\n5. 提交成功，跳转至请假记录页面，状态为"待审批"',
                'tags': ['请假'],
                'automation_status': 'not_automated',
                'requirement': 'REQ-LEAVE-001',
                'estimated_hours': 0.50,
                'created_by': 'lisi',
                'updated_by': 'lisi',
                'review_status': 'approved',
                'generation_source': 'manual',
            },
            {
                'version_key': 'oa-system_V2.0',
                'module_key': 'oa-system_V2.0_请假审批',
                'title': '审批通过请假申请',
                'priority': 'p1',
                'precondition': '1. 已登录OA系统\n2. 有待审批的请假申请',
                'steps': '1. 进入审批列表页面\n2. 点击待审批的请假申请\n3. 查看请假详情\n4. 点击"通过"按钮\n5. 填写审批意见\n6. 确认审批',
                'expected_result': '1. 审批列表展示待审批记录\n2. 请假详情正常展示\n3. 请假信息完整准确\n4. 弹出审批确认框\n5. 审批意见可正常输入\n6. 审批通过，状态变为"已通过"，申请人收到通知',
                'tags': ['审批'],
                'automation_status': 'not_analyzed',
                'requirement': 'REQ-APPROVAL-001',
                'estimated_hours': 0.50,
                'created_by': 'zhangsan',
                'updated_by': 'zhangsan',
                'review_status': 'pending',
                'generation_source': 'ai_generated',
                'ai_request_id': 'REQ-AI-20260515-002',
                'ai_model_version': 'gpt-4o',
                'ai_confidence': 0.85,
            },
            {
                'version_key': 'oa-system_V2.0',
                'module_key': 'oa-system_V2.0_报销审批',
                'title': '驳回报销申请-金额超限',
                'priority': 'p2',
                'precondition': '1. 已登录OA系统\n2. 有待审批的报销申请\n3. 报销金额超过审批人权限',
                'steps': '1. 进入审批列表页面\n2. 点击待审批的报销申请\n3. 检查报销金额\n4. 点击"驳回"按钮\n5. 填写驳回原因: 金额超限\n6. 确认驳回',
                'expected_result': '1. 审批列表展示待审批记录\n2. 报销详情正常展示\n3. 报销金额显示红色超限标识\n4. 弹出驳回确认框\n5. 驳回原因为必填项\n6. 驳回成功，状态变为"已驳回"，申请人收到通知',
                'tags': ['审批', '报销'],
                'automation_status': 'not_analyzed',
                'requirement': 'REQ-APPROVAL-002',
                'estimated_hours': 0.50,
                'created_by': 'lisi',
                'updated_by': 'lisi',
                'review_status': 'rejected',
                'generation_source': 'manual',
            },
        ]

        for data in case_data:
            version = versions[data.pop('version_key')]
            module = modules.get(data.pop('module_key'))
            created_by = users[data.pop('created_by')]
            updated_by = users[data.pop('updated_by')]
            case = TestCase.objects.create(
                version=version,
                module=module,
                created_by=created_by,
                updated_by=updated_by,
                **data,
            )
            cases.append(case)
        self.stdout.write(f'  创建测试用例: {len(cases)} 条')
        return cases

    def _create_reviews(self, cases, users):
        self.stdout.write('\n[8/8] 创建评审和执行记录...')
        reviews = []
        review_data = [
            (0, 'admin', 'approved', '用例编写规范，步骤清晰'),
            (1, 'admin', 'approved', '异常场景覆盖到位'),
            (2, 'admin', 'approved', '安全相关用例，建议增加解锁后的验证'),
            (3, 'zhangsan', 'pending', ''),
            (4, 'admin', 'approved', '冒烟用例，步骤完整'),
            (5, 'zhangsan', 'approved', '展示验证通过'),
            (6, 'admin', 'approved', '核心流程用例，覆盖全面'),
            (7, 'zhangsan', 'pending', ''),
            (8, 'admin', 'approved', '打卡功能用例通过'),
            (9, 'zhangsan', 'approved', '请假流程覆盖完整'),
            (10, 'admin', 'pending', ''),
            (11, 'zhangsan', 'rejected', '驳回原因不够具体，需补充超限阈值说明'),
        ]
        for case_idx, reviewer_key, status, comment in review_data:
            if case_idx < len(cases):
                review = TestCaseReview.objects.create(
                    test_case=cases[case_idx],
                    reviewer=users[reviewer_key],
                    status=status,
                    comment=comment,
                )
                reviews.append(review)
        self.stdout.write(f'  创建评审记录: {len(reviews)} 条')
        return reviews

    def _create_executions(self, cases, users):
        executions = []
        execution_data = [
            (0, 'zhangsan', 'pass', '登录成功，跳转正常', ''),
            (1, 'zhangsan', 'pass', '错误提示正确显示', ''),
            (2, 'lisi', 'fail', '第三次错误后未显示剩余机会提示', 'Bug-001: 错误次数提示文案缺失'),
            (4, 'zhangsan', 'pass', '搜索结果准确', ''),
            (5, 'lisi', 'pass', '详情页展示正常', ''),
            (6, 'zhangsan', 'pass', '下单流程通畅', ''),
            (8, 'zhangsan', 'pass', '打卡成功', ''),
            (9, 'lisi', 'pass', '请假提交成功', ''),
        ]
        for case_idx, executor_key, result, actual_result, remark in execution_data:
            if case_idx < len(cases):
                execution = TestCaseExecution.objects.create(
                    test_case=cases[case_idx],
                    executed_by=users[executor_key],
                    result=result,
                    actual_result=actual_result,
                    remark=remark,
                )
                executions.append(execution)
        self.stdout.write(f'  创建执行记录: {len(executions)} 条')
        return executions
