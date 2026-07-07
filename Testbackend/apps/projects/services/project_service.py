"""
项目服务
"""

import logging
from django.conf import settings
from django.db import transaction
from django.db.models import Count, F

from apps.core.permissions import (
    is_system_admin, get_default_permissions, has_project_permission,
    ProjectPermissionService
)
from apps.core.exceptions import ValidationError, BusinessError, NotFoundError
from apps.projects.repositories import ProjectRepository, ProjectMemberRepository, ProjectRoleRepository
from apps.users.repositories import UserRepository
from apps.projects.models import Project, ProjectMember, ProjectRole

logger = logging.getLogger(__name__)


class ProjectService:
    """项目服务"""

    @staticmethod
    def get_project_list(user, filters=None, page=1, limit=10):
        """获取项目列表"""
        project_ids = ProjectRepository.get_user_projects(user)
        queryset = ProjectRepository.get_projects_by_ids(project_ids)

        if filters:
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            if filters.get('type'):
                queryset = queryset.filter(type=filters['type'])
            if filters.get('keyword'):
                queryset = queryset.filter(name__icontains=filters['keyword'])
            if filters.get('is_favorite'):
                favorite_ids = ProjectMemberRepository.get_user_favorite_projects(user).values_list(
                    'project_id', flat=True
                )
                queryset = queryset.filter(id__in=favorite_ids)

        total = queryset.count()
        offset = (page - 1) * limit
        projects = list(queryset[offset:offset + limit])

        # 获取用户在各项目中的角色和收藏信息
        member_queryset = ProjectMemberRepository.get_user_member_projects(user)
        member_data = {}
        for member in member_queryset:
            member_data[member.project_id] = (member.role, member.is_favorite)

        projects_data = []
        for project in projects:
            member_info = member_data.get(project.id)
            is_owner = project.owner_id == user.id

            if member_info:
                role, is_favorite = member_info[0], member_info[1]
            else:
                role, is_favorite = 'viewer', False

            # 判断用户是否是项目管理员（owner 或 admin 角色）
            is_admin = is_owner or role == 'admin'
            projects_data.append(ProjectService.build_project_data(project, is_favorite, is_admin, role, is_owner))

        return {'projects': projects_data, 'total': total}

    @staticmethod
    def get_project(project_identifier, user):
        """获取项目详情"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                return None, '无权限访问此项目'

        member = ProjectMemberRepository.get_member(project, user)
        is_favorite = member.is_favorite if member else False

        project_data = ProjectService.build_project_data(project, is_favorite)
        project_data['createdAt'] = project.created_at.isoformat()
        project_data['updatedAt'] = project.updated_at.isoformat()

        return project_data, None

    @staticmethod
    def create_project(user, data):
        """创建项目"""
        name = data.get('name')
        code = data.get('code')

        if not name:
            return None, '项目名称不能为空'
        if not code:
            return None, '项目标识不能为空'

        valid_types = [choice[0] for choice in Project.TYPE_CHOICES]
        if data.get('type') and data['type'] not in valid_types:
            return None, '无效的项目类型'

        valid_statuses = [choice[0] for choice in Project.STATUS_CHOICES]
        if data.get('status') and data['status'] not in valid_statuses:
            return None, '无效的项目状态'

        with transaction.atomic():
            project = ProjectRepository.create_project(
                name=name,
                code=code,
                owner=user,
                description=data.get('description', ''),
                type=data.get('type', 'web'),
                status=data.get('status', 'active')
            )

            ProjectMemberRepository.add_member(project, user, role='admin')
            ProjectRoleRepository.create_default_roles(project, get_default_permissions)

            # 自动创建默认用例库和版本
            try:
                from apps.testcase.models import TestCaseRepository, TestCaseVersion

                # 创建默认用例库
                default_repository = TestCaseRepository.objects.create(
                    name=f'{project.name} 用例库',
                    project=project,
                    description=f'{project.name} 项目的默认用例库',
                    is_default=True,
                    created_by=user
                )

                # 创建默认版本
                TestCaseVersion.objects.create(
                    repository=default_repository,
                    name='v1.0',
                    description='初始版本',
                    status='active',
                    is_default=True,
                    created_by=user
                )
            except Exception as e:
                logger.warning(f"自动创建默认用例库和版本失败: {str(e)}")

            # 自动创建知识库
            try:
                from apps.knowledge.repositories.weknora_repository import weknora_repository
                if weknora_repository.api_key:
                    kb_name = f"{project.name} 知识库"
                    kb_data = {
                        'name': kb_name,
                        'description': f"项目 {project.name} 的知识库",
                        'type': 'document',
                        'storage_provider_config': {'provider': 'local'},
                    }
                    # 设置默认模型ID（需要在环境变量中配置）
                    embedding_model_id = getattr(settings, 'WEKNORA_DEFAULT_EMBEDDING_MODEL_ID', '')
                    llm_model_id = getattr(settings, 'WEKNORA_DEFAULT_LLM_MODEL_ID', '')
                    if embedding_model_id:
                        kb_data['embedding_model_id'] = embedding_model_id
                    if llm_model_id:
                        kb_data['summary_model_id'] = llm_model_id

                    result = weknora_repository.create_knowledge_base(kb_data)
                    if result.get('success'):
                        kb_result = result.get('data', {})
                        project.knowledge_base_id = kb_result.get('id')
                        project.knowledge_base_name = kb_name
                        project.save(update_fields=['knowledge_base_id', 'knowledge_base_name'])
            except ImportError:
                logger.debug("WeKnora repository not available")
            except Exception as e:
                logger.warning(f"自动创建知识库失败: {str(e)}")

        return project, None

    @staticmethod
    def update_project(project_identifier, user, data):
        """更新项目"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, role, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member or role not in ['owner', 'admin']:
                return None, '无权限更新此项目'

        update_fields = {}
        field_mapping = {
            'name': 'name', 'code': 'code', 'identifier': 'identifier',
            'description': 'description', 'type': 'type', 'status': 'status',
            'visibility': 'visibility', 'icon': 'icon', 'iconColor': 'icon_color',
            'startTime': 'start_time', 'endTime': 'end_time',
            'testCases': 'test_cases', 'testPlans': 'test_plans', 'bugs': 'bugs'
        }

        for api_field, model_field in field_mapping.items():
            if api_field in data:
                update_fields[model_field] = data[api_field]

        if 'code' in update_fields:
            update_fields['code'] = update_fields['code'].lower()
        if 'identifier' in update_fields and update_fields['identifier']:
            update_fields['identifier'] = update_fields['identifier'].lower()

        ProjectRepository.update_project(project, **update_fields)

        if 'isFavorite' in data:
            member = ProjectMemberRepository.get_member(project, user)
            if member:
                ProjectMemberRepository.update_member(member, is_favorite=data['isFavorite'])

        return project, None

    @staticmethod
    def delete_project(project_identifier, user):
        """删除项目"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return False, '项目不存在'

        if not is_system_admin(user):
            if not project.owner or project.owner.id != user.id:
                return False, '只有项目所有者才能删除项目'

        if project.knowledge_base_id:
            try:
                from apps.knowledge.repositories.weknora_repository import weknora_repository
                if weknora_repository.api_key:
                    weknora_repository.delete_knowledge_base(project.knowledge_base_id)
            except ImportError:
                logger.debug("WeKnora repository not available")
            except Exception as e:
                logger.warning(f"删除知识库失败: {str(e)}")

        ProjectRepository.delete_project(project)
        return True, None

    @staticmethod
    def build_project_data(project, is_favorite=False, is_admin=False, role='viewer', is_owner=False):
        """构建项目响应数据"""
        # 获取用例库、版本、模块统计
        from apps.testcase.models import TestCaseRepository, TestCaseVersion, TestModule

        repositories_count = TestCaseRepository.objects.filter(project=project).count()
        versions_count = TestCaseVersion.objects.filter(repository__project=project).count()
        modules_count = TestModule.objects.filter(version__repository__project=project).count()

        return {
            'id': project.id,
            'name': project.name,
            'code': project.code,
            'identifier': project.identifier or project.code,
            'description': project.description,
            'type': project.type,
            'status': project.status,
            'visibility': project.visibility,
            'icon': project.icon,
            'iconColor': project.icon_color,
            'startTime': project.start_time.isoformat() if project.start_time else None,
            'endTime': project.end_time.isoformat() if project.end_time else None,
            'owner': project.owner.username if project.owner else None,
            'ownerAvatar': project.owner.avatar if project.owner else '',
            'isFavorite': is_favorite,
            'isAdmin': is_admin,
            'isOwner': is_owner,
            'role': role,
            'testCases': project.test_cases,
            'testPlans': project.test_plans,
            'bugs': project.bugs,
            'repositories': repositories_count,
            'versions': versions_count,
            'modules': modules_count,
            'knowledgeBaseId': project.knowledge_base_id,
            'knowledgeBaseName': project.knowledge_base_name,
            'createdAt': project.created_at.isoformat() if project.created_at else None,
            'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
        }

    @staticmethod
    def get_project_stats(user):
        """获取项目统计信息"""
        project_ids = ProjectRepository.get_user_projects(user)
        stats = ProjectRepository.get_project_stats(project_ids)

        by_type = {
            'web': stats['by_type'].get('web', 0),
            'mobile': stats['by_type'].get('mobile', 0),
            'api': stats['by_type'].get('api', 0),
            'performance': stats['by_type'].get('performance', 0),
            'security': stats['by_type'].get('security', 0),
            'other': stats['by_type'].get('other', 0)
        }

        return {
            'total': stats['total'],
            'active': stats['active'],
            'completed': stats['completed'],
            'pending': stats['pending'],
            'archived': stats['archived'],
            'byType': by_type
        }

    @staticmethod
    def get_recent_projects(user, limit=6):
        """获取最近访问的项目"""
        # 获取用户作为成员的项目
        member_projects = list(
            ProjectMemberRepository.get_user_member_projects(user)
            .select_related('project')
            .order_by('-updated_at')[:limit]
        )

        # 获取用户作为 owner 但没有成员记录的项目
        owned_projects = Project.objects.filter(owner=user).exclude(
            id__in=[m.project_id for m in member_projects]
        ).order_by('-updated_at')[:limit - len(member_projects)]

        projects = []
        for member in member_projects:
            project = member.project
            projects.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'description': project.description,
                'type': project.type,
                'status': project.status,
                'icon': project.icon,
                'iconColor': project.icon_color,
                'testCases': project.test_cases,
                'isFavorite': member.is_favorite
            })

        for project in owned_projects:
            projects.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'description': project.description,
                'type': project.type,
                'status': project.status,
                'icon': project.icon,
                'iconColor': project.icon_color,
                'testCases': project.test_cases,
                'isFavorite': False
            })

        return projects

    @staticmethod
    def update_visit_time(project_identifier, user):
        """更新项目访问时间"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return False, '项目不存在'

        member = ProjectMemberRepository.get_member(project, user)
        if member:
            member.save(update_fields=['updated_at'])
            return True, None

        return False, '不是项目成员'

    @staticmethod
    def get_todos(user):
        """获取待办事项"""
        from apps.testcase.models import TestCase, TestCaseReview, TestCaseExecution

        project_ids = ProjectRepository.get_user_projects(user)

        todos = []

        # 获取待审核的测试用例
        try:
            pending_reviews = TestCaseReview.objects.filter(
                test_case__version__repository__project_id__in=project_ids,
                status='pending'
            ).select_related('test_case', 'test_case__version__repository__project')[:5]

            for review in pending_reviews:
                project = review.test_case.version.repository.project if review.test_case.version and review.test_case.version.repository else None
                todos.append({
                    'id': f'review_{review.id}',
                    'type': 'review',
                    'title': f'审核测试用例: {review.test_case.title}',
                    'projectName': project.name if project else '',
                    'projectCode': project.code if project else '',
                    'testCaseId': review.test_case.id,
                    'priority': 'high' if review.test_case.priority == 'p0' else 'medium',
                    'createdAt': review.created_at.isoformat() if review.created_at else None
                })
        except Exception as e:
            logger.warning(f'获取待审核测试用例失败: {str(e)}')

        # 获取待执行的测试用例（执行结果为空的记录）
        try:
            pending_executions = TestCaseExecution.objects.filter(
                test_case__version__repository__project_id__in=project_ids,
                result__isnull=True
            ).select_related('test_case', 'test_case__version__repository__project')[:5]

            for execution in pending_executions:
                project = execution.test_case.version.repository.project if execution.test_case.version and execution.test_case.version.repository else None
                todos.append({
                    'id': f'execute_{execution.id}',
                    'type': 'execute',
                    'title': f'执行测试用例: {execution.test_case.title}',
                    'projectName': project.name if project else '',
                    'projectCode': project.code if project else '',
                    'testCaseId': execution.test_case.id,
                    'priority': 'medium',
                    'createdAt': execution.executed_at.isoformat() if execution.executed_at else None
                })
        except Exception as e:
            logger.warning(f'获取待执行测试用例失败: {str(e)}')

        # 按创建时间排序
        todos.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        return todos[:10]

    @staticmethod
    def search_projects(user, keyword):
        """搜索项目"""
        project_ids = ProjectRepository.get_user_projects(user)
        queryset = ProjectRepository.get_projects_by_ids(project_ids)

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        member_favorites = dict(
            ProjectMemberRepository.get_user_member_projects(user)
            .values_list('project_id', 'is_favorite')
        )

        results = []
        for project in queryset:
            results.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'description': project.description,
                'type': project.type,
                'status': project.status,
                'owner': project.owner.username if project.owner else None,
                'isFavorite': member_favorites.get(project.id, False)
            })

        return results, None

    @staticmethod
    def get_project_knowledge_base(project_identifier, user):
        """获取项目关联的知识库信息"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                return None, '无权限访问此项目'

        if not project.knowledge_base_id:
            return None, None

        try:
            from apps.knowledge.repositories.weknora_repository import weknora_repository
            if not weknora_repository.api_key:
                return None, '知识库服务未配置，请设置 WEKNORA_API_KEY 环境变量'

            result = weknora_repository.get_knowledge_base(project.knowledge_base_id)
            if result.get('success'):
                kb_data = result.get('data', {})
                return {
                    'id': kb_data.get('id'),
                    'name': kb_data.get('name'),
                    'description': kb_data.get('description', ''),
                    'type': kb_data.get('type', 'document'),
                    'knowledgeCount': kb_data.get('knowledge_count', 0),
                    'chunkCount': kb_data.get('chunk_count', 0),
                    'createdAt': kb_data.get('created_at'),
                    'updatedAt': kb_data.get('updated_at'),
                }, None

            error_msg = result.get('error', '获取知识库失败')
            if result.get('code') == 'CONNECTION_ERROR':
                error_msg = '无法连接到知识库服务，请确保 WeKnora 服务正在运行'
            return None, error_msg
        except Exception as e:
            logger.error(f'获取项目知识库失败: {str(e)}', exc_info=True)
            return None, f'获取失败: {str(e)}'

    @staticmethod
    def link_knowledge_base(project_identifier, user, knowledge_base_id, knowledge_base_name=None):
        """关联知识库到项目"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, role, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member or role not in ['owner', 'admin']:
                return None, '无权限关联知识库'

        if not knowledge_base_id:
            return None, '知识库ID不能为空'

        try:
            from apps.knowledge.repositories.weknora_repository import weknora_repository
            if not weknora_repository.api_key:
                return None, '知识库服务未配置，请设置 WEKNORA_API_KEY 环境变量'

            result = weknora_repository.get_knowledge_base(knowledge_base_id)
            if not result.get('success'):
                error_msg = '知识库不存在或无法访问'
                if result.get('code') == 'CONNECTION_ERROR':
                    error_msg = '无法连接到知识库服务，请确保 WeKnora 服务正在运行'
                return None, error_msg

            project.knowledge_base_id = knowledge_base_id
            project.knowledge_base_name = knowledge_base_name or result.get('data', {}).get('name', '')
            project.save(update_fields=['knowledge_base_id', 'knowledge_base_name', 'updated_at'])

            return {
                'knowledgeBaseId': project.knowledge_base_id,
                'knowledgeBaseName': project.knowledge_base_name,
            }, None
        except Exception as e:
            logger.error(f'关联知识库失败: {str(e)}', exc_info=True)
            return None, f'关联失败: {str(e)}'

    @staticmethod
    def unlink_knowledge_base(project_identifier, user):
        """解除知识库关联"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return False, '项目不存在'

        if not is_system_admin(user):
            is_member, role, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member or role not in ['owner', 'admin']:
                return False, '无权限解除关联'

        project.knowledge_base_id = None
        project.knowledge_base_name = None
        project.save(update_fields=['knowledge_base_id', 'knowledge_base_name', 'updated_at'])

        return True, None

    @staticmethod
    def create_project_knowledge_base(project_identifier, user, name=None, description=None):
        """为项目创建并关联知识库"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, role, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member or role not in ['owner', 'admin']:
                return None, '无权限创建知识库'

        if project.knowledge_base_id:
            return None, '项目已关联知识库，请先解除关联'

        try:
            from apps.knowledge.repositories.weknora_repository import weknora_repository
            if not weknora_repository.api_key:
                return None, '知识库服务未配置，请设置 WEKNORA_API_KEY 环境变量'

            kb_name = name or f"{project.name} 知识库"
            kb_description = description or f"项目 {project.name} 的知识库"

            result = weknora_repository.create_knowledge_base({
                'name': kb_name,
                'description': kb_description,
                'type': 'document',
            })

            if result.get('success'):
                kb_data = result.get('data', {})
                kb_id = kb_data.get('id')

                project.knowledge_base_id = kb_id
                project.knowledge_base_name = kb_name
                project.save(update_fields=['knowledge_base_id', 'knowledge_base_name', 'updated_at'])

                return {
                    'id': kb_id,
                    'name': kb_name,
                    'knowledgeBaseId': kb_id,
                    'knowledgeBaseName': kb_name,
                }, None

            error_msg = result.get('error', '创建知识库失败')
            if result.get('code') == 'CONNECTION_ERROR':
                error_msg = '无法连接到知识库服务，请确保 WeKnora 服务正在运行'
            return None, error_msg
        except Exception as e:
            logger.error(f'创建项目知识库失败: {str(e)}', exc_info=True)
            return None, f'创建失败: {str(e)}'


