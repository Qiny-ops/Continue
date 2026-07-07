"""
权限服务

由于 Permission 模型已删除，权限现在通过硬编码方式管理。
项目级权限由 ProjectRole.permissions JSONField 存储。
"""

from apps.core.permissions import PROJECT_PERMISSIONS, get_default_permissions
from apps.core.exceptions import ValidationError, NotFoundError, BusinessError
from apps.core.permissions import is_system_admin


class PermissionService:
    """权限服务"""

    @staticmethod
    def get_permissions_and_groups():
        """获取权限列表和分组"""
        permissions_list = []
        for code, name in PROJECT_PERMISSIONS.items():
            # 根据权限代码确定分组
            if 'testcase' in code or 'test' in code:
                group = 'testcase'
            elif 'bug' in code:
                group = 'bug'
            elif 'member' in code:
                group = 'member'
            elif 'project' in code or 'settings' in code:
                group = 'project'
            elif 'api' in code:
                group = 'api'
            elif 'report' in code:
                group = 'report'
            else:
                group = 'other'
            permissions_list.append({'key': code, 'name': name, 'group': group})

        group_names = {
            'project': '项目管理',
            'member': '成员管理',
            'testcase': '测试用例',
            'api': '接口管理',
            'bug': '缺陷管理',
            'report': '报告中心',
        }
        groups = [{'key': g, 'name': n} for g, n in group_names.items()]

        return {'permissions': permissions_list, 'groups': groups}

    @staticmethod
    def create_permission(name, code, type='project', description='', operator=None):
        """创建权限 - 已废弃，权限现在是硬编码的"""
        raise BusinessError('权限系统已重构，不再支持动态创建权限')

    @staticmethod
    def update_permission(permission_id, data, operator=None):
        """更新权限 - 已废弃"""
        raise BusinessError('权限系统已重构，不再支持动态更新权限')

    @staticmethod
    def delete_permission(permission_id, operator=None):
        """删除权限 - 已废弃"""
        raise BusinessError('权限系统已重构，不再支持动态删除权限')