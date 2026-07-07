"""
评审数据访问层
"""

from apps.core.base.repository import BaseRepository
from apps.testcase.models import TestCaseReview


class ReviewRepository(BaseRepository):
    """评审数据访问层"""
    model = TestCaseReview

    @classmethod
    def get_by_id(cls, review_id):
        """根据ID获取评审"""
        return TestCaseReview.objects.filter(id=review_id).first()

    @classmethod
    def get_by_case(cls, test_case_id):
        """获取测试用例的所有评审"""
        return TestCaseReview.objects.filter(test_case_id=test_case_id)

    @classmethod
    def create_review(cls, test_case, reviewer, **extra_fields):
        """创建评审"""
        return TestCaseReview.objects.create(
            test_case=test_case,
            reviewer=reviewer,
            **extra_fields
        )

    @classmethod
    def update_review(cls, review, **kwargs):
        """更新评审"""
        for attr, value in kwargs.items():
            setattr(review, attr, value)
        review.save()
        return review