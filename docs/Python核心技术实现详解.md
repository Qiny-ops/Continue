# 项目Python核心技术详解

> 本文档详细说明项目中使用的Python核心技术，包括装饰器、索引设计、文件上传、ORM优化等。

---

## 一、装饰器技术

### 1.1 权限装饰器

**文件位置**: `apps/core/decorators.py`

#### 1.1.1 项目权限装饰器

```python
def require_project_permission(permission_code):
    """
    项目权限检查装饰器

    使用 functools.wraps 保留原函数的元信息（__name__, __doc__等）

    用法:
        @api_view(['POST'])
        @authentication_classes([JWTAuthentication])
        @permission_classes([IsAuthenticated])
        @require_project_permission('testcase_manage')
        def create_testcase(request, project_identifier):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)  # 保留原函数元信息
        def wrapper(request, *args, **kwargs):
            # 获取项目ID或标识符
            project_id = kwargs.get('project_id')
            project_identifier = kwargs.get('project_identifier')

            # 如果是标识符，需要转换为ID
            if project_identifier and not project_id:
                from apps.projects.repositories import ProjectRepository
                project = ProjectRepository.get_by_identifier(project_identifier)
                if project:
                    project_id = project.id

            if not project_id:
                return StandardResponse(message='无法确定项目', code=400)

            # 检查权限
            if not has_project_permission(project_id, request.user, permission_code):
                return StandardResponse(message='无权限执行此操作', code=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**为什么使用装饰器？**

| 方案 | 优点 | 缺点 |
|------|------|------|
| **装饰器** | 代码复用、声明式、关注点分离 | 嵌套多层时可读性降低 |
| 中间件 | 全局生效 | 粒度太粗，无法针对单个视图 |
| 基类继承 | 统一行为 | Python单继承限制，不够灵活 |

**选择装饰器的原因：**
- 按需使用，灵活度高
- 可以组合多个装饰器
- 权限逻辑与业务逻辑分离

#### 1.1.2 系统管理员权限装饰器

```python
def require_system_admin(view_func):
    """系统管理员权限检查装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_system_admin(request.user):
            return StandardResponse(message='需要系统管理员权限', code=403)
        return view_func(request, *args, **kwargs)
    return wrapper
```

#### 1.1.3 装饰器组合使用

```python
# 实际使用示例
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@require_project_admin
def update_project_settings(request, project_identifier):
    """更新项目设置 - 需要项目管理员权限"""
    ...
```

**装饰器执行顺序（从外到内）：**

```
请求 → api_view → authentication_classes → permission_classes → require_project_admin → 视图函数
```

---

### 1.2 DRF框架装饰器

#### 1.2.1 @api_view

```python
from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])  # 只允许GET和POST方法
def test_cases_view(request):
    if request.method == 'GET':
        # 获取列表
        ...
    elif request.method == 'POST':
        # 创建
        ...
```

**为什么用@api_view而不是ViewSet？**

| 方案 | 适用场景 | 选择理由 |
|------|---------|---------|
| **@api_view** | 简单CRUD、定制化逻辑 | 灵活度高，适合本项目 |
| ViewSet | 标准REST操作 | 需要额外的Router配置 |
| APIView | 类视图，支持继承 | 本项目函数式风格更简洁 |

#### 1.2.2 @authentication_classes

```python
from rest_framework.decorators import authentication_classes
from apps.users.authentication import JWTAuthentication

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
def get_profile(request):
    # request.user 已经是认证后的用户
    return StandardResponse(data={'username': request.user.username})
```

#### 1.2.3 @permission_classes

```python
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    # 未登录用户会收到401响应
    ...
```

---

### 1.3 Python内置装饰器

#### 1.3.1 @staticmethod 和 @classmethod

```python
class ProjectService:
    """项目服务"""

    @staticmethod
    def get_project_stats(user):
        """静态方法 - 不需要访问实例属性

        为什么用staticmethod？
        - Service层不需要维护状态
        - 无需实例化即可调用
        - 更易于单元测试（可以直接mock）
        """
        project_ids = ProjectRepository.get_user_projects(user)
        return ProjectRepository.get_project_stats(project_ids)

    @classmethod
    def success(cls, data=None, message=None):
        """类方法 - 可以访问类属性

        为什么用classmethod？
        - 可以被继承覆写
        - 可以访问类级别的配置
        """
        return data, message
```

**@staticmethod vs @classmethod：**

| 特性 | @staticmethod | @classmethod |
|------|---------------|--------------|
| 访问实例属性 | ❌ | ❌ |
| 访问类属性 | ❌ | ✓ (通过cls) |
| 可被继承覆写 | ❌ | ✓ |
| 适用场景 | 工具方法、纯函数 | 工厂方法、需要类属性的方法 |

#### 1.3.2 @property

```python
class User(AbstractUser):
    @property
    def is_admin(self):
        """属性访问器 - 像访问属性一样调用方法"""
        return self.system_role.code == 'admin' if self.system_role else False

# 使用
user = User.objects.get(id=1)
if user.is_admin:  # 不需要 user.is_admin()
    print("是管理员")
```

#### 1.3.3 @transaction.atomic

```python
from django.db import transaction

class ProjectService:
    @staticmethod
    @transaction.atomic
    def create_project(user, data):
        """事务装饰器 - 整个方法在事务中执行

        如果任何操作失败，所有数据库操作都会回滚
        """
        # 创建项目
        project = ProjectRepository.create_project(...)

        # 添加成员
        ProjectMemberRepository.add_member(project, user, role='admin')

        # 创建默认角色权限
        ProjectRoleRepository.create_default_roles(project)

        # 创建默认用例库和版本
        TestCaseRepository.objects.create(...)
        TestCaseVersion.objects.create(...)

        return project  # 成功则提交事务
```

**为什么用装饰器而不是with语句？**

```python
# 方式一：装饰器（推荐）
@transaction.atomic
def create_project(user, data):
    ...

# 方式二：with语句
def create_project(user, data):
    with transaction.atomic():
        ...
```

选择装饰器的原因：
- 声明式，意图更明确
- 代码更简洁
- 适合整个方法都需要事务的场景

---

## 二、数据库索引设计

### 2.1 索引类型与使用

#### 2.1.1 单字段索引

```python
class User(AbstractUser):
    class Meta:
        indexes = [
            models.Index(fields=['username']),   # 按用户名查询
            models.Index(fields=['email']),      # 按邮箱查询
            models.Index(fields=['status']),     # 按状态筛选
            models.Index(fields=['system_role']), # 按角色筛选
        ]
```

**应用场景：**
- `username`：登录时查询
- `email`：邮箱找回密码、用户搜索
- `status`：管理后台按状态筛选用户
- `system_role`：按角色查询用户列表

#### 2.1.2 复合索引

```python
class TestCase(models.Model):
    class Meta:
        indexes = [
            # 复合索引：先按version筛选，再按priority排序
            models.Index(fields=['version', 'priority']),

            # 复合索引：按版本筛选自动化状态
            models.Index(fields=['version', 'automation_status']),

            # 复合索引：按版本和模块查询
            models.Index(fields=['version', 'parent']),  # TestModule
        ]
```

**为什么需要复合索引？**

查询场景：获取某版本下的所有P0优先级用例

```python
# 没有复合索引
TestCase.objects.filter(version_id=1, priority='p0')
# 执行：先按version筛选 → 结果集再按priority过滤（性能差）

# 有复合索引 (version, priority)
# 执行：直接定位到符合条件的记录（性能好）
```

**复合索引原则（最左前缀）：**

```python
# 索引: ['version', 'priority', 'module']

# ✓ 能命中索引
filter(version=1)
filter(version=1, priority='p0')
filter(version=1, priority='p0', module=5)

# ✗ 不能命中索引
filter(priority='p0')           # 跳过了version
filter(module=5)                # 跳过了version和priority
filter(priority='p0', module=5) # 跳过了version
```

#### 2.1.3 业务场景索引设计

```python
class ProjectMember(models.Model):
    class Meta:
        indexes = [
            # 获取项目的活跃成员列表
            models.Index(fields=['project', 'status']),

            # 获取项目的某角色成员
            models.Index(fields=['project', 'role']),

            # 获取用户收藏的项目
            models.Index(fields=['user', 'is_favorite']),
        ]
```

**查询场景映射：**

| 查询场景 | SQL | 索引 |
|---------|-----|------|
| 获取项目成员 | `WHERE project_id=X AND status='active'` | `(project, status)` |
| 获取项目管理员 | `WHERE project_id=X AND role='admin'` | `(project, role)` |
| 获取用户收藏 | `WHERE user_id=X AND is_favorite=True` | `(user, is_favorite)` |

### 2.2 索引设计决策

**为什么不给所有字段加索引？**

| 考量 | 说明 |
|------|------|
| 写入性能 | 每次INSERT/UPDATE/DELETE都需要更新索引 |
| 存储空间 | 索引占用磁盘空间 |
| 内存占用 | 索引会被加载到内存，影响可用内存 |

**索引设计原则：**

1. **选择性高的字段优先**：email、code等唯一字段比status选择性高
2. **高频查询优先**：分析实际查询频率
3. **复合索引覆盖**：一个复合索引可以替代多个单字段索引
4. **避免过度索引**：通常索引数量不超过表字段数的20%

---

## 三、文件上传技术

### 3.1 头像上传实现

**文件位置**: `apps/users/services/user_service.py`

```python
from django.core.files.storage import default_storage
import uuid

class UserServiceExtended:
    @staticmethod
    def upload_avatar(user, avatar_file):
        """上传头像

        技术要点：
        1. 文件大小验证
        2. 文件类型验证
        3. 安全文件名生成
        4. Django default_storage存储
        """
        # 1. 大小验证（最大2MB）
        if avatar_file.size > 2 * 1024 * 1024:
            raise ValidationError('头像文件大小不能超过2MB')

        # 2. 类型验证
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            raise ValidationError('只支持 JPG、PNG、GIF 格式的图片')

        # 3. 安全文件名（防止路径遍历攻击）
        ext = avatar_file.name.split('.')[-1].lower()
        filename = f'avatars/{user.id}_{uuid.uuid4().hex[:8]}.{ext}'

        # 4. 存储（自动处理路径、去重）
        saved_path = default_storage.save(filename, avatar_file)

        # 5. 更新用户记录
        user.avatar = saved_path
        user.save()

        return saved_path
```

**为什么使用default_storage？**

```python
# settings.py 配置
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# default_storage 自动处理：
# - 文件路径拼接
# - 文件名冲突（自动加后缀）
# - 支持切换存储后端（本地/S3/OSS等）
```

### 3.2 知识库文件上传

**文件位置**: `apps/knowledge/views/knowledge_views.py`

```python
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def upload_file_knowledge_view(request, kb_id):
    """上传文件到知识库"""
    # 1. 获取上传文件
    file_obj = request.FILES.get('file')
    if not file_obj:
        return StandardResponse(message='文件不能为空', code=400)

    # 2. 读取文件内容
    file_content = file_obj.read()
    file_name = file_obj.name

    # 3. 获取额外参数
    enable_multimodel = request.POST.get('enable_multimodel', 'true').lower() == 'true'
    metadata = request.POST.get('metadata')

    # 4. 调用服务层处理
    result = KnowledgeService.upload_file_knowledge(
        kb_id=kb_id,
        file_content=file_content,
        file_name=file_name,
        metadata={'raw': metadata} if metadata else None,
        enable_multimodel=enable_multimodel
    )

    if result.get('success'):
        return StandardResponse(data=result.get('data', {}), message='上传成功')
    return StandardResponse(message=result.get('error', '上传失败'), code=500)
```

**Django文件上传机制：**

```python
# request.FILES 是一个字典
request.FILES = {
    'file': InMemoryUploadedFile(
        name='document.pdf',
        content_type='application/pdf',
        size=1024000,
        ...
    )
}

# 文件对象的方法
file_obj.read()       # 读取全部内容
file_obj.chunks()     # 分块读取（适合大文件）
file_obj.name         # 原始文件名
file_obj.size         # 文件大小
file_obj.content_type # MIME类型
```

### 3.3 文件下载实现

```python
from django.http import HttpResponse

@api_view(['GET'])
def download_knowledge_view(request, knowledge_id):
    """下载知识文件"""
    response = KnowledgeService.download_knowledge(knowledge_id)

    # 错误处理
    if isinstance(response, dict):
        return StandardResponse(message=response.get('error', '下载失败'), code=500)

    # 使用Django HttpResponse直接返回二进制
    return HttpResponse(
        response.content,
        content_type=response.headers.get('Content-Type', 'application/octet-stream'),
        headers={
            'Content-Disposition': response.headers.get('Content-Disposition', '')
        }
    )
```

**文件下载安全考虑：**

| 安全点 | 处理方式 |
|--------|---------|
| 路径遍历 | 不使用用户输入的文件路径，使用ID查询 |
| 权限控制 | 检查用户是否有权限访问该文件 |
| 敏感文件 | 记录下载日志 |
| MIME类型 | 正确设置Content-Type，防止浏览器执行 |

---

## 四、ORM高级查询技术

### 4.1 select_related（JOIN查询优化）

**解决N+1查询问题：**

```python
# 问题代码（N+1查询）
cases = TestCase.objects.all()
for case in cases:
    print(case.module.name)      # 每次循环都查询module表
    print(case.version.name)     # 每次循环都查询version表

# 优化后（使用JOIN，只执行1条SQL）
cases = TestCase.objects.select_related('module', 'version').all()
for case in cases:
    print(case.module.name)      # 不额外查询
    print(case.version.name)     # 不额外查询
```

**select_related原理：**

```sql
-- 不使用select_related
SELECT * FROM testcase_testcase;
SELECT * FROM testcase_testmodule WHERE id = 1;
SELECT * FROM testcase_testversion WHERE id = 1;
-- ... N+1条SQL

-- 使用select_related
SELECT
    testcase.*,
    module.id, module.name, module.parent_id,
    version.id, version.name, version.repository_id
FROM testcase_testcase testcase
LEFT JOIN testcase_testmodule module ON testcase.module_id = module.id
LEFT JOIN testcase_testversion version ON testcase.version_id = version.id;
-- 只1条SQL
```

**适用场景：** 外键关系（ForeignKey, OneToOne）

### 4.2 prefetch_related（IN查询优化）

**处理多对多/反向关系：**

```python
# 获取用例库及其所有版本
repositories = TestCaseRepository.objects.prefetch_related('versions').all()

for repo in repositories:
    for version in repo.versions.all():  # 不额外查询
        print(version.name)
```

**prefetch_related原理：**

```sql
-- 两条SQL
SELECT * FROM testcase_testcaserepository;
SELECT * FROM testcase_testcaseversion WHERE repository_id IN (1, 2, 3, ...);
-- Python层面合并结果
```

**select_related vs prefetch_related：**

| 方法 | 关系类型 | SQL方式 | 适用场景 |
|------|---------|---------|---------|
| select_related | ForeignKey, OneToOne | JOIN | 一对一、多对一 |
| prefetch_related | ManyToMany, 反向ForeignKey | IN查询 | 多对多、一对多 |

### 4.3 组合使用

```python
class TestCaseDataRepository:
    @classmethod
    def get_base_queryset(cls):
        """获取基础查询集 - 组合预加载"""
        return TestCase.objects.select_related(
            'version', 'version__repository', 'version__repository__project',
            'module', 'created_by', 'updated_by'
        ).prefetch_related(
            'executions'  # 一对多关系
        )
```

### 4.4 Q对象（复杂查询）

```python
from django.db.models import Q

class UserRepository:
    @staticmethod
    def search_users(keyword, limit=20):
        """搜索用户 - 多字段OR查询"""
        queryset = User.objects.filter(status='active').select_related('system_role')

        if keyword:
            queryset = queryset.filter(
                Q(username__icontains=keyword) |  # 用户名包含
                Q(name__icontains=keyword) |      # 姓名包含
                Q(email__icontains=keyword)       # 邮箱包含
            )

        return queryset[:limit]
```

**Q对象组合：**

```python
# OR条件
Q(status='active') | Q(status='pending')

# AND条件
Q(status='active') & Q(role='admin')

# NOT条件
~Q(status='deleted')

# 复杂组合
(Q(status='active') & Q(role='admin')) | Q(is_superuser=True)
```

### 4.5 F对象（字段引用）

```python
from django.db.models import F

# 不使用F对象（需要先查询）
case = TestCase.objects.get(id=1)
case.view_count += 1
case.save()

# 使用F对象（一条SQL完成）
TestCase.objects.filter(id=1).update(view_count=F('view_count') + 1)

# 条件更新
ProjectMember.objects.filter(
    updated_at__lt=F('joined_at')  # 更新时间早于加入时间（异常数据）
).delete()
```

### 4.6 annotate和aggregate（聚合查询）

```python
from django.db.models import Count, Q

class ProjectRepository:
    @staticmethod
    def get_project_stats(project_ids):
        """获取项目统计信息"""
        queryset = Project.objects.filter(id__in=project_ids)

        # aggregate：返回单个结果
        status_stats = queryset.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status='pending')),
            archived=Count('id', filter=Q(status='archived'))
        )

        # annotate：为每条记录添加字段
        by_type = queryset.values('type').annotate(count=Count('id'))

        return {'total': status_stats['total'], 'by_type': list(by_type)}
```

**aggregate vs annotate：**

| 方法 | 返回值 | 用途 |
|------|--------|------|
| aggregate | 字典 | 整体统计（总数、平均值等） |
| annotate | QuerySet | 为每条记录添加计算字段 |

### 4.7 bulk_create和bulk_update（批量操作）

```python
class ModuleRepository:
    @classmethod
    def bulk_create(cls, modules_data: List[Dict]) -> List[TestModule]:
        """批量创建模块

        为什么用bulk_create？
        - 100条数据：100次INSERT vs 1次批量INSERT
        - 性能提升10-100倍
        """
        modules = [TestModule(**data) for data in modules_data]
        return TestModule.objects.bulk_create(modules)

class BaseRepository:
    @classmethod
    def bulk_update(cls, objects_list, fields):
        """批量更新

        参数：
        - objects_list: 对象列表（需要有id）
        - fields: 要更新的字段名列表
        """
        return cls.model.objects.bulk_update(objects_list, fields)

# 使用示例
members = ProjectMember.objects.filter(project_id=1)
for member in members:
    member.status = 'active'
ProjectMember.objects.bulk_update(members, ['status'])
```

---

## 五、缓存技术

### 5.1 Django缓存配置

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### 5.2 幂等性缓存实现

**文件位置**: `apps/testcase/services/test_case_service.py`

```python
from django.core.cache import cache

class IdempotencyService:
    """幂等性服务 - 防止重复提交"""

    IDEMPOTENCY_KEY_PREFIX = 'idempotency_'
    IDEMPOTENCY_KEY_TTL = 3600  # 1小时

    @staticmethod
    def generate_key(operation, user_id, data_hash):
        """生成幂等键"""
        return f"{IdempotencyService.IDEMPOTENCY_KEY_PREFIX}{operation}_{user_id}_{data_hash}"

    @staticmethod
    def check_and_set(operation, user_id, data_hash, result=None):
        """检查幂等键，如果已存在则返回之前的结果"""
        key = IdempotencyService.generate_key(operation, user_id, data_hash)

        # 检查是否已存在
        cached_result = cache.get(key)
        if cached_result is not None:
            return cached_result, True  # 幂等命中

        # 设置新键
        if result is not None:
            cache.set(key, result, IdempotencyService.IDEMPOTENCY_KEY_TTL)

        return None, False

    @staticmethod
    def generate_data_hash(data):
        """生成数据哈希值"""
        import json
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()
```

**使用示例：**

```python
@transaction.atomic
def batch_copy_test_cases(ids, user, idempotency_key=None):
    """批量复制测试用例 - 支持幂等性"""
    if idempotency_key:
        data_hash = IdempotencyService.generate_data_hash({'ids': sorted(ids)})
        cached_result, hit = IdempotencyService.check_and_set(
            'batch_copy', user.id, data_hash
        )
        if hit:
            return cached_result  # 返回之前的结果，不重复执行

    # 执行复制...
    result = len(copied_cases)

    # 设置幂等结果
    if idempotency_key:
        IdempotencyService.set_result('batch_copy', user.id, data_hash, result)

    return result
```

### 5.3 权限缓存

```python
def get_user_permissions(project_id, user):
    """获取用户在项目中的权限（带缓存）"""
    cache_key = f'project_permissions_{project_id}_{user.id}'
    permissions = cache.get(cache_key)

    if permissions is None:
        permissions = _calculate_permissions(project_id, user)
        cache.set(cache_key, permissions, 300)  # 5分钟

    return permissions

def update_member_role(project_id, user_id, new_role):
    """更新成员角色 - 清除缓存"""
    member.role = new_role
    member.save()

    # 清除缓存
    cache.delete(f'project_permissions_{project_id}_{user_id}')
```

### 5.4 限流缓存

**文件位置**: `apps/core/middleware/rate_limit.py`

```python
class RateLimitMiddleware:
    def __call__(self, request):
        # 登录接口限流
        if request.path in self.login_paths and request.method == 'POST':
            return self._handle_login_rate_limit(request)

        # API限流
        if request.path.startswith('/api/'):
            client_ip = self._get_client_ip(request)
            cache_key = f'rate_limit_api_{client_ip}'
            request_count = cache.get(cache_key, 0)

            if request_count >= self.auth_rate_limit:
                return JsonResponse({'code': 429, 'message': '请求过于频繁'}, status=429)

            cache.set(cache_key, request_count + 1, self.window_seconds)

        return self.get_response(request)

    def _handle_login_rate_limit(self, request):
        """登录限流 - 防暴力破解"""
        client_ip = self._get_client_ip(request)

        # 检查是否被锁定
        lockout_key = f'login_lockout_{client_ip}'
        lockout_until = cache.get(lockout_key)
        if lockout_until:
            return JsonResponse({'message': '账户已被锁定'}, status=429)

        # 统计登录尝试
        attempts_key = f'login_attempts_{client_ip}'
        attempts = cache.get(attempts_key, 0)

        if attempts >= self.login_max_attempts:
            # 锁定账户
            cache.set(lockout_key, time.time() + 300, 300)
            cache.delete(attempts_key)
            return JsonResponse({'message': '登录尝试过多'}, status=429)

        cache.set(attempts_key, attempts + 1, 60)
        return self.get_response(request)
```

---

## 六、Python安全实践

### 6.1 密码安全

```python
# Django自动使用PBKDF2加密
class User(AbstractUser):
    # Django的AbstractUser自动处理密码加密
    # 使用PBKDF2 + SHA256，迭代次数默认600000次
    pass

# 密码验证
user = authenticate(username=username, password=password)  # 自动验证

# 密码重置令牌
import secrets
token = secrets.token_urlsafe(32)  # 加密安全的随机令牌
```

### 6.2 防用户枚举攻击

```python
@staticmethod
def send_password_reset_email(email):
    """发送密码重置邮件

    安全说明：无论邮箱是否存在，都返回成功消息，防止用户枚举攻击
    """
    if not email:
        return  # 不抛出异常

    user = User.objects.filter(email=email).first()
    if not user:
        logger.info(f"密码重置请求：邮箱 {email} 未注册")
        return  # 静默返回，不报错

    # 发送邮件...
```

### 6.3 测试账号安全清理

```python
@api_view(['DELETE'])
def cleanup_test_user_view(request):
    """清理测试用户

    安全检查：
    1. 只删除test_开头的用户名
    2. 时间戳格式验证
    """
    username = request.query_params.get('username')

    # 安全检查：只能删除test_开头的
    if not username.startswith('test_'):
        return StandardResponse(message='只能删除测试账号', code=403)

    # 时间戳格式验证
    import re
    if not re.match(r'test_\d{8}_\d{6}_[a-z0-9]{4}$', username):
        return StandardResponse(message='用户名格式不符合规范', code=400)

    user = User.objects.get(username=username)
    user.delete()
    return StandardResponse(message=f'测试用户 {username} 已删除')
```

---

## 七、技术选型总结

### 7.1 Python技术清单

| 技术点 | 使用方式 | 应用场景 |
|--------|---------|---------|
| **装饰器** | 自定义权限装饰器、@wraps | 权限控制、日志记录 |
| **@staticmethod** | Service层静态方法 | 业务逻辑处理 |
| **@classmethod** | Repository基类 | 数据访问抽象 |
| **@property** | 模型属性访问器 | 计算属性 |
| **@transaction.atomic** | 事务装饰器 | 数据一致性保证 |
| **索引** | 单字段、复合索引 | 查询性能优化 |
| **select_related** | JOIN预加载 | 解决N+1问题 |
| **prefetch_related** | IN查询预加载 | 多对多关系 |
| **Q对象** | 复杂OR/AND查询 | 多条件搜索 |
| **F对象** | 字段引用 | 原子更新 |
| **annotate/aggregate** | 聚合查询 | 统计计算 |
| **bulk_create/update** | 批量操作 | 性能优化 |
| **Django缓存** | locmem/Redis | 幂等性、限流、权限缓存 |
| **default_storage** | 文件存储 | 头像上传 |
| **secrets模块** | 安全随机数 | 令牌生成 |

### 7.2 为什么选择这些技术？

| 需求 | 技术选择 | 不选其他方案的原因 |
|------|---------|-------------------|
| 权限控制 | 自定义装饰器 | 比中间件粒度更细，比基类更灵活 |
| 数据一致性 | @transaction.atomic | 比手动管理事务更简洁 |
| 查询优化 | select_related/prefetch_related | 比原生SQL更易维护 |
| 批量操作 | bulk_create/update | 比循环save()快10-100倍 |
| 限流 | Django缓存 | 比Redis简单，开发环境够用 |
| 文件上传 | default_storage | 支持多种存储后端，易于切换 |

---

*文档版本：v1.0*
*最后更新：2026年5月28日*
