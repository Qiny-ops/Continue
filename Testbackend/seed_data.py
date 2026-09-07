"""生成测试数据"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Testbackend.settings'

import django
django.setup()

from apps.users.models import User, Role
from apps.projects.models import Project, ProjectMember, ProjectRole
from apps.testcase.models import TestCaseRepository, TestCaseVersion, TestModule, TestCase, TestCaseExecution, TestCaseReview, AIGenerationRecord
from apps.requirement.models import Requirement
from apps.apitest.models import ApiEnvironment, ApiTestCase, ApiTestRun

# 1. 设置管理员密码
admin = User.objects.get(username='admin')
admin.set_password('admin123')
admin.name = '系统管理员'
admin.status = 'active'
admin.save()

# 2. 创建角色
admin_role, _ = Role.objects.get_or_create(code='admin', defaults={'name': '系统管理员', 'type': 'system', 'status': 'active'})
user_role, _ = Role.objects.get_or_create(code='user', defaults={'name': '普通用户', 'type': 'default', 'status': 'active'})
admin.system_role = admin_role
admin.save()

# 3. 创建测试用户
tester1, _ = User.objects.get_or_create(username='zhangsan', defaults={'password': 'test123', 'email': 'zhangsan@test.com', 'name': '张三', 'system_role': user_role, 'status': 'active'})
tester1.set_password('test123')
tester1.save()
tester2, _ = User.objects.get_or_create(username='lisi', defaults={'email': 'lisi@test.com', 'name': '李四', 'system_role': user_role, 'status': 'active'})
tester2.set_password('test123')
tester2.save()
tester3, _ = User.objects.get_or_create(username='wangwu', defaults={'email': 'wangwu@test.com', 'name': '王五', 'system_role': user_role, 'status': 'active'})
tester3.set_password('test123')
tester3.save()

# 4. 创建项目
proj1 = Project.objects.create(name='电商平台', code='ECOM', description='电商后台管理系统', type='web', status='active', owner=admin, created_by=admin, icon='Shop', icon_color='#3b82f6')
proj2 = Project.objects.create(name='用户中心', code='UCENTER', description='用户认证与权限中心', type='api', status='active', owner=admin, created_by=admin, icon='User', icon_color='#22c55e')
proj3 = Project.objects.create(name='移动端APP', code='MAPP', description='移动端应用测试', type='mobile', status='pending', owner=admin, created_by=admin, icon='Iphone', icon_color='#f59e0b')

# 5. 添加项目成员
ProjectMember.objects.create(project=proj1, user=admin, role='admin', status='active')
ProjectMember.objects.create(project=proj1, user=tester1, role='tester', status='active')
ProjectMember.objects.create(project=proj1, user=tester2, role='developer', status='active')
ProjectMember.objects.create(project=proj2, user=admin, role='admin', status='active')
ProjectMember.objects.create(project=proj2, user=tester1, role='tester', status='active')
ProjectMember.objects.create(project=proj2, user=tester3, role='developer', status='active')
ProjectMember.objects.create(project=proj3, user=admin, role='admin', status='active')
ProjectMember.objects.create(project=proj3, user=tester2, role='tester', status='active')

# 6. 创建项目角色权限
for proj in [proj1, proj2, proj3]:
    for rkey, perms in [
        ('admin', ['project_manage','member_manage','testcase_manage','testcase_view','apitest_manage','apitest_view','apitest_execute','knowledge_manage','knowledge_view','test_execute','report_view','settings_manage']),
        ('developer', ['testcase_view','testcase_manage','apitest_view','apitest_execute','knowledge_view','report_view']),
        ('tester', ['testcase_view','testcase_manage','apitest_view','apitest_execute','test_execute','knowledge_view','report_view']),
        ('viewer', ['testcase_view','apitest_view','knowledge_view','report_view']),
    ]:
        ProjectRole.objects.get_or_create(project=proj, role_key=rkey, defaults={'permissions': perms, 'name': {'admin':'管理员','developer':'开发人员','tester':'测试人员','viewer':'观察者'}[rkey]})

print('=== 项目和用户创建完成 ===')

# 7. 创建用例库
repo1 = TestCaseRepository.objects.create(name='电商平台用例库', project=proj1, description='电商平台功能测试用例库', is_default=True, created_by=admin)
repo2 = TestCaseRepository.objects.create(name='用户中心用例库', project=proj2, description='用户中心接口测试用例库', is_default=True, created_by=admin)
repo3 = TestCaseRepository.objects.create(name='移动端用例库', project=proj3, description='移动端APP测试用例库', is_default=True, created_by=admin)

# 8. 创建版本
ver1 = TestCaseVersion.objects.create(name='v2.0', repository=repo1, description='2026年Q3版本', status='active', is_default=True, created_by=admin)
ver1_old = TestCaseVersion.objects.create(name='v1.0', repository=repo1, description='历史版本', status='archived', is_default=False, created_by=admin)
ver2 = TestCaseVersion.objects.create(name='v1.0', repository=repo2, description='初始版本', status='active', is_default=True, created_by=admin)
ver3 = TestCaseVersion.objects.create(name='v1.0', repository=repo3, description='初始版本', status='active', is_default=True, created_by=admin)

print('=== 用例库和版本创建完成 ===')

# 9. 创建模块树
mod_login = TestModule.objects.create(name='登录模块', version=ver1, sort_order=0)
mod_product = TestModule.objects.create(name='商品管理', version=ver1, sort_order=1)
mod_product_list = TestModule.objects.create(name='商品列表', version=ver1, parent=mod_product, sort_order=0)
mod_product_add = TestModule.objects.create(name='新增商品', version=ver1, parent=mod_product, sort_order=1)
mod_order = TestModule.objects.create(name='订单管理', version=ver1, sort_order=2)
mod_payment = TestModule.objects.create(name='支付模块', version=ver1, sort_order=3)
mod_search = TestModule.objects.create(name='搜索功能', version=ver1, sort_order=4)

mod_auth = TestModule.objects.create(name='认证模块', version=ver2, sort_order=0)
mod_perm = TestModule.objects.create(name='权限管理', version=ver2, sort_order=1)
mod_profile = TestModule.objects.create(name='用户信息', version=ver2, sort_order=2)

print('=== 模块创建完成 ===')

# 10. 创建需求
req1 = Requirement.objects.create(project=proj1, version=ver1, title='用户登录功能', func_point='用户登录', priority='p0', status='active', source='manual', created_by=tester1, updated_by=tester1)
req2 = Requirement.objects.create(project=proj1, version=ver1, title='商品搜索功能', func_point='商品搜索', priority='p1', status='active', source='manual', created_by=tester1, updated_by=tester1)
req3 = Requirement.objects.create(project=proj1, version=ver1, title='订单支付功能', func_point='订单支付', priority='p0', status='active', source='ai_extracted', knowledge_base_id='kb_001', created_by=tester2, updated_by=tester2)
req4 = Requirement.objects.create(project=proj2, version=ver2, title='OAuth2认证', func_point='OAuth2认证接入', priority='p0', status='active', source='manual', created_by=tester3, updated_by=tester3)
req5 = Requirement.objects.create(project=proj2, version=ver2, title='角色权限管理', func_point='角色权限CRUD', priority='p1', status='draft', source='manual', created_by=tester3, updated_by=tester3)

print('=== 需求创建完成 ===')

# 11. 创建功能测试用例
cases_data = [
    (mod_login, '用户名密码登录-正常流程', 'p0', '用户已注册账号，密码正确', '1. 打开登录页面\n2. 输入用户名admin\n3. 输入密码123456\n4. 点击登录按钮', '登录成功，跳转到首页', 'approved', 'manual'),
    (mod_login, '用户名密码登录-密码错误', 'p1', '用户已注册账号，密码输入错误', '1. 打开登录页面\n2. 输入用户名admin\n3. 输入错误密码\n4. 点击登录按钮', '提示密码错误，登录失败', 'approved', 'manual'),
    (mod_login, '登录页面-记住密码功能', 'p2', '用户已注册账号', '1. 打开登录页面\n2. 输入用户名和密码\n3. 勾选记住密码\n4. 点击登录\n5. 关闭浏览器重新打开', '自动填充用户名和密码', 'pending', 'manual'),
    (mod_product_list, '商品列表-分页展示', 'p1', '系统中存在商品数据', '1. 进入商品管理页面\n2. 查看商品列表', '商品列表按分页展示，默认每页20条', 'approved', 'manual'),
    (mod_product_add, '新增商品-必填字段校验', 'p0', '用户有商品管理权限', '1. 进入新增商品页面\n2. 不填写任何字段\n3. 点击提交', '提示必填字段不能为空', 'pending', 'manual'),
    (mod_product_add, '新增商品-正常流程', 'p0', '用户有商品管理权限，商品信息已准备', '1. 进入新增商品页面\n2. 填写商品名称、价格、分类\n3. 上传商品图片\n4. 点击提交', '商品创建成功，列表中可见新商品', 'pending', 'ai_generated'),
    (mod_order, '创建订单-正常流程', 'p0', '用户已登录，购物车中有商品', '1. 进入购物车\n2. 选择商品\n3. 点击结算\n4. 填写收货地址\n5. 确认订单', '订单创建成功，进入待支付状态', 'approved', 'manual'),
    (mod_order, '订单取消-未支付订单', 'p2', '用户有未支付订单', '1. 进入我的订单\n2. 选择未支付订单\n3. 点击取消订单', '订单状态变为已取消', 'pending', 'manual'),
    (mod_payment, '支付-支付宝支付', 'p0', '用户有待支付订单，支付宝账号已绑定', '1. 进入订单支付页面\n2. 选择支付宝支付\n3. 确认支付', '支付成功，订单状态变为已支付', 'pending', 'ai_generated'),
    (mod_payment, '支付-微信支付', 'p0', '用户有待支付订单，微信账号已绑定', '1. 进入订单支付页面\n2. 选择微信支付\n3. 扫码确认支付', '支付成功，订单状态变为已支付', 'pending', 'manual'),
    (mod_search, '搜索-关键词搜索商品', 'p1', '系统中存在商品数据', '1. 在搜索框输入关键词\n2. 点击搜索', '显示包含关键词的商品列表', 'approved', 'manual'),
    (mod_search, '搜索-空结果提示', 'p2', '无', '1. 在搜索框输入不存在的商品名\n2. 点击搜索', '显示无搜索结果提示', 'pending', 'manual'),
    (mod_auth, '用户注册-正常流程', 'p0', '无', '1. 打开注册页面\n2. 填写用户名、邮箱、密码\n3. 点击注册', '注册成功，自动登录', 'approved', 'manual'),
    (mod_auth, '用户注册-重复邮箱', 'p1', '邮箱已被注册', '1. 打开注册页面\n2. 填写已注册的邮箱\n3. 点击注册', '提示邮箱已被注册', 'pending', 'manual'),
    (mod_perm, '角色创建-正常流程', 'p1', '管理员已登录', '1. 进入角色管理\n2. 点击新建角色\n3. 填写角色名称和权限\n4. 点击保存', '角色创建成功', 'approved', 'manual'),
    (mod_profile, '修改用户信息-修改昵称', 'p2', '用户已登录', '1. 进入个人中心\n2. 修改昵称\n3. 点击保存', '昵称修改成功', 'pending', 'manual'),
]

created_cases = []
for module, title, priority, precondition, steps, expected, review_status, source in cases_data:
    case = TestCase.objects.create(
        title=title, module=module, version=module.version, priority=priority,
        precondition=precondition, steps=steps, expected_result=expected,
        review_status=review_status, generation_source=source,
        created_by=tester1 if source=='manual' else tester2,
        updated_by=tester1 if source=='manual' else tester2,
    )
    created_cases.append(case)

# 关联需求到用例
created_cases[0].requirement = req1
created_cases[0].save()
created_cases[1].requirement = req1
created_cases[1].save()
created_cases[10].requirement = req2
created_cases[10].save()
created_cases[12].requirement = req4
created_cases[12].save()

print(f'=== 创建了 {len(created_cases)} 个功能测试用例 ===')

# 12. 创建执行记录
exec_results = ['pass', 'fail', 'pass', 'pass', 'skip', 'block', 'pass', 'pass', 'fail', 'pass']
for i, case in enumerate(created_cases[:10]):
    result = exec_results[i] if i < len(exec_results) else 'pass'
    TestCaseExecution.objects.create(
        test_case=case, executed_by=tester1, result=result,
        actual_result='符合预期' if result=='pass' else ('与预期不符' if result=='fail' else ''),
    )

print('=== 执行记录创建完成 ===')

# 13. 创建评审记录
review_cases = [c for c in created_cases if c.review_status == 'pending']
for case in review_cases[:3]:
    TestCaseReview.objects.create(
        test_case=case, reviewer=tester2, status='pending', comment=''
    )

print('=== 评审记录创建完成 ===')

# 14. 创建AI生成记录
AIGenerationRecord.objects.create(
    version=ver1, module=mod_product_add,
    module_name='商品管理', func_point='新增商品', test_type='功能点测试',
    knowledge_base_ids=['kb_001'], knowledge_ids=[],
    ai_request_id='req_001', ai_model_version='gpt-4o',
    ai_confidence=0.92,
    status='completed', cases_created_count=1,
    created_by=tester2,
)

print('=== AI生成记录创建完成 ===')

# 15. 创建接口测试环境
env1 = ApiEnvironment.objects.create(
    project=proj1, name='测试环境', env_type='test',
    base_url='https://api-test.ecom.example.com',
    auth_type='bearer', auth_token='{{test_token}}',
    is_default=True, is_active=True,
    created_by=admin,
)
env2 = ApiEnvironment.objects.create(
    project=proj1, name='开发环境', env_type='dev',
    base_url='https://api-dev.ecom.example.com',
    auth_type='none', is_default=False, is_active=True,
    created_by=admin,
)

print('=== 接口测试环境创建完成 ===')

# 16. 创建接口测试用例
api_cases_data = [
    ('用户登录接口', '用户已注册', '调用登录接口', '返回200和token', 'p0', 'draft', 'manual'),
    ('获取商品列表接口', '无', '调用商品列表接口', '返回商品列表数据', 'p1', 'ready', 'manual'),
    ('创建订单接口', '用户已登录', '调用创建订单接口', '返回订单ID', 'p0', 'draft', 'ai_generated'),
    ('支付回调接口', '订单已创建', '调用支付回调接口', '订单状态更新为已支付', 'p0', 'draft', 'manual'),
    ('搜索商品接口', '无', '调用搜索接口', '返回搜索结果', 'p1', 'ready', 'ai_generated'),
]

api_cases = []
for name, precondition, testpoint, expectation, priority, status, source in api_cases_data:
    case = ApiTestCase.objects.create(
        project=proj1, version=ver1, name=name,
        precondition=precondition, testpoint=testpoint, expectation=expectation,
        priority=priority, status=status, source=source,
        test_data={'username': 'test_user', 'password': 'test123'} if '登录' in name else {},
        run_list=[],
        knowledge_base_id='kb_001' if source=='ai_generated' else '',
        created_by=tester1 if source=='manual' else tester2,
        updated_by=tester1 if source=='manual' else tester2,
    )
    api_cases.append(case)

print(f'=== 创建了 {len(api_cases)} 个接口测试用例 ===')

# 17. 创建接口测试执行记录
ApiTestRun.objects.create(
    test_case=api_cases[0], environment=env1, result='pass',
    duration_ms=320, step_results=[{'step': 1, 'success': True, 'status_code': 200}],
    executed_by=tester1,
)
ApiTestRun.objects.create(
    test_case=api_cases[1], environment=env1, result='fail',
    duration_ms=150, error_message='返回数据格式不匹配',
    step_results=[{'step': 1, 'success': False, 'status_code': 200}],
    executed_by=tester1,
)

print('=== 接口测试执行记录创建完成 ===')

# 统计
print()
print('========== 数据统计 ==========')
print(f'用户: {User.objects.count()}')
print(f'项目: {Project.objects.count()}')
print(f'用例库: {TestCaseRepository.objects.count()}')
print(f'版本: {TestCaseVersion.objects.count()}')
print(f'模块: {TestModule.objects.count()}')
print(f'需求: {Requirement.objects.count()}')
print(f'功能测试用例: {TestCase.objects.count()}')
print(f'执行记录: {TestCaseExecution.objects.count()}')
print(f'评审记录: {TestCaseReview.objects.count()}')
print(f'AI生成记录: {AIGenerationRecord.objects.count()}')
print(f'接口测试环境: {ApiEnvironment.objects.count()}')
print(f'接口测试用例: {ApiTestCase.objects.count()}')
print(f'接口测试执行: {ApiTestRun.objects.count()}')