class ProjectMemberService:
    """项目成员服务"""

    @staticmethod
    def get_members(project_identifier, user):
        """获取项目成员列表"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                return None, '无权限查看项目成员'

        members = ProjectMemberRepository.get_project_members(project)

        members_data = []
        for member in members:
            members_data.append({
                'id': member.id,
                'userId': member.user.id,
                'name': member.user.name or member.user.username,
                'email': member.user.email,
                'avatar': member.user.avatar or '',
                'role': member.role,
                'status': member.status,
                'joinedAt': member.joined_at.isoformat() if member.joined_at else None,
                'isOwner': member.user.id == project.owner.id if project.owner else False
            })

        return members_data, None

    @staticmethod
    def add_member(project_identifier, operator, user_id, role='viewer', status='active'):
        """添加项目成员"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return None, '无权限添加项目成员'

        valid_roles = [choice[0] for choice in ProjectMember.ROLE_CHOICES]
        if role not in valid_roles:
            return None, f'无效的角色类型，有效值为: {", ".join(valid_roles)}'

        valid_statuses = [choice[0] for choice in ProjectMember.STATUS_CHOICES]
        if status not in valid_statuses:
            return None, f'无效的状态类型，有效值为: {", ".join(valid_statuses)}'

        user = UserRepository.get_by_id(user_id)
        if not user:
            return None, '用户不存在'

        existing = ProjectMemberRepository.get_member(project, user)
        if existing:
            return None, '该用户已是项目成员'

        member = ProjectMemberRepository.add_member(project, user, role, status)

        return {
            'id': member.id,
            'userId': member.user.id,
            'name': member.user.name or member.user.username,
            'email': member.user.email,
            'avatar': member.user.avatar or '',
            'role': member.role,
            'status': member.status,
            'joinedAt': member.joined_at.isoformat() if member.joined_at else None
        }, None

    @staticmethod
    def update_member(project_identifier, operator, member_id, data):
        """更新成员信息

        业务逻辑：
        1. 检查操作者权限
        2. 更新成员角色或状态
        3. 清除相关权限缓存
        """
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return None, '无权限修改成员信息'

        try:
            member = ProjectMember.objects.select_related('user').get(id=member_id, project=project)
        except ProjectMember.DoesNotExist:
            return None, '成员不存在'

        old_status = member.status
        old_role = member.role

        if 'role' in data:
            valid_roles = [choice[0] for choice in ProjectMember.ROLE_CHOICES]
            if data['role'] not in valid_roles:
                return None, '无效的角色类型'
            member.role = data['role']
        if 'status' in data:
            valid_statuses = [choice[0] for choice in ProjectMember.STATUS_CHOICES]
            if data['status'] not in valid_statuses:
                return None, '无效的状态类型'
            member.status = data['status']

        member.save()

        # 清除用户相关的权限缓存
        ProjectService._clear_user_permission_cache(member.user.id, project.id)

        # 记录变更日志
        if old_status != member.status:
            logger.info(f"项目 {project.name} 成员 {member.user.username} 状态从 {old_status} 变更为 {member.status}，操作者: {operator.username}")
        if old_role != member.role:
            logger.info(f"项目 {project.name} 成员 {member.user.username} 角色从 {old_role} 变更为 {member.role}，操作者: {operator.username}")

        return {
            'id': member.id,
            'userId': member.user.id,
            'name': member.user.name or member.user.username,
            'email': member.user.email,
            'avatar': member.user.avatar or '',
            'role': member.role,
            'status': member.status,
            'joinedAt': member.joined_at.isoformat() if member.joined_at else None
        }, None

    @staticmethod
    def _clear_user_permission_cache(user_id, project_id=None):
        """清除用户权限缓存

        当用户角色或状态变更时，需要清除相关缓存以确保权限立即生效
        """
        from django.core.cache import cache

        # 清除用户项目列表缓存
        cache_keys = [
            f'user_projects_{user_id}',
            f'user_accessible_projects_{user_id}',
        ]

        if project_id:
            cache_keys.extend([
                f'project_member_{project_id}_{user_id}',
                f'project_permissions_{project_id}_{user_id}',
            ])

        for key in cache_keys:
            cache.delete(key)

        logger.debug(f"已清除用户 {user_id} 的权限缓存")

    @staticmethod
    def remove_member(project_identifier, operator, member_id):
        """移除成员"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return False, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return False, '无权限移除成员'

        try:
            member = ProjectMember.objects.select_related('user').get(id=member_id, project=project)
        except ProjectMember.DoesNotExist:
            return False, '成员不存在'

        if member.user.id == project.owner.id if project.owner else False:
            return False, '无法移除项目创建者'

        member.delete()
        return True, None

    @staticmethod
    @transaction.atomic
    def batch_update_members(project_identifier, operator, member_ids, data):
        """批量更新成员"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return 0, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return 0, '无权限批量修改成员'

        update_data = {}
        if 'role' in data:
            valid_roles = [choice[0] for choice in ProjectMember.ROLE_CHOICES]
            if data['role'] not in valid_roles:
                return 0, '无效的角色类型'
            update_data['role'] = data['role']
        if 'status' in data:
            valid_statuses = [choice[0] for choice in ProjectMember.STATUS_CHOICES]
            if data['status'] not in valid_statuses:
                return 0, '无效的状态类型'
            update_data['status'] = data['status']

        if not member_ids:
            return 0, '成员ID列表不能为空'

        if not update_data:
            return 0, '没有需要更新的数据'

        if project.owner:
            owner_member_ids = list(
                ProjectMember.objects.filter(
                    id__in=member_ids, project=project, user=project.owner
                ).values_list('id', flat=True)
            )
            if owner_member_ids:
                return 0, '无法修改项目创建者的信息，请从成员列表中移除创建者后重试'

        updated_count = ProjectMemberRepository.batch_update_members(project, member_ids, **update_data)
        return updated_count, None

    @staticmethod
    def toggle_favorite(project_identifier, user):
        """切换收藏状态"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        member = ProjectMemberRepository.get_member(project, user)
        if not member:
            return None, '您不是该项目的成员'

        member.is_favorite = not member.is_favorite
        member.save(update_fields=['is_favorite', 'updated_at'])

        return member.is_favorite, None

    @staticmethod
    def set_favorite(project_identifier, user, is_favorite):
        """设置收藏状态"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        member = ProjectMemberRepository.get_member(project, user)
        if not member:
            return None, '您不是该项目的成员'

        member.is_favorite = is_favorite
        member.save(update_fields=['is_favorite', 'updated_at'])

        return member.is_favorite, None

    @staticmethod
    def get_favorite_projects(user):
        """获取收藏的项目"""
        members = ProjectMemberRepository.get_user_favorite_projects(user)

        projects = []
        for member in members:
            project = member.project
            projects.append({
                'id': project.id,
                'name': project.name,
                'code': project.code,
                'description': project.description,
                'type': project.type,
                'status': project.status,
                'owner': project.owner.username if project.owner else None,
                'isFavorite': True,
                'testCases': project.test_cases,
                'testPlans': project.test_plans,
                'bugs': project.bugs
            })

        return projects

    @staticmethod
    def get_project_activities(project_identifier, user, limit=10):
        """获取项目动态"""
        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                return None, '无权限查看项目动态'

        activities = []
        from apps.testcase.models import TestCaseRepository, TestCaseVersion, TestModule, TestCase, TestCaseExecution

        # 获取最近的用例库创建
        repositories = TestCaseRepository.objects.filter(
            project=project
        ).select_related('created_by').order_by('-created_at')[:limit]
        for repo in repositories:
            if repo.created_by:
                activities.append({
                    'id': f'repo_{repo.id}',
                    'type': 'create',
                    'title': f'创建了用例库「{repo.name}」',
                    'user': repo.created_by.name or repo.created_by.username,
                    'time': repo.created_at.isoformat()
                })

        # 获取最近的版本创建
        versions = TestCaseVersion.objects.filter(
            repository__project=project
        ).select_related('created_by', 'repository').order_by('-created_at')[:limit]
        for version in versions:
            if version.created_by:
                activities.append({
                    'id': f'version_{version.id}',
                    'type': 'create',
                    'title': f'创建了版本「{version.name}」',
                    'user': version.created_by.name or version.created_by.username,
                    'time': version.created_at.isoformat()
                })

        # 获取最近的测试用例创建
        test_cases = TestCase.objects.filter(
            version__repository__project=project
        ).select_related('created_by', 'version').order_by('-created_at')[:limit]
        for case in test_cases:
            if case.created_by:
                activities.append({
                    'id': f'case_{case.id}',
                    'type': 'create',
                    'title': f'创建了测试用例「{case.title}」',
                    'user': case.created_by.name or case.created_by.username,
                    'time': case.created_at.isoformat()
                })

        # 获取最近的测试用例更新
        updated_cases = TestCase.objects.filter(
            version__repository__project=project
        ).select_related('updated_by', 'version').exclude(
            updated_at=F('created_at')
        ).order_by('-updated_at')[:limit]
        for case in updated_cases:
            if case.updated_by:
                activities.append({
                    'id': f'update_{case.id}',
                    'type': 'update',
                    'title': f'更新了测试用例「{case.title}」',
                    'user': case.updated_by.name or case.updated_by.username,
                    'time': case.updated_at.isoformat()
                })

        # 获取最近的执行记录
        executions = TestCaseExecution.objects.filter(
            test_case__version__repository__project=project
        ).select_related('executed_by', 'test_case').order_by('-executed_at')[:limit]
        for exec_record in executions:
            if exec_record.executed_by:
                activities.append({
                    'id': f'exec_{exec_record.id}',
                    'type': 'execute',
                    'title': f'执行了测试用例「{exec_record.test_case.title}」',
                    'user': exec_record.executed_by.name or exec_record.executed_by.username,
                    'time': exec_record.executed_at.isoformat()
                })

        # 按时间排序，取最近的
        activities.sort(key=lambda x: x['time'], reverse=True)
        return activities[:limit], None


