"""
项目模块 - 常量定义
"""

# 项目状态
class ProjectStatus:
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    DELETED = 'deleted'

    CHOICES = [
        (ACTIVE, '进行中'),
        (ARCHIVED, '已归档'),
        (DELETED, '已删除'),
    ]


# 项目类型
class ProjectType:
    SOFTWARE = 'software'
    HARDWARE = 'hardware'
    MIXED = 'mixed'

    CHOICES = [
        (SOFTWARE, '软件项目'),
        (HARDWARE, '硬件项目'),
        (MIXED, '软硬结合项目'),
    ]


# 项目成员角色
class MemberRole:
    OWNER = 'owner'
    ADMIN = 'admin'
    DEVELOPER = 'developer'
    TESTER = 'tester'
    VIEWER = 'viewer'

    CHOICES = [
        (OWNER, '所有者'),
        (ADMIN, '管理员'),
        (DEVELOPER, '开发人员'),
        (TESTER, '测试人员'),
        (VIEWER, '访客'),
    ]


# 成员状态
class MemberStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    PENDING = 'pending'

    CHOICES = [
        (ACTIVE, '已激活'),
        (INACTIVE, '未激活'),
        (PENDING, '待确认'),
    ]


# 项目标识符长度
PROJECT_IDENTIFIER_MIN_LENGTH = 2
PROJECT_IDENTIFIER_MAX_LENGTH = 20

# 项目名称长度
PROJECT_NAME_MAX_LENGTH = 100

# 项目描述最大长度
PROJECT_DESCRIPTION_MAX_LENGTH = 500

# 每页默认项目数量
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
