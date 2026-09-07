"""
需求生成测试用例服务

独立于现有 AI 生成流程，从需求管理页面触发。
"""
import logging
from typing import Tuple

from django.db import transaction
from django.contrib.auth import get_user_model

from apps.requirement.repositories.requirement_repository import RequirementRepository
from apps.testcase.clients.ai_client import AITestCaseClientSync, AIServiceError
from apps.testcase.services.ai_generation_service import AIGenerationService

logger = logging.getLogger(__name__)
User = get_user_model()


class RequirementGenerateService:
    """从需求生成测试用例"""

    def __init__(self):
        self.ai_service = AIGenerationService()

    @classmethod
    def generate_from_requirement(
        cls,
        requirement_id: int,
        version_id: int,
        user=None,
    ) -> Tuple[dict, str]:
        """从单个需求生成测试用例"""
        service = cls()
        requirement = RequirementRepository.get_by_id(requirement_id)
        if not requirement:
            raise NotFoundError('需求不存在')

        item = {
            'module': '',
            'func_point': requirement.func_point or requirement.title,
            'related_detail': requirement.description or '',
        }

        input_text = service.ai_service._build_input_text(item)
        result = service.ai_service.generate_from_text(
            input_text=input_text,
            version_id=version_id,
            user=user,
        )

        if result.get('success') and result.get('cases'):
            # 回填需求关联
            from apps.testcase.models import TestCase
            TestCase.objects.filter(
                id__in=[c['id'] for c in result['cases'] if c.get('id')]
            ).update(requirement_id=requirement_id)

        return result, None

    @classmethod
    def batch_generate_from_requirements(
        cls,
        requirement_ids: list,
        version_id: int,
        user=None,
    ) -> Tuple[dict, str]:
        """从多个需求批量生成测试用例"""
        service = cls()
        requirements = RequirementRepository.get_by_ids(requirement_ids)

        if not requirements:
            raise BusinessError('未找到指定需求')

        items = []
        for req in requirements:
            items.append({
                'module': '',
                'func_point': req.func_point or req.title,
                'related_detail': req.description or '',
                'requirement_id': req.id,
            })

        total_created = 0
        total_errors = 0
        all_cases = []
        all_errors = []

        for item in items:
            input_text = service.ai_service._build_input_text(item)
            result = service.ai_service.generate_from_text(
                input_text=input_text,
                version_id=version_id,
                user=user,
            )

            if result.get('success'):
                total_created += result.get('created_count', 0)
                all_cases.extend(result.get('cases', []))

                # 回填需求关联
                if item.get('requirement_id'):
                    from apps.testcase.models import TestCase
                    TestCase.objects.filter(
                        id__in=[c['id'] for c in result.get('cases', []) if c.get('id')]
                    ).update(requirement_id=item['requirement_id'])
            else:
                total_errors += 1
                all_errors.append({
                    'requirement_id': item.get('requirement_id'),
                    'error': result.get('error', '生成失败'),
                })

        return {
            'success': total_created > 0 or total_errors == 0,
            'created_count': total_created,
            'error_count': total_errors,
            'cases': all_cases,
            'errors': all_errors,
        }, None
