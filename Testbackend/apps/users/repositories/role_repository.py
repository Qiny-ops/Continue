"""
角色数据访问层
"""

from django.db import models
from apps.users.models import Role


class RoleRepository:
    """角色数据访问层"""

    @staticmethod
    def get_all():
        """获取所有角色"""
        return Role.objects.all().order_by('id')

    @staticmethod
    def get_all_with_user_count():
        """获取所有角色及其用户数量"""
        return Role.objects.annotate(
            user_count=models.Count('users')
        ).order_by('id')

    @staticmethod
    def get_by_id(role_id):
        """根据ID获取角色"""
        return Role.objects.filter(id=role_id).first()

    @staticmethod
    def get_by_code(code):
        """根据代码获取角色"""
        return Role.objects.filter(code=code).first()

    @staticmethod
    def get_default_role():
        """获取默认角色（访客）"""
        role = Role.objects.filter(code='guest').first()
        if not role:
            role = Role.objects.create(
                name='访客',
                code='guest',
                type='default',
                description='默认访客角色，拥有基本查看权限',
                status='active'
            )
        return role

    @staticmethod
    def create_role(name, code, type='default', description='', status='active'):
        """创建角色"""
        return Role.objects.create(
            name=name,
            code=code,
            type=type,
            description=description,
            status=status
        )

    @staticmethod
    def update_role(role, **kwargs):
        """更新角色"""
        for attr, value in kwargs.items():
            setattr(role, attr, value)
        role.save()
        return role

    @staticmethod
    def delete_role(role_id):
        """删除角色"""
        return Role.objects.filter(id=role_id).delete()
