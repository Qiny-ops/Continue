"""
执行服务层
"""

import logging
from apps.core.permissions import is_system_admin
from apps.testcase.models import TestCaseExecution, TestCaseReview

logger = logging.getLogger(__name__)


class ExecutionService:
    """执行服务"""

    @staticmethod
    def get_all_executions():
        """获取所有执行记录"""
        return TestCaseExecution.objects.all()

    @staticmethod
    def get_user_accessible_executions(user):
        """获取用户有权限访问的执行记录"""
        from apps.projects.models import ProjectMember, Project

        if is_system_admin(user):
            return TestCaseExecution.objects.all()

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )
        allowed_project_ids = member_project_ids | owned_project_ids

        return TestCaseExecution.objects.filter(
            test_case__version__repository__project_id__in=allowed_project_ids
        ).distinct()

    @staticmethod
    def check_execution_permission(test_case, user):
        """检查用户是否有权限执行测试用例"""
        if is_system_admin(user):
            return True, None

        from apps.projects.repositories import ProjectMemberRepository
        is_member, role, _ = ProjectMemberRepository.is_project_member(
            test_case.version.repository.project_id, user
        )

        if not is_member:
            return False, '您没有权限执行该测试用例'

        if role not in ['owner', 'admin', 'tester']:
            return False, '您没有执行测试用例的权限'

        return True, None

    @staticmethod
    def create_execution(test_case, executed_by, result, actual_result='', remark=''):
        """创建执行记录"""
        return TestCaseExecution.objects.create(
            test_case=test_case,
            executed_by=executed_by,
            result=result,
            actual_result=actual_result,
            remark=remark
        )

    @staticmethod
    def get_execution_history(test_case_id):
        """获取用例执行历史"""
        return TestCaseExecution.objects.filter(
            test_case_id=test_case_id
        ).select_related('executed_by').order_by('-executed_at')

    @staticmethod
    def get_execution_statistics(test_case_id):
        """获取用例执行统计

        Args:
            test_case_id: 测试用例ID

        Returns:
            dict: 包含执行统计数据的字典
                - total: 总执行次数
                - pass_count: 通过次数
                - fail_count: 失败次数
                - block_count: 阻塞次数
                - skip_count: 跳过次数
                - last_result: 最近一次执行结果
                - pass_rate: 通过率（百分比）
        """
        executions = TestCaseExecution.objects.filter(test_case_id=test_case_id)
        total = executions.count()

        if total == 0:
            return {
                'total': 0,
                'pass_count': 0,
                'fail_count': 0,
                'block_count': 0,
                'skip_count': 0,
                'last_result': None,
                'pass_rate': 0
            }

        pass_count = executions.filter(result='pass').count()
        fail_count = executions.filter(result='fail').count()
        block_count = executions.filter(result='block').count()
        skip_count = executions.filter(result='skip').count()

        last_execution = executions.order_by('-executed_at').first()
        last_result = last_execution.result if last_execution else None

        pass_rate = round(pass_count / total * 100, 1) if total > 0 else 0

        return {
            'total': total,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'block_count': block_count,
            'skip_count': skip_count,
            'last_result': last_result,
            'pass_rate': pass_rate
        }

    @staticmethod
    def get_executions_since_approval(test_case_id):
        """获取最近评审通过后的执行记录

        用于追踪评审通过后的用例执行情况

        Args:
            test_case_id: 测试用例ID

        Returns:
            QuerySet: 最近评审通过后的执行记录
        """
        # 获取最近的通过评审记录
        last_approved = TestCaseReview.objects.filter(
            test_case_id=test_case_id, status='approved'
        ).order_by('-created_at').first()

        if not last_approved:
            # 如果没有通过评审，返回所有执行记录
            return TestCaseExecution.objects.filter(
                test_case_id=test_case_id
            ).select_related('executed_by').order_by('-executed_at')

        # 返回评审通过后的执行记录
        return TestCaseExecution.objects.filter(
            test_case_id=test_case_id,
            executed_at__gte=last_approved.created_at
        ).select_related('executed_by').order_by('-executed_at')

    @staticmethod
    def get_execution_summary_for_project(project_id):
        """获取项目的执行统计摘要

        Args:
            project_id: 项目ID

        Returns:
            dict: 项目级别的执行统计
        """
        from apps.testcase.models import TestCase

        # 获取项目下所有用例
        test_cases = TestCase.objects.filter(
            version__repository__project_id=project_id
        ).prefetch_related('executions')

        total_cases = test_cases.count()
        executed_cases = sum(1 for tc in test_cases if tc.executions.exists())

        total_executions = 0
        pass_count = 0
        fail_count = 0

        for tc in test_cases:
            executions = tc.executions.all()
            total_executions += executions.count()
            pass_count += executions.filter(result='pass').count()
            fail_count += executions.filter(result='fail').count()

        return {
            'total_cases': total_cases,
            'executed_cases': executed_cases,
            'unexecuted_cases': total_cases - executed_cases,
            'total_executions': total_executions,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'execution_rate': round(executed_cases / total_cases * 100, 1) if total_cases > 0 else 0,
            'pass_rate': round(pass_count / total_executions * 100, 1) if total_executions > 0 else 0
        }
