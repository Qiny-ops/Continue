"""
用户服务
"""

import re
import logging
import uuid
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.conf import settings

from apps.users.models import User, Role
from apps.core.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessError
)
from apps.core.permissions import is_system_admin

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""

    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError('用户不存在')

    @staticmethod
    def get_users_list(filters=None, page=1, limit=10):
        """获取用户列表"""
        filters = filters or {}
        queryset = User.objects.all().select_related('system_role')

        keyword = filters.get('keyword', '')
        if keyword:
            queryset = queryset.filter(
                models.Q(username__icontains=keyword) |
                models.Q(name__icontains=keyword) |
                models.Q(email__icontains=keyword)
            )

        status_filter = filters.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        role_filter = filters.get('role', '')
        if role_filter:
            queryset = queryset.filter(system_role__code=role_filter)

        total = queryset.count()
        offset = (page - 1) * limit
        users = queryset[offset:offset + limit]

        return {
            'users': users,
            'total': total
        }

    @staticmethod
    @transaction.atomic
    def create_user(username, password, email, name=None, phone=''):
        """创建用户

        并发安全：通过捕获数据库完整性错误处理竞态条件。
        即使多个请求同时通过存在性检查，数据库唯一约束会确保最终一致性。
        """
        from django.db import IntegrityError

        if not all([username, password, email]):
            raise ValidationError('用户名、密码和邮箱不能为空')

        is_valid, error_msg = PasswordService.validate_strength(password)
        if not is_valid:
            raise ValidationError(error_msg)

        try:
            default_role = Role.get_default_role()

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                name=name or username,
                phone=phone,
                system_role=default_role,
                status='active'
            )
            return user

        except IntegrityError as e:
            error_msg = str(e).lower()
            if 'username' in error_msg or '用户名' in error_msg:
                raise BusinessError('用户名已存在')
            elif 'email' in error_msg or '邮箱' in error_msg:
                raise BusinessError('邮箱已被注册')
            else:
                # 其他完整性错误，重新检查
                if User.objects.filter(username=username).exists():
                    raise BusinessError('用户名已存在')
                if User.objects.filter(email=email).exists():
                    raise BusinessError('邮箱已被注册')
                raise BusinessError('创建用户失败，请稍后重试')

    @staticmethod
    def update_user(user, data):
        """更新用户信息"""
        allowed_fields = ['name', 'phone']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        user.save()
        return user


class PasswordService:
    """密码服务"""

    COMMON_PASSWORDS = [
        'password', 'Password1', 'Password123', 'Admin123', 'Qwer1234',
        'Abcd1234', 'Test1234', 'Welcome1', 'P@ssw0rd', 'Passw0rd'
    ]

    @staticmethod
    def validate_strength(password):
        """验证密码强度"""
        if len(password) < 8:
            return False, '密码长度至少为8位'
        if len(password) > 128:
            return False, '密码长度不能超过128位'
        if not re.search(r'[A-Z]', password):
            return False, '密码必须包含至少一个大写字母'
        if not re.search(r'[a-z]', password):
            return False, '密码必须包含至少一个小写字母'
        if not re.search(r'\d', password):
            return False, '密码必须包含至少一个数字'
        if password.lower() in [p.lower() for p in PasswordService.COMMON_PASSWORDS]:
            return False, '密码过于简单，请使用更复杂的密码'

        return True, ''

    @staticmethod
    def change_password(user, old_password, new_password):
        """修改密码"""
        if not old_password or not new_password:
            raise ValidationError('旧密码和新密码不能为空')

        if not user.check_password(old_password):
            raise ValidationError('旧密码错误')

        is_valid, error_msg = PasswordService.validate_strength(new_password)
        if not is_valid:
            raise ValidationError(error_msg)

        user.set_password(new_password)
        user.save()


class EmailService:
    """邮箱服务"""

    @staticmethod
    def send_verification_code(email, purpose='update_email'):
        """发送验证码"""
        if not email:
            raise ValidationError('邮箱不能为空')

        try:
            validate_email(email)
        except DjangoValidationError:
            raise ValidationError('邮箱格式不正确')

        code = get_random_string(6, allowed_chars='0123456789')

        cache_key = f'email_code_{purpose}_{email}'
        cache.set(cache_key, code, timeout=300)

        subject = '验证码'
        message = f'您的验证码是：{code}，有效期5分钟。'
        from_email = settings.EMAIL_HOST_USER

        try:
            send_mail(subject, message, from_email, [email])
        except Exception as e:
            logger.warning(f'发送验证码邮件失败: {str(e)}')
            raise BusinessError('发送验证码失败，请稍后重试')

        return True

    @staticmethod
    def verify_code(email, code, purpose='update_email'):
        """验证验证码"""
        cache_key = f'email_code_{purpose}_{email}'
        cached_code = cache.get(cache_key)

        if not cached_code or cached_code != code:
            return False

        cache.delete(cache_key)
        return True


