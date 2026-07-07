"""
生成测试用例管理系统的测试数据
根据实际业务场景生成：用户、角色、项目、用例库、版本、模块、测试用例等
"""

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.projects.models import Project, ProjectMember, ProjectRole
from apps.testcase.models import (
    TestCaseRepository,
    TestCaseVersion,
    TestModule,
    TestCase,
    TestStep,
    TestCaseReview,
    TestCaseExecution
)
from apps.users.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '生成测试用例管理系统的测试数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='清除现有数据后重新生成',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始生成测试数据...'))
        
        if options.get('clean'):
            self.clean_data()
        
        self.create_roles_and_permissions()
        users = self.create_users()
        projects = self.create_projects(users)
        self.create_project_members(projects, users)
        self.create_project_roles(projects)
        
        for project in projects:
            self.create_repositories_and_testcases(project, users)
        
        self.stdout.write(self.style.SUCCESS('\n测试数据生成完成！'))
        self.print_summary(users, projects)

    def clean_data(self):
        """清除现有数据"""
        self.stdout.write(self.style.WARNING('清除现有数据...'))
        TestCaseExecution.objects.all().delete()
        TestCaseReview.objects.all().delete()
        TestStep.objects.all().delete()
        TestCase.objects.all().delete()
        TestModule.objects.all().delete()
        TestCaseVersion.objects.all().delete()
        TestCaseRepository.objects.all().delete()
        ProjectMember.objects.all().delete()
        ProjectRole.objects.all().delete()
        Project.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('数据清除完成'))

    def create_roles_and_permissions(self):
        """创建系统角色 - 简化为 admin 和 user"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('创建系统角色...'))

        roles_data = [
            {'name': '系统管理员', 'code': 'admin', 'type': 'system'},
            {'name': '普通用户', 'code': 'user', 'type': 'default'},
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'type': role_data['type'],
                    'status': 'active'
                }
            )
            if created:
                self.stdout.write(f'  [OK] 创建角色: {role.name}')

    def create_users(self):
        """创建测试用户"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('创建测试用户...'))

        users_data = [
            {'username': 'admin', 'name': '系统管理员', 'role_code': 'admin', 'is_staff': True},
            {'username': 'user1', 'name': '张三', 'role_code': 'user'},
            {'username': 'user2', 'name': '李四', 'role_code': 'user'},
            {'username': 'user3', 'name': '王五', 'role_code': 'user'},
            {'username': 'user4', 'name': '赵六', 'role_code': 'user'},
            {'username': 'user5', 'name': '孙七', 'role_code': 'user'},
        ]

        users = {}
        for user_data in users_data:
            role = Role.objects.get(code=user_data['role_code'])
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'name': user_data['name'],
                    'email': f"{user_data['username']}@test.com",
                    'is_staff': user_data.get('is_staff', False),
                    'system_role': role,
                    'status': 'active'
                }
            )
            if created:
                user.set_password('test123456')
                user.save()
                self.stdout.write(f'  [OK] 创建用户: {user.name} ({user.username})')
            users[user_data['username']] = user
        
        return users

    def create_projects(self, users):
        """创建项目"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('创建项目...'))
        
        projects_data = [
            {
                'name': '电商平台系统',
                'code': 'ecommerce',
                'type': 'web',
                'status': 'active',
                'description': '综合性电商平台，包含用户端、商家后台、管理后台',
                'owner': 'test_manager',
                'created_by': 'test_manager'
            },
            {
                'name': '移动APP',
                'code': 'mobile_app',
                'type': 'mobile',
                'status': 'active',
                'description': 'iOS和Android移动应用程序',
                'owner': 'test_manager',
                'created_by': 'test_manager'
            },
            {
                'name': 'API网关服务',
                'code': 'api_gateway',
                'type': 'api',
                'status': 'active',
                'description': '微服务API网关和核心服务接口',
                'owner': 'pm1',
                'created_by': 'pm1'
            },
            {
                'name': '性能测试项目',
                'code': 'perf_test',
                'type': 'performance',
                'status': 'pending',
                'description': '系统性能测试和压力测试',
                'owner': 'tester1',
                'created_by': 'tester1'
            },
        ]
        
        projects = []
        for proj_data in projects_data:
            project, created = Project.objects.get_or_create(
                code=proj_data['code'],
                defaults={
                    'name': proj_data['name'],
                    'type': proj_data['type'],
                    'status': proj_data['status'],
                    'description': proj_data['description'],
                    'owner': users.get(proj_data['owner']),
                    'created_by': users.get(proj_data.get('created_by', proj_data['owner'])),
                    'visibility': 'public'
                }
            )
            if created:
                self.stdout.write(f'  [OK] 创建项目: {project.name}')
            projects.append(project)
        
        return projects

    def create_project_members(self, projects, users):
        """创建项目成员"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('创建项目成员...'))
        
        members_config = {
            'ecommerce': [
                ('test_manager', 'admin'),
                ('tester1', 'tester'),
                ('tester2', 'tester'),
                ('developer1', 'developer'),
                ('developer2', 'developer'),
                ('pm1', 'viewer'),
            ],
            'mobile_app': [
                ('test_manager', 'admin'),
                ('tester1', 'tester'),
                ('developer1', 'developer'),
            ],
            'api_gateway': [
                ('pm1', 'admin'),
                ('tester2', 'tester'),
                ('developer2', 'developer'),
            ],
            'perf_test': [
                ('tester1', 'admin'),
                ('tester2', 'tester'),
            ],
        }
        
        for project in projects:
            if project.code in members_config:
                for username, role in members_config[project.code]:
                    if username in users:
                        member, created = ProjectMember.objects.get_or_create(
                            project=project,
                            user=users[username],
                            defaults={'role': role, 'status': 'active'}
                        )
                        if created:
                            self.stdout.write(f'  [OK] 添加成员: {users[username].name} -> {project.name} ({role})')

    def create_project_roles(self, projects):
        """创建项目角色权限配置"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('创建项目角色权限...'))
        
        role_permissions = {
            'admin': ['project_manage', 'member_manage', 'testcase_manage', 'testcase_view', 'test_execute', 'report_view'],
            'developer': ['testcase_view', 'test_execute', 'report_view'],
            'tester': ['testcase_manage', 'testcase_view', 'test_execute', 'report_view'],
            'viewer': ['testcase_view', 'report_view'],
        }
        
        for project in projects:
            for role_key, perms in role_permissions.items():
                role, created = ProjectRole.objects.get_or_create(
                    project=project,
                    role_key=role_key,
                    defaults={'permissions': perms}
                )
                if created:
                    self.stdout.write(f'  [OK] 配置权限: {project.name} - {role_key}')

    def create_repositories_and_testcases(self, project, users):
        """创建用例库和测试用例"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'创建 {project.name} 的用例库...'))
        
        repo_configs = self.get_repo_configs(project)
        
        for repo_config in repo_configs:
            repo = self.create_repository(project, users, repo_config)
            versions = self.create_versions(repo, users)
            for version in versions:
                self.create_modules_and_cases(version, users, repo_config)

    def get_repo_configs(self, project):
        """根据项目类型返回用例库配置"""
        base_configs = {
            'web': [
                {
                    'name': 'Web前端',
                    'description': 'Web前端界面测试用例',
                    'modules': self.get_web_modules(),
                    'test_cases': self.get_web_test_cases()
                },
                {
                    'name': '后端API',
                    'description': '后端API接口测试用例',
                    'modules': self.get_api_modules(),
                    'test_cases': self.get_api_test_cases()
                }
            ],
            'mobile': [
                {
                    'name': 'iOS应用',
                    'description': 'iOS客户端测试用例',
                    'modules': self.get_mobile_modules(),
                    'test_cases': self.get_mobile_test_cases()
                },
                {
                    'name': 'Android应用',
                    'description': 'Android客户端测试用例',
                    'modules': self.get_mobile_modules(),
                    'test_cases': self.get_mobile_test_cases()
                }
            ],
            'api': [
                {
                    'name': 'API接口测试',
                    'description': 'API接口功能测试用例',
                    'modules': self.get_api_modules(),
                    'test_cases': self.get_api_test_cases()
                }
            ],
            'performance': [
                {
                    'name': '性能测试用例',
                    'description': '系统性能测试用例库',
                    'modules': self.get_performance_modules(),
                    'test_cases': self.get_performance_test_cases()
                }
            ]
        }
        return base_configs.get(project.type, base_configs['web'])

    def get_web_modules(self):
        return {
            '用户管理': ['注册登录', '个人信息', '密码管理', '权限设置'],
            '商品模块': ['商品列表', '商品详情', '商品搜索', '商品分类'],
            '订单模块': ['创建订单', '订单列表', '订单详情', '订单取消'],
            '支付模块': ['支付方式', '支付流程', '退款处理'],
            '后台管理': ['用户管理', '商品管理', '订单管理', '数据统计']
        }

    def get_api_modules(self):
        return {
            '用户接口': ['认证接口', '用户信息接口', '权限接口'],
            '业务接口': ['商品接口', '订单接口', '支付接口'],
            '数据接口': ['查询接口', '统计接口', '导出接口']
        }

    def get_mobile_modules(self):
        return {
            '登录注册': ['手机号登录', '第三方登录', '注册流程'],
            '首页': ['轮播图', '推荐商品', '搜索功能'],
            '商品': ['商品列表', '商品详情', '商品收藏'],
            '购物车': ['添加商品', '修改数量', '结算'],
            '我的': ['个人信息', '订单列表', '设置']
        }

    def get_performance_modules(self):
        return {
            '接口性能': ['并发测试', '压力测试', '稳定性测试'],
            '页面性能': ['加载时间', '渲染性能', '资源优化'],
            '数据库性能': ['查询性能', '连接池', '索引优化']
        }

    def get_web_test_cases(self):
        return [
            {'title': '用户注册-正常流程', 'module': '注册登录', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 打开注册页面\n2. 准备有效手机号',
             'steps': [
                 {'step_number': 1, 'description': '输入有效手机号', 'expected_result': '手机号格式校验通过'},
                 {'step_number': 2, 'description': '获取并输入验证码', 'expected_result': '验证码校验通过'},
                 {'step_number': 3, 'description': '设置密码并确认', 'expected_result': '密码强度校验通过'},
                 {'step_number': 4, 'description': '点击注册按钮', 'expected_result': '注册成功，跳转登录页'}
             ]},
            {'title': '用户登录-账号密码登录', 'module': '注册登录', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 已注册账号\n2. 打开登录页面',
             'steps': [
                 {'step_number': 1, 'description': '输入正确的用户名', 'expected_result': '用户名显示正常'},
                 {'step_number': 2, 'description': '输入正确的密码', 'expected_result': '密码显示为密文'},
                 {'step_number': 3, 'description': '点击登录按钮', 'expected_result': '登录成功，跳转首页'}
             ]},
            {'title': '商品搜索-关键词搜索', 'module': '商品搜索', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 已登录\n2. 首页有商品数据',
             'steps': [
                 {'step_number': 1, 'description': '在搜索框输入商品关键词', 'expected_result': '显示搜索建议'},
                 {'step_number': 2, 'description': '点击搜索按钮', 'expected_result': '显示搜索结果列表'},
                 {'step_number': 3, 'description': '检查搜索结果', 'expected_result': '结果与关键词相关'}
             ]},
            {'title': '创建订单-正常流程', 'module': '创建订单', 'priority': 'p0', 'automation_status': 'not_automated',
             'precondition': '1. 已登录\n2. 购物车有商品\n3. 有收货地址',
             'steps': [
                 {'step_number': 1, 'description': '选择购物车商品', 'expected_result': '商品选中状态'},
                 {'step_number': 2, 'description': '点击结算', 'expected_result': '进入订单确认页'},
                 {'step_number': 3, 'description': '确认收货地址', 'expected_result': '地址信息正确'},
                 {'step_number': 4, 'description': '提交订单', 'expected_result': '订单创建成功'}
             ]},
            {'title': '支付流程-支付宝支付', 'module': '支付流程', 'priority': 'p0', 'automation_status': 'not_automated',
             'precondition': '1. 已创建待支付订单',
             'steps': [
                 {'step_number': 1, 'description': '选择支付宝支付', 'expected_result': '跳转支付宝页面'},
                 {'step_number': 2, 'description': '完成支付', 'expected_result': '支付成功'},
                 {'step_number': 3, 'description': '返回商户', 'expected_result': '订单状态更新为已支付'}
             ]},
            {'title': '个人信息修改-修改昵称', 'module': '个人信息', 'priority': 'p2', 'automation_status': 'automated',
             'precondition': '1. 已登录',
             'steps': [
                 {'step_number': 1, 'description': '进入个人中心', 'expected_result': '显示个人信息'},
                 {'step_number': 2, 'description': '点击编辑', 'expected_result': '进入编辑模式'},
                 {'step_number': 3, 'description': '修改昵称并保存', 'expected_result': '昵称修改成功'}
             ]},
        ]

    def get_api_test_cases(self):
        return [
            {'title': '用户登录接口-正常登录', 'module': '认证接口', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 用户已注册\n2. 接口服务正常',
             'steps': [
                 {'step_number': 1, 'description': 'POST /api/auth/login', 'expected_result': '返回200状态码'},
                 {'step_number': 2, 'description': '验证返回token', 'expected_result': 'token格式正确'},
                 {'step_number': 3, 'description': '验证token有效期', 'expected_result': '有效期24小时'}
             ]},
            {'title': '获取用户信息接口', 'module': '用户信息接口', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 用户已登录\n2. 有有效token',
             'steps': [
                 {'step_number': 1, 'description': 'GET /api/user/info', 'expected_result': '返回200状态码'},
                 {'step_number': 2, 'description': '验证返回数据结构', 'expected_result': '包含必要字段'},
                 {'step_number': 3, 'description': '验证数据正确性', 'expected_result': '数据与数据库一致'}
             ]},
            {'title': '商品列表接口-分页查询', 'module': '商品接口', 'priority': 'p1', 'automation_status': 'automated',
             'precondition': '1. 接口服务正常',
             'steps': [
                 {'step_number': 1, 'description': 'GET /api/products?page=1&size=10', 'expected_result': '返回200状态码'},
                 {'step_number': 2, 'description': '验证分页数据', 'expected_result': '返回10条数据'},
                 {'step_number': 3, 'description': '验证总数字段', 'expected_result': 'total字段正确'}
             ]},
        ]

    def get_mobile_test_cases(self):
        return [
            {'title': 'APP启动-正常启动', 'module': '登录注册', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. APP已安装\n2. 设备网络正常',
             'steps': [
                 {'step_number': 1, 'description': '点击APP图标', 'expected_result': 'APP启动'},
                 {'step_number': 2, 'description': '等待启动页加载', 'expected_result': '显示启动页'},
                 {'step_number': 3, 'description': '进入首页', 'expected_result': '首页正常显示'}
             ]},
            {'title': '手机号登录-验证码登录', 'module': '手机号登录', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. APP已启动\n2. 手机号已注册',
             'steps': [
                 {'step_number': 1, 'description': '输入手机号', 'expected_result': '格式校验通过'},
                 {'step_number': 2, 'description': '获取验证码', 'expected_result': '验证码发送成功'},
                 {'step_number': 3, 'description': '输入验证码登录', 'expected_result': '登录成功'}
             ]},
        ]

    def get_performance_test_cases(self):
        return [
            {'title': '登录接口并发测试', 'module': '并发测试', 'priority': 'p0', 'automation_status': 'automated',
             'precondition': '1. 测试环境已部署\n2. JMeter已配置',
             'steps': [
                 {'step_number': 1, 'description': '设置100并发用户', 'expected_result': '配置成功'},
                 {'step_number': 2, 'description': '执行测试脚本', 'expected_result': '测试完成'},
                 {'step_number': 3, 'description': '检查响应时间', 'expected_result': '平均响应时间<500ms'},
                 {'step_number': 4, 'description': '检查错误率', 'expected_result': '错误率<1%'}
             ]},
            {'title': '首页加载时间测试', 'module': '加载时间', 'priority': 'p1', 'automation_status': 'automated',
             'precondition': '1. 网络环境正常',
             'steps': [
                 {'step_number': 1, 'description': '清除浏览器缓存', 'expected_result': '缓存已清除'},
                 {'step_number': 2, 'description': '访问首页', 'expected_result': '页面加载完成'},
                 {'step_number': 3, 'description': '记录加载时间', 'expected_result': '加载时间<3秒'}
             ]},
        ]

    def create_repository(self, project, users, config):
        """创建用例库"""
        repo, created = TestCaseRepository.objects.get_or_create(
            name=config['name'],
            project=project,
            defaults={
                'description': config['description'],
                'is_default': TestCaseRepository.objects.filter(project=project).count() == 0,
                'created_by': users.get('test_manager')
            }
        )
        if created:
            self.stdout.write(f'  [OK] 创建用例库: {repo.name}')
        return repo

    def create_versions(self, repo, users):
        """创建版本"""
        versions = []
        versions_data = [
            {'name': 'v1.0', 'status': 'archived', 'is_default': False, 'description': '初始版本'},
            {'name': 'v2.0', 'status': 'archived', 'is_default': False, 'description': '功能优化版本'},
            {'name': 'v3.0', 'status': 'active', 'is_default': True, 'description': '当前版本'},
        ]
        
        for ver_data in versions_data:
            version, created = TestCaseVersion.objects.get_or_create(
                name=ver_data['name'],
                repository=repo,
                defaults={
                    'description': ver_data['description'],
                    'status': ver_data['status'],
                    'is_default': ver_data['is_default'],
                    'created_by': users.get('test_manager')
                }
            )
            if created:
                self.stdout.write(f'    [OK] 创建版本: {version.name}')
            versions.append(version)
        return versions

    def create_modules_and_cases(self, version, users, config):
        """创建模块和测试用例"""
        modules_config = config['modules']
        test_cases_config = config['test_cases']
        
        module_map = {}
        sort_order = 1
        for parent_name, children in modules_config.items():
            parent_module, created = TestModule.objects.get_or_create(
                name=parent_name,
                version=version,
                parent=None,
                defaults={'sort_order': sort_order}
            )
            if created:
                self.stdout.write(f'      [OK] 创建模块: {parent_module.name}')
            module_map[parent_name] = parent_module
            
            for idx, child_name in enumerate(children):
                child_module, created = TestModule.objects.get_or_create(
                    name=child_name,
                    version=version,
                    parent=parent_module,
                    defaults={'sort_order': idx + 1}
                )
                if created:
                    self.stdout.write(f'        [OK] 创建子模块: {child_module.name}')
                module_map[child_name] = child_module
            sort_order += 1
        
        tester_users = [u for u in users.values() if u.system_role and u.system_role.code in ['test_engineer', 'test_manager']]
        
        for case_data in test_cases_config:
            module_name = case_data.get('module')
            module = module_map.get(module_name)
            if not module:
                continue
            
            test_case, created = TestCase.objects.get_or_create(
                title=case_data['title'],
                version=version,
                defaults={
                    'module': module,
                    'priority': case_data.get('priority', 'p2'),
                    'automation_status': case_data.get('automation_status', 'not_analyzed'),
                    'precondition': case_data.get('precondition', ''),
                    'estimated_hours': round(random.uniform(0.5, 2.0), 2),
                    'created_by': random.choice(tester_users) if tester_users else users.get('test_manager'),
                    'updated_by': random.choice(tester_users) if tester_users else users.get('test_manager'),
                }
            )
            
            if created:
                self.stdout.write(f'        [OK] 创建用例: {test_case.title}')
                
                for step_data in case_data.get('steps', []):
                    TestStep.objects.create(
                        test_case=test_case,
                        step_number=step_data['step_number'],
                        description=step_data['description'],
                        expected_result=step_data.get('expected_result', '')
                    )
                
                if random.random() > 0.6:
                    self.create_review(test_case, users)
                
                if random.random() > 0.4:
                    self.create_executions(test_case, users)

    def create_review(self, test_case, users):
        """创建评审记录"""
        reviewer = users.get('test_manager')
        if not reviewer:
            return
        
        status = random.choice(['pending', 'approved', 'rejected'])
        comments = {
            'pending': '待评审',
            'approved': '用例设计合理，覆盖主要场景，通过评审',
            'rejected': '需要补充异常场景和边界条件测试'
        }
        
        review = TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=reviewer,
            status=status,
            comment=comments.get(status, '')
        )
        self.stdout.write(f'          [OK] 创建评审: {review.get_status_display()}')

    def create_executions(self, test_case, users):
        """创建执行记录"""
        tester_users = [u for u in users.values() if u.system_role and u.system_role.code == 'test_engineer']
        if not tester_users:
            return
        
        results = ['pass', 'fail', 'block', 'skip']
        result_comments = {
            'pass': '执行通过，实际结果与预期一致',
            'fail': '执行失败，发现缺陷',
            'block': '阻塞，依赖条件不满足',
            'skip': '跳过执行'
        }
        
        for i in range(random.randint(1, 2)):
            result = random.choice(results)
            executed_at = datetime.now() - timedelta(days=random.randint(1, 30))
            
            execution = TestCaseExecution.objects.create(
                test_case=test_case,
                executed_by=random.choice(tester_users),
                result=result,
                actual_result=result_comments.get(result, ''),
                remark=f'第{i+1}次执行'
            )
            TestCaseExecution.objects.filter(id=execution.id).update(executed_at=executed_at)
        
        self.stdout.write(f'          [OK] 创建执行记录')

    def print_summary(self, users, projects):
        """打印数据摘要"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('数据摘要:'))
        self.stdout.write(f'  用户数: {User.objects.count()}')
        self.stdout.write(f'  项目数: {Project.objects.count()}')
        self.stdout.write(f'  用例库数: {TestCaseRepository.objects.count()}')
        self.stdout.write(f'  版本数: {TestCaseVersion.objects.count()}')
        self.stdout.write(f'  模块数: {TestModule.objects.count()}')
        self.stdout.write(f'  测试用例数: {TestCase.objects.count()}')
        self.stdout.write(f'  测试步骤数: {TestStep.objects.count()}')
        self.stdout.write(f'  评审记录数: {TestCaseReview.objects.count()}')
        self.stdout.write(f'  执行记录数: {TestCaseExecution.objects.count()}')
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('测试账号信息:'))
        self.stdout.write('  所有用户密码: test123456')
        self.stdout.write('  管理员账号: admin')
        self.stdout.write('  测试经理: test_manager')
        self.stdout.write('  测试工程师: tester1, tester2')
