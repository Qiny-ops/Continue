"""
角色服务
"""

from django.db.models import Count
from apps.users.models import Role
from apps.core.exceptions import NotFoundError, ValidationError, BusinessError
from apps.core.permissions import SYSTEM_PERMISSIONS, SYSTEM_ROLE_DEFAULTS


# 系统权限定义（用于前端展示）
SYSTEM_PERMISSION_LIST = [
    {'code': code, 'name': name}
    for code, name in SYSTEM_PERMISSIONS.items()
]


class RoleService:
    """角色服务"""

    @staticmethod
    def get_roles_with_user_count():
        """获取角色列表（包含用户数量）"""
        return Role.objects.annotate(
            user_count=Count('users')
        ).order_by('id')

    @staticmethod
    def get_role_by_code(code):
        """根据编码获取角色"""
        try:
            return Role.objects.get(code=code)
        except Role.DoesNotExist:
            raise NotFoundError('角色不存在')

    @staticmethod
    def get_role_by_id(role_id):
        """根据ID获取角色"""
        try:
            return Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise NotFoundError('角色不存在')

    @staticmethod
    def create_role(name, code, description='', role_type='default'):
        """创建角色"""
        if not name or not code:
            raise ValidationError('角色名称和编码不能为空')

        if Role.objects.filter(code=code).exists():
            raise BusinessError('角色编码已存在')

        if Role.objects.filter(name=name).exists():
            raise BusinessError('角色名称已存在')

        # 根据角色代码获取默认权限
        default_permissions = SYSTEM_ROLE_DEFAULTS.get(code, [])

        role = Role.objects.create(
            name=name,
            code=code,
            description=description,
            type=role_type,
            status='active',
            permissions=default_permissions
        )
        return role

    @staticmethod
    def update_role(role_id, data):
        """更新角色"""
        role = RoleService.get_role_by_id(role_id)

        # 系统角色（admin/user）不允许修改编码
        if role.code in ['admin', 'user']:
            if 'code' in data and data['code'] != role.code:
                raise BusinessError('系统角色不允许修改编码')

        allowed_fields = ['name', 'description', 'status']
        for field in allowed_fields:
            if field in data:
                setattr(role, field, data[field])

        role.save()
        return role

    @staticmethod
    def delete_role(role_id):
        """删除角色"""
        role = RoleService.get_role_by_id(role_id)

        # 系统角色不允许删除
        if role.code in ['admin', 'user']:
            raise BusinessError('系统角色不允许删除')

        # 检查是否有用户使用此角色
        user_count = role.users.count()
        if user_count > 0:
            raise BusinessError(f'该角色下有 {user_count} 个用户，无法删除')

        role.delete()
        return True

    @staticmethod
    def get_role_permissions(role_id):
        """
        获取角色权限列表

        从 Role.permissions JSONField 读取，如果为空则使用默认映射。

        Args:
            role_id: 角色ID

        Returns:
            list: 权限代码列表
        """
        role = RoleService.get_role_by_id(role_id)

        # 从 JSONField 读取
        if role.permissions:
            return role.permissions

        # 如果为空，使用默认权限映射
        return SYSTEM_ROLE_DEFAULTS.get(role.code, [])

    @staticmethod
    def update_role_permissions(role_id, permissions):
        """
        更新角色权限

        将权限列表写入 Role.permissions JSONField。
        系统角色 admin 的权限固定为全部，不允许修改。

        Args:
            role_id: 角色ID
            permissions: 权限代码列表

        Returns:
            list: 更新后的权限列表
        """
        role = RoleService.get_role_by_id(role_id)

        # admin 角色权限固定为全部
        if role.code == 'admin':
            raise BusinessError('系统管理员角色权限不允许修改')

        # 验证权限代码合法性
        valid_codes = set(SYSTEM_PERMISSIONS.keys())
        invalid_codes = set(permissions) - valid_codes
        if invalid_codes:
            raise BusinessError(f'无效的权限代码: {", ".join(invalid_codes)}')

        role.permissions = permissions
        role.save(update_fields=['permissions', 'updated_at'])
        return permissions

    @staticmethod
    def get_system_permissions():
        """
        获取系统权限列表

        Returns:
            list: 系统权限列表
        """
        return SYSTEM_PERMISSION_LIST
