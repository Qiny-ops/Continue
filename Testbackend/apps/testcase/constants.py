"""
测试用例模块 - 常量定义
"""

# 用例库状态
class RepositoryStatus:
    ACTIVE = 'active'
    ARCHIVED = 'archived'

    CHOICES = [
        (ACTIVE, '活跃'),
        (ARCHIVED, '已归档'),
    ]


# 版本状态
class VersionStatus:
    DRAFT = 'draft'
    ACTIVE = 'active'
    RELEASED = 'released'
    ARCHIVED = 'archived'

    CHOICES = [
        (DRAFT, '草稿'),
        (ACTIVE, '活跃'),
        (RELEASED, '已发布'),
        (ARCHIVED, '已归档'),
    ]


# 用例优先级
class TestCasePriority:
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'

    CHOICES = [
        (CRITICAL, '紧急'),
        (HIGH, '高'),
        (MEDIUM, '中'),
        (LOW, '低'),
    ]


# 自动化状态
class AutomationStatus:
    MANUAL = 'manual'
    AUTOMATED = 'automated'
    PARTIAL = 'partial'

    CHOICES = [
        (MANUAL, '手工测试'),
        (AUTOMATED, '自动化测试'),
        (PARTIAL, '半自动化'),
    ]


# 评审状态
class ReviewStatus:
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    NEEDS_REVISION = 'needs_revision'

    CHOICES = [
        (PENDING, '待评审'),
        (APPROVED, '已通过'),
        (REJECTED, '已拒绝'),
        (NEEDS_REVISION, '需修改'),
    ]


# 执行结果
class ExecutionResult:
    PASSED = 'passed'
    FAILED = 'failed'
    BLOCKED = 'blocked'
    SKIPPED = 'skipped'

    CHOICES = [
        (PASSED, '通过'),
        (FAILED, '失败'),
        (BLOCKED, '阻塞'),
        (SKIPPED, '跳过'),
    ]


# 模块名称最大长度
MODULE_NAME_MAX_LENGTH = 100

# 用例标题最大长度
TESTCASE_TITLE_MAX_LENGTH = 200

# 步骤描述最大长度
STEP_DESCRIPTION_MAX_LENGTH = 1000

# 预期结果最大长度
EXPECTED_RESULT_MAX_LENGTH = 1000

# 每页默认用例数量
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
