"""
用户模块 - 序列化器

提供用户相关的数据序列化。
"""

from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    """用户基础序列化器"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField()
    system_role = serializers.CharField(required=False, allow_null=True)
    system_role_name = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()
    last_login_time = serializers.DateTimeField(required=False, allow_null=True)


class UserListSerializer(serializers.Serializer):
    """用户列表序列化器"""
    users = UserSerializer(many=True)
    total = serializers.IntegerField()


class UserProfileSerializer(serializers.Serializer):
    """用户资料序列化器"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField()
    system_role = serializers.CharField(required=False, allow_null=True)
    system_role_name = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()
    last_login_time = serializers.DateTimeField(required=False, allow_null=True)


class UserCreateSerializer(serializers.Serializer):
    """用户创建序列化器"""
    username = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128)
    name = serializers.CharField(max_length=50)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)


class UserUpdateSerializer(serializers.Serializer):
    """用户更新序列化器"""
    name = serializers.CharField(required=False, max_length=50)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    avatar = serializers.CharField(required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField()
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    """登录响应序列化器"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True)
    system_role = serializers.CharField(required=False, allow_null=True)
    token = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8, max_length=128)


class RoleSerializer(serializers.Serializer):
    """角色序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    user_count = serializers.IntegerField(required=False)


class PermissionSerializer(serializers.Serializer):
    """权限序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    type = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False)