class ProjectRoleService:
    """项目角色权限服务"""

    @staticmethod
    def get_project_roles(project_identifier, user):
        """获取项目角色列表"""
        from apps.core.permissions import PROJECT_PERMISSIONS

        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(user):
            is_member, _, _ = ProjectMemberRepository.is_project_member(project.id, user)
            if not is_member:
                return None, '无权限查看项目角色'

        role_counts = ProjectMemberRepository.get_member_role_counts(project)
        saved_permissions = ProjectRoleRepository.get_project_roles(project)

        # 所有可用权限列表（供前端分配）
        all_permissions = list(PROJECT_PERMISSIONS.keys())

        # admin 角色默认拥有所有权限，但也支持自定义配置
        admin_saved = saved_permissions.get('admin')
        admin_permissions = admin_saved if admin_saved else all_permissions

        roles_data = [
            {
                'key': 'admin',
                'name': '管理员',
                'color': '#ef4444',
                'memberCount': role_counts.get('admin', 0),
                'permissions': admin_permissions
            },
            {
                'key': 'developer',
                'name': '开发人员',
                'color': '#3b82f6',
                'memberCount': role_counts.get('developer', 0),
                'permissions': saved_permissions.get('developer', get_default_permissions('developer'))
            },
            {
                'key': 'tester',
                'name': '测试人员',
                'color': '#22c55e',
                'memberCount': role_counts.get('tester', 0),
                'permissions': saved_permissions.get('tester', get_default_permissions('tester'))
            },
            {
                'key': 'viewer',
                'name': '观察者',
                'color': '#6b7280',
                'memberCount': role_counts.get('viewer', 0),
                'permissions': saved_permissions.get('viewer', get_default_permissions('viewer'))
            }
        ]

        # 加载自定义角色（排除内置角色）
        builtin_keys = ['admin', 'developer', 'tester', 'viewer']
        custom_roles = ProjectRole.objects.filter(project=project).exclude(role_key__in=builtin_keys)
        for custom_role in custom_roles:
            roles_data.append({
                'key': custom_role.role_key,
                'name': custom_role.name or custom_role.role_key,
                'color': custom_role.color or '#8b5cf6',
                'memberCount': role_counts.get(custom_role.role_key, 0),
                'permissions': custom_role.permissions or []
            })

        return {'roles': roles_data, 'all_permissions': all_permissions}, None

    @staticmethod
    def update_role_permissions(project_identifier, operator, role_key, permissions):
        """更新角色权限"""
        from apps.core.permissions import PROJECT_PERMISSIONS

        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return False, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return False, '无权限修改角色权限'

        # 内置角色验证
        builtin_keys = ['admin', 'developer', 'tester', 'viewer']
        if role_key not in builtin_keys:
            # 自定义角色需检查是否存在
            if not ProjectRole.objects.filter(project=project, role_key=role_key).exists():
                return False, '角色不存在'

        # 使用 PROJECT_PERMISSIONS 验证权限
        valid_permissions = list(PROJECT_PERMISSIONS.keys())

        # 过滤掉无效的旧权限（自动迁移）
        filtered_permissions = [p for p in permissions if p in valid_permissions]

        # 不再报错，而是自动过滤无效权限
        ProjectRoleRepository.update_role_permissions(project, role_key, filtered_permissions)
        return True, None

    @staticmethod
    def create_project_role(project_identifier, operator, data):
        """创建自定义项目角色"""
        from apps.core.permissions import PROJECT_PERMISSIONS

        project = ProjectRepository.get_by_identifier(project_identifier)
        if not project:
            return None, '项目不存在'

        if not is_system_admin(operator):
            is_member, operator_role, _ = ProjectMemberRepository.is_project_member(project.id, operator)
            if not is_member or operator_role not in ['owner', 'admin']:
                return None, '无权限创建角色'

        role_key = data.get('key', '').strip()
        role_name = data.get('name', '').strip()
        permissions = data.get('permissions', [])
        color = data.get('color', '#8b5cf6')

        if not role_key or not role_name:
            return None, '角色标识和名称不能为空'

        # 检查角色标识是否已存在
        if ProjectRole.objects.filter(project=project, role_key=role_key).exists():
            return None, '角色标识已存在'

        # 不允许使用系统内置角色标识
        if role_key in ['admin', 'developer', 'tester', 'viewer']:
            return None, '不能使用系统内置角色标识'

        # 验证权限
        valid_permissions = list(PROJECT_PERMISSIONS.keys())
        filtered_permissions = [p for p in permissions if p in valid_permissions]

        role = ProjectRole.objects.create(
            project=project,
            role_key=role_key,
            permissions=filtered_permissions,
            name=role_name,
            color=color
        )

        return {
            'key': role.role_key,
            'name': role_name,
            'color': color,
            'memberCount': 0,
            'permissions': filtered_permissions
        }, None