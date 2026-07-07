"""
执行记录数据访问层
"""

from apps.core.base.repository import BaseRepository
from apps.testcase.models import TestCaseExecution


class ExecutionRepository(BaseRepository):
    """执行记录数据访问层"""
    model = TestCaseExecution

    @classmethod
    def get_by_id(cls, execution_id):
        """根据ID获取执行记录"""
        return TestCaseExecution.objects.filter(id=execution_id).first()

    @classmethod
    def get_by_case(cls, test_case_id):
        """获取测试用例的所有执行记录"""
        return TestCaseExecution.objects.filter(test_case_id=test_case_id)

    @classmethod
    def create_execution(cls, test_case, executed_by, **extra_fields):
        """创建执行记录"""
        return TestCaseExecution.objects.create(
            test_case=test_case,
            executed_by=executed_by,
            **extra_fields
        )

    @classmethod
    def delete_execution(cls, execution):
        """删除执行记录"""
        execution.delete()