class UserServiceExtended:
    """用户扩展服务"""

    # 用户状态合法转换路径
    # pending -> active: 需要管理员审核或邮箱验证
    # active -> disabled/suspended: 管理员操作
    # disabled/suspended -> active: 管理员操作
    # disabled -> deleted: 管理员操作（需要先处理关联数据）
    VALID_STATUS_TRANSITIONS = {
        'pending': ['active', 'disabled'],
        'active': ['disabled', 'suspended'],
        'disabled': ['active', 'deleted'],
        'suspended': ['active', 'disabled'],
    }

    @staticmethod
    def update_user_role(user_id, role_code, operator):
        """更新用户角色"""
        if not is_system_admin(operator):
            raise BusinessError('无权限更新用户角色')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError('用户不存在')

        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            raise NotFoundError('角色不存在')

        user.system_role = role
        user.save()
        return user

    @staticmethod
    def update_user_status(user_id, status, operator):
        """更新用户状态

        业务逻辑：
        1. 只有管理员可以更新用户状态
        2. 状态转换必须遵循合法路径
        3. 不能更新自己的状态
        """
        if not is_system_admin(operator):
            raise BusinessError('无权限更新用户状态')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError('用户不存在')

        # 不能更新自己的状态
        if user.id == operator.id:
            raise BusinessError('不能更新自己的状态')

        valid_statuses = [choice[0] for choice in User.STATUS_CHOICES]
        if status not in valid_statuses:
            raise ValidationError('无效的状态')

        # 验证状态转换是否合法
        current_status = user.status
        if current_status not in UserServiceExtended.VALID_STATUS_TRANSITIONS:
            raise ValidationError(f'当前状态 {current_status} 无法转换')

        allowed_transitions = UserServiceExtended.VALID_STATUS_TRANSITIONS[current_status]
        if status not in allowed_transitions:
            raise ValidationError(f'状态 {current_status} 不能直接转换为 {status}，允许的转换: {", ".join(allowed_transitions)}')

        user.status = status
        user.save()
        return user

    @staticmethod
    def search_users(keyword, limit=20):
        """搜索用户

        安全说明：
        1. 只返回基本字段，不暴露敏感信息（邮箱、手机等）
        2. 限制最大返回数量为 100，防止大量数据请求
        """
        # 限制最大返回数量
        max_limit = 100
        limit = min(limit, max_limit) if limit > 0 else 20

        queryset = User.objects.filter(status='active').select_related('system_role')

        if keyword:
            queryset = queryset.filter(
                models.Q(username__icontains=keyword) |
                models.Q(name__icontains=keyword)
            )

        users = queryset[:limit]

        return [
            {
                'id': user.id,
                'name': user.name or user.username,
                'username': user.username,
                'avatar': user.avatar,
            }
            for user in users
        ]

    @staticmethod
    def upload_avatar(user, avatar_file):
        """上传头像"""
        if avatar_file.size > 2 * 1024 * 1024:
            raise ValidationError('头像文件大小不能超过2MB')

        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            raise ValidationError('只支持 JPG、PNG、GIF 格式的图片')

        ext = avatar_file.name.split('.')[-1].lower()
        filename = f'avatars/{user.id}_{uuid.uuid4().hex[:8]}.{ext}'

        saved_path = default_storage.save(filename, avatar_file)
        user.avatar = saved_path
        user.save()

        return saved_path

    @staticmethod
    def send_password_reset_email(email):
        """发送密码重置邮件

        安全说明：无论邮箱是否存在，都返回成功消息，防止用户枚举攻击。
        实际邮件只发送给存在的用户，但响应不区分。
        """
        if not email:
            # 不抛出异常，静默返回，防止枚举
            return

        user = User.objects.filter(email=email).first()
        if not user:
            # 用户不存在时静默返回，不发送邮件，但也不报错
            logger.info(f"密码重置请求：邮箱 {email} 未注册")
            return

        # 使用加密安全的随机生成器
        import secrets
        token = secrets.token_urlsafe(32)
        user.reset_password_token = token
        user.reset_password_expire = timezone.now() + timezone.timedelta(hours=24)
        user.save()

        reset_url = f'{settings.FRONTEND_URL}/reset-password/{token}/'

        try:
            send_mail(
                subject='重置密码',
                message=f'请点击以下链接重置密码：\n{reset_url}\n\n此链接将在24小时后失效。',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email]
            )
            logger.info(f"密码重置邮件已发送至 {email}")
        except Exception as e:
            logger.warning(f'发送重置密码邮件失败: {str(e)}')
            # 不抛出异常，防止通过错误信息枚举用户

    @staticmethod
    def reset_password(token, new_password):
        """重置密码"""
        if not new_password:
            raise ValidationError('新密码不能为空')

        user = User.objects.filter(reset_password_token=token).first()
        if not user:
            raise ValidationError('无效的重置密码链接')

        if user.reset_password_expire < timezone.now():
            raise ValidationError('重置密码链接已过期')

        is_valid, error_msg = PasswordService.validate_strength(new_password)
        if not is_valid:
            raise ValidationError(error_msg)

        user.set_password(new_password)
        user.reset_password_token = None
        user.reset_password_expire = None
        user.save()

    @staticmethod
    def update_email(user, new_email, code):
        """更新邮箱"""
        if not new_email or not code:
            raise ValidationError('邮箱和验证码不能为空')

        if not EmailService.verify_code(new_email, code, 'update_email'):
            raise ValidationError('验证码错误或已过期')

        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            raise BusinessError('该邮箱已被其他用户使用')

        user.email = new_email
        user.save()

    @staticmethod
    def check_user_can_be_deleted(user):
        """检查用户是否可以被删除

        返回: (can_delete, related_info)
        - can_delete: 是否可以删除
        - related_info: 关联数据信息（如果不能删除）
        """
        from apps.projects.models import Project, ProjectMember
        from apps.testcase.models import TestCase, TestCaseRepository

        related_info = []

        # 检查用户拥有的项目
        owned_projects = Project.objects.filter(owner=user).count()
        if owned_projects > 0:
            related_info.append(f'拥有 {owned_projects} 个项目')

        # 检查用户创建的测试用例
        created_cases = TestCase.objects.filter(created_by=user).count()
        if created_cases > 0:
            related_info.append(f'创建了 {created_cases} 个测试用例')

        # 检查用户创建的用例库
        created_repos = TestCaseRepository.objects.filter(created_by=user).count()
        if created_repos > 0:
            related_info.append(f'创建了 {created_repos} 个用例库')

        can_delete = len(related_info) == 0
        return can_delete, related_info

    @staticmethod
    @transaction.atomic
    def delete_user(user_id, operator, transfer_to_user_id=None):
        """删除用户

        业务逻辑：
        1. 只有管理员可以删除用户
        2. 不能删除自己
        3. 如果用户有关联数据，需要先转移或指定接收者
        4. 如果指定了 transfer_to_user_id，将关联数据转移给该用户

        Args:
            user_id: 要删除的用户ID
            operator: 操作者
            transfer_to_user_id: 数据转移目标用户ID（可选）

        Returns:
            deleted_username: 被删除的用户名
            transferred_count: 转移的数据数量
        """
        if not is_system_admin(operator):
            raise BusinessError('无权限删除用户')

        if user_id == operator.id:
            raise BusinessError('不能删除自己')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError('用户不存在')

        # 检查是否有关联数据
        can_delete, related_info = UserServiceExtended.check_user_can_be_deleted(user)

        if not can_delete:
            if transfer_to_user_id:
                # 转移数据给指定用户
                try:
                    transfer_to_user = User.objects.get(id=transfer_to_user_id)
                except User.DoesNotExist:
                    raise NotFoundError('目标用户不存在')

                from apps.projects.models import Project
                from apps.testcase.models import TestCase, TestCaseRepository

                transferred_count = 0

                # 转移项目所有权
                projects = Project.objects.filter(owner=user)
                for project in projects:
                    project.owner = transfer_to_user
                    project.save()
                    transferred_count += 1

                # 转移测试用例创建者
                cases = TestCase.objects.filter(created_by=user)
                cases.update(created_by=transfer_to_user, updated_by=transfer_to_user)
                transferred_count += cases.count()

                # 转移用例库创建者
                repos = TestCaseRepository.objects.filter(created_by=user)
                repos.update(created_by=transfer_to_user)
                transferred_count += repos.count()

                logger.info(f"用户 {operator.username} 删除用户 {user.username}，转移 {transferred_count} 条数据给 {transfer_to_user.username}")
            else:
                # 没有指定转移目标，提示用户处理
                raise BusinessError(
                    f'该用户有关联数据：{", ".join(related_info)}。'
                    '请先转移这些数据或指定数据接收者。'
                )

        username = user.username
        user.delete()

        return username

    @staticmethod
    @transaction.atomic
    def batch_delete_users(user_ids, operator):
        """批量删除用户

        Args:
            user_ids: 要删除的用户ID列表
            operator: 操作者

        Returns:
            deleted_count: 成功删除的数量
            failed_users: 删除失败的用户信息列表
        """
        if not is_system_admin(operator):
            raise BusinessError('无权限删除用户')

        deleted_count = 0
        failed_users = []

        for user_id in user_ids:
            if user_id == operator.id:
                failed_users.append({'id': user_id, 'reason': '不能删除自己'})
                continue

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                failed_users.append({'id': user_id, 'reason': '用户不存在'})
                continue

            # 检查是否有关联数据
            can_delete, related_info = UserServiceExtended.check_user_can_be_deleted(user)

            if not can_delete:
                failed_users.append({
                    'id': user_id,
                    'username': user.username,
                    'reason': f'有关联数据：{", ".join(related_info)}'
                })
                continue

            user.delete()
            deleted_count += 1

        logger.info(f"用户 {operator.username} 批量删除用户，成功 {deleted_count} 个，失败 {len(failed_users)} 个")

        return deleted_count, failed_users
