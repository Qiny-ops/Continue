"""
用户模块 - 常量定义
"""

# 用户状态
class UserStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'

    CHOICES = [
        (ACTIVE, '正常'),
        (INACTIVE, '未激活'),
        (SUSPENDED, '已停用'),
    ]


# 系统角色代码
class SystemRoleCode:
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'


# 角色类型
class RoleType:
    SYSTEM = 'system'
    PROJECT = 'project'

    CHOICES = [
        (SYSTEM, '系统角色'),
        (PROJECT, '项目角色'),
    ]


# 角色状态
class RoleStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    CHOICES = [
        (ACTIVE, '启用'),
        (INACTIVE, '禁用'),
    ]


# 权限类型
class PermissionType:
    SYSTEM = 'system'
    PROJECT = 'project'

    CHOICES = [
        (SYSTEM, '系统权限'),
        (PROJECT, '项目权限'),
    ]


# Token 过期时间（小时）
JWT_EXPIRATION_HOURS = 24

# 密码最小长度
PASSWORD_MIN_LENGTH = 8

# 用户名最小/最大长度
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

# 验证码过期时间（秒）
VERIFICATION_CODE_EXPIRY = 300

# 头像上传路径
AVATAR_UPLOAD_PATH = 'avatars/'

# 头像最大尺寸（字节）
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2MB
