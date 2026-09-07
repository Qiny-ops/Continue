"""
评审服务层
"""

import logging
from django.db import transaction
from apps.core.permissions import is_system_admin
from apps.testcase.models import TestCaseReview, TestCase

logger = logging.getLogger(__name__)


class ReviewService:
    """评审服务"""

    # 评审轮次上限：超过后不再允许重新提交，防止无限驳回循环
    MAX_REVISION_COUNT = 5

    @staticmethod
    def get_all_reviews():
        """获取所有评审记录"""
        return TestCaseReview.objects.all()

    @staticmethod
    def get_user_accessible_reviews(user):
        """获取用户有权限访问的评审记录"""
        from apps.projects.models import ProjectMember, Project

        if is_system_admin(user):
            return TestCaseReview.objects.all()

        member_project_ids = set(
            ProjectMember.objects.filter(user=user, status='active')
            .values_list('project_id', flat=True)
        )
        owned_project_ids = set(
            Project.objects.filter(owner=user)
            .values_list('id', flat=True)
        )
        allowed_project_ids = member_project_ids | owned_project_ids

        return TestCaseReview.objects.filter(
            test_case__version__repository__project_id__in=allowed_project_ids
        ).distinct()

    @staticmethod
    def check_review_permission(test_case, user):
        """检查用户是否有权限评审测试用例"""
        if is_system_admin(user):
            return True

        from apps.projects.repositories import ProjectMemberRepository
        is_member, _, _ = ProjectMemberRepository.is_project_member(
            test_case.version.repository.project_id, user
        )
        return is_member

    @staticmethod
    @transaction.atomic
    def create_review(test_case, reviewer, comment='', status='pending'):
        """创建评审记录

        业务逻辑：
        1. 创建评审记录
        2. 自动更新测试用例的评审状态为 'pending'
        """
        review = TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=reviewer,
            comment=comment,
            status=status
        )

        # 更新测试用例的评审状态
        test_case.review_status = 'pending'
        test_case.save(update_fields=['review_status'])

        logger.info(f"用户 {reviewer.username} 创建了用例 {test_case.title} 的评审记录")
        return review

    @staticmethod
    @transaction.atomic
    def update_review_status(review, new_status, comment=''):
        """更新评审状态

        业务逻辑：
        1. 更新评审记录的状态
        2. 自动同步测试用例的评审状态

        Args:
            review: 评审记录
            new_status: 新状态 ('approved', 'rejected', 'pending')
            comment: 评审意见
        """
        valid_statuses = [choice[0] for choice in TestCaseReview.STATUS_CHOICES]
        if new_status not in valid_statuses:
            raise ValueError(f'无效的评审状态: {new_status}')

        review.status = new_status
        if comment:
            review.comment = comment
        review.save()

        # 同步更新测试用例的评审状态
        test_case = review.test_case
        test_case.review_status = new_status
        test_case.save(update_fields=['review_status'])

        logger.info(f"评审记录 {review.id} 状态更新为 {new_status}，用例 {test_case.title} 同步更新")
        return review

    @staticmethod
    @transaction.atomic
    def reject_with_feedback(test_case, reviewer, comment):
        """驳回评审并记录驳回原因

        Args:
            test_case: 测试用例
            reviewer: 评审人
            comment: 驳回原因

        Returns:
            TestCaseReview: 创建的驳回评审记录
        """
        if not comment or not comment.strip():
            raise ValueError('驳回原因不能为空')

        # 获取当前评审轮次
        last_review = test_case.reviews.order_by('-created_at').first()
        revision_number = last_review.revision_number if last_review else 1

        # 创建驳回评审记录
        review = TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=reviewer,
            status='rejected',
            comment=comment.strip(),
            revision_number=revision_number
        )

        # 更新用例状态为已驳回
        test_case.review_status = 'rejected'
        test_case.save(update_fields=['review_status'])

        logger.info(f"用户 {reviewer.username} 驳回了用例 {test_case.title}，原因: {comment}")
        return review

    @staticmethod
    @transaction.atomic
    def approve_review(test_case, reviewer, comment=''):
        """通过评审

        Args:
            test_case: 测试用例
            reviewer: 评审人
            comment: 评审意见（可选）

        Returns:
            TestCaseReview: 创建的通过评审记录
        """
        # 获取当前评审轮次
        last_review = test_case.reviews.order_by('-created_at').first()
        revision_number = last_review.revision_number if last_review else 1

        # 创建通过评审记录
        review = TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=reviewer,
            status='approved',
            comment=comment.strip() if comment else '评审通过',
            revision_number=revision_number
        )

        # 更新用例状态为已通过
        test_case.review_status = 'approved'
        test_case.save(update_fields=['review_status'])

        logger.info(f"用户 {reviewer.username} 通过了用例 {test_case.title} 的评审")
        return review

    @staticmethod
    @transaction.atomic
    def resubmit_for_review(test_case, user, revision_note=''):
        """修改后重新提交评审

        业务流程：
        1. 检查用例状态是否为"已驳回"
        2. 创建新的评审记录，关联到上一轮驳回的评审
        3. 更新用例状态为"修改后待重审"

        Args:
            test_case: 测试用例
            user: 提交重审的用户（通常是用例创建者）
            revision_note: 修改说明

        Returns:
            TestCaseReview: 新创建的评审记录

        Raises:
            ValueError: 如果用例状态不是"已驳回"
        """
        if test_case.review_status != 'rejected':
            raise ValueError('只有已驳回的用例才能重新提交评审')

        # 获取最近一次驳回的评审记录
        last_rejected_review = test_case.reviews.filter(
            status='rejected'
        ).order_by('-created_at').first()

        if not last_rejected_review:
            raise ValueError('未找到驳回记录，无法重新提交评审')

        # 计算新的评审轮次
        new_revision_number = last_rejected_review.revision_number + 1

        # 评审轮次上限保护：避免争议用例无限驳回循环
        if new_revision_number > ReviewService.MAX_REVISION_COUNT:
            raise ValueError(
                f'评审轮次已达上限 ({ReviewService.MAX_REVISION_COUNT})，'
                f'无法再次提交。请由管理员确认处置或关闭该用例。'
            )

        # 创建新的评审记录
        new_review = TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=None,  # 待分配评审人
            status='pending',
            revision_number=new_revision_number,
            revision_note=revision_note.strip() if revision_note else '',
            previous_review=last_rejected_review
        )

        # 更新用例状态为"修改后待重审"
        test_case.review_status = 'revision_pending'
        test_case.save(update_fields=['review_status'])

        logger.info(
            f"用户 {user.username} 重新提交了用例 {test_case.title} 的评审，"
            f"轮次: {new_revision_number}"
        )
        return new_review

    @staticmethod
    def get_review_history(test_case_id):
        """获取完整的评审历史

        Args:
            test_case_id: 测试用例ID

        Returns:
            QuerySet: 按时间排序的评审记录列表
        """
        return TestCaseReview.objects.filter(
            test_case_id=test_case_id
        ).select_related(
            'reviewer', 'previous_review'
        ).order_by('created_at')

    @staticmethod
    def get_latest_review(test_case_id):
        """获取最新的评审记录

        Args:
            test_case_id: 测试用例ID

        Returns:
            TestCaseReview: 最新的评审记录，如果没有则返回 None
        """
        return TestCaseReview.objects.filter(
            test_case_id=test_case_id
        ).select_related('reviewer').order_by('-created_at').first()
