"""
AI生成测试用例编排服务

负责编排需求提取→AI生成→数据保存流程，事务管理。
支持JSON格式验证、KTO训练数据集保存、重试机制。
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.testcase.clients.ai_client import AITestCaseClientSync, AIServiceError
from apps.testcase.repositories.test_case_repository import TestCaseDataRepository
from apps.testcase.repositories.test_module_repository import TestModuleRepository
from apps.knowledge.services.requirement_service import RequirementService

logger = logging.getLogger(__name__)
User = get_user_model()


class KTODatasetWriter:
    """KTO训练数据集写入器"""

    # 系统提示词
    SYSTEM_PROMPT = "你的任务是帮我生成功能测试用例"

    def __init__(self, dataset_dir: str = None):
        self.dataset_dir = dataset_dir or getattr(
            settings, 'KTO_DATASET_DIR',
            os.path.join(settings.BASE_DIR, 'kto_dataset')
        )
        self._ensure_dir()

    def _ensure_dir(self):
        """确保数据集目录存在"""
        os.makedirs(self.dataset_dir, exist_ok=True)

    def _get_filename(self, prefix: str = 'kto') -> str:
        """获取数据集文件名"""
        date_str = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.dataset_dir, f'{prefix}_{date_str}.jsonl')

    def _build_kto_record(
        self,
        user_content: str,
        assistant_content: str,
        label: bool
    ) -> dict:
        """
        构建KTO格式的训练数据记录

        Args:
            user_content: 用户输入内容（prompt）
            assistant_content: AI响应内容
            label: True表示好的响应（chosen），False表示不好的响应（rejected）

        Returns:
            KTO格式的数据记录
        """
        return {
            "messages": [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content
                },
                {
                    "role": "assistant",
                    "content": assistant_content
                }
            ],
            "label": label
        }

    def save_invalid_response(
        self,
        input_text: str,
        raw_response: str,
        error_message: str,
        mapping_info: dict = None
    ):
        """
        保存无效的AI响应到KTO数据集（负样本）

        Args:
            input_text: 输入文本（prompt）
            raw_response: AI原始响应
            error_message: 错误信息
            mapping_info: 映射信息（模块、功能点等）
        """
        filename = self._get_filename('kto')

        # 构建KTO格式记录
        record = self._build_kto_record(
            user_content=input_text,
            assistant_content=raw_response,
            label=False  # 负样本
        )

        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.info(f"已保存负样本到KTO数据集: {filename}")
        except Exception as e:
            logger.error(f"保存KTO数据集失败: {e}")

    def save_parse_error(
        self,
        input_text: str,
        raw_content: str,
        parse_error: str,
        mapping_info: dict = None
    ):
        """保存JSON解析错误的数据（负样本）"""
        filename = self._get_filename('kto')

        # 构建KTO格式记录
        record = self._build_kto_record(
            user_content=input_text,
            assistant_content=raw_content,
            label=False  # 负样本
        )

        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.info(f"已保存解析错误负样本到KTO数据集: {filename}")
        except Exception as e:
            logger.error(f"保存KTO数据集失败: {e}")

    def save_valid_response(
        self,
        input_text: str,
        response: Any,
        mapping_info: dict = None
    ):
        """保存有效的响应（正样本）"""
        filename = self._get_filename('kto')

        # 将响应转换为JSON字符串
        if isinstance(response, (list, dict)):
            assistant_content = json.dumps(response, ensure_ascii=False)
        else:
            assistant_content = str(response)

        # 构建KTO格式记录
        record = self._build_kto_record(
            user_content=input_text,
            assistant_content=assistant_content,
            label=True  # 正样本
        )

        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.info(f"已保存正样本到KTO数据集: {filename}")
        except Exception as e:
            logger.error(f"保存KTO数据集失败: {e}")


class TestCaseDataValidator:
    """测试用例数据验证器"""

    # 必需字段（至少需要包含其中一个）
    REQUIRED_TITLE_FIELDS = ['title', 'testpoint', 'name']
    REQUIRED_STEP_FIELDS = ['steps', 'test_steps', 'description']

    @classmethod
    def validate_case(cls, case_data: dict) -> Tuple[bool, List[str]]:
        """
        验证单个测试用例数据

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if not isinstance(case_data, dict):
            return False, ['测试用例必须是字典类型']

        # 检查标题字段
        has_title = any(case_data.get(f) for f in cls.REQUIRED_TITLE_FIELDS)
        if not has_title:
            errors.append(f'缺少标题字段，需要以下字段之一: {cls.REQUIRED_TITLE_FIELDS}')

        # 检查步骤字段
        has_steps = any(case_data.get(f) for f in cls.REQUIRED_STEP_FIELDS)
        if not has_steps:
            errors.append(f'缺少步骤字段，需要以下字段之一: {cls.REQUIRED_STEP_FIELDS}')

        return len(errors) == 0, errors

    @classmethod
    def validate_cases_list(cls, cases_data: Any) -> Tuple[bool, List[dict], List[str]]:
        """
        验证测试用例列表

        Args:
            cases_data: AI返回的用例数据（可能是列表或单个对象）

        Returns:
            (is_valid, valid_cases, error_messages)
        """
        errors = []
        valid_cases = []

        # 确保是列表
        if isinstance(cases_data, dict):
            cases_list = [cases_data]
        elif isinstance(cases_data, list):
            cases_list = cases_data
        else:
            return False, [], ['AI返回数据格式错误，期望列表或字典']

        if len(cases_list) == 0:
            return False, [], ['AI返回数据为空']

        for i, case_data in enumerate(cases_list):
            is_valid, case_errors = cls.validate_case(case_data)
            if is_valid:
                valid_cases.append(case_data)
            else:
                errors.append(f'用例{i+1}: {"; ".join(case_errors)}')

        # 至少有一个有效用例就算部分成功
        return len(valid_cases) > 0, valid_cases, errors


class AIGenerationService:
    """AI生成测试用例编排服务"""

    # 测试方向prompt
    TEST_PROMPTS = [
        "测试方向：功能点测试用例场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
        "测试方向：业务逻辑测试用例场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
        "测试方向：其他测试场景。请依据这些信息帮我生成功能测试用例。\n注意：\n1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。\n2、你需要严格按照 json 格式生成，并且要能解析。",
    ]

    # 测试类型名称
    TEST_TYPE_NAMES = ['功能点测试', '业务逻辑测试', '其他测试']

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    def __init__(
        self,
        ai_client: AITestCaseClientSync = None,
        case_repository: TestCaseDataRepository = None,
        module_repository: TestModuleRepository = None,
        requirement_service: RequirementService = None,
        kto_writer: KTODatasetWriter = None,
    ):
        # 依赖注入，便于测试Mock
        self.ai_client = ai_client or AITestCaseClientSync()
        self.case_repository = case_repository or TestCaseDataRepository()
        self.module_repository = module_repository or TestModuleRepository()
        self.requirement_service = requirement_service or RequirementService()
        self.kto_writer = kto_writer or KTODatasetWriter()
        self.validator = TestCaseDataValidator()

    def generate_from_knowledge(
        self,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        version_id: str,
        user: User = None,
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        AI生成测试用例（从需求文档）

        完整流程：
        1. 从知识库提取需求功能点
        2. 检索关联需求详情
        3. 调用AI微服务生成测试用例（带重试）
        4. 验证JSON格式
        5. 保存到数据库

        Args:
            knowledge_base_ids: 知识库ID列表
            knowledge_ids: 文件ID列表
            version_id: 版本ID
            user: 当前用户
            query: 自定义查询内容
            session_id: 会话ID

        Returns:
            {
                'success': bool,
                'created_count': int,
                'error_count': int,
                'cases': [...],  # 创建的测试用例列表
                'errors': [...],
                'retry_count': int,  # 重试次数
            }
        """
        try:
            if not knowledge_base_ids:
                return {'success': False, 'error': '至少需要提供一个知识库 ID'}

            # 1. 需求提取
            requirements, session_id = self.requirement_service.extract(
                knowledge_base_ids, knowledge_ids, query, session_id, **kwargs
            )

            if not requirements:
                logger.warning("需求提取结果为空")
                return {
                    'success': True,
                    'created_count': 0,
                    'error_count': 0,
                    'cases': [],
                    'errors': [],
                    'retry_count': 0,
                }

            # 2. 检索关联需求
            requirements_with_details = self.requirement_service.retrieve_related(
                requirements, knowledge_base_ids, knowledge_ids, session_id
            )

            # 3. 批量生成测试用例（带重试和验证）
            ai_results, item_mapping, total_retries = self._generate_batch_with_retry(
                requirements_with_details
            )

            # 4. 保存到数据库（事务保护）
            created_cases, error_count, errors = self._save_with_transaction(
                ai_results, item_mapping, version_id, user
            )

            return {
                'success': True,
                'created_count': len(created_cases),
                'error_count': error_count,
                'cases': created_cases,
                'errors': errors,
                'retry_count': total_retries,
            }

        except AIServiceError as e:
            logger.error(f"AI生成服务错误: {e.message}")
            return {
                'success': False,
                'error': f"AI生成服务错误: {e.message}",
                'code': e.code,
            }
        except Exception as e:
            logger.error(f"生成测试用例失败: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def generate_from_text(
        self,
        input_text: str,
        version_id: str = None,
        user: User = None,
    ) -> Dict[str, Any]:
        """
        从文本生成测试用例（直接存库）

        带重试和JSON验证机制
        验证失败立即写入KTO数据集，然后重试
        """
        import time

        last_error = None
        total_retries = 0

        for attempt in range(self.MAX_RETRIES):
            try:
                ai_result = self.ai_client.generate_cases(input_text)

                if not ai_result.success:
                    last_error = ai_result.error or 'AI生成服务返回错误'
                    logger.warning(f"AI生成失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {last_error}")

                    # 立即保存失败响应到KTO数据集
                    self.kto_writer.save_invalid_response(
                        input_text=input_text,
                        raw_response=ai_result.raw_content or '',
                        error_message=last_error,
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY_SECONDS)
                        total_retries += 1
                        continue

                    return {
                        'success': False,
                        'error': last_error,
                        'created_count': 0,
                        'error_count': 0,
                        'cases': [],
                        'errors': [],
                        'retry_count': total_retries,
                    }

                # 验证JSON格式
                cases_data = ai_result.result
                if isinstance(cases_data, str):
                    # 尝试解析JSON字符串
                    try:
                        cases_data = json.loads(cases_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON解析失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}")

                        # 立即保存解析错误到KTO数据集
                        self.kto_writer.save_parse_error(
                            input_text=input_text,
                            raw_content=cases_data,
                            parse_error=str(e),
                        )

                        if attempt < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY_SECONDS)
                            total_retries += 1
                            continue

                        return {
                            'success': False,
                            'error': f'JSON解析失败: {str(e)}',
                            'created_count': 0,
                            'error_count': 0,
                            'cases': [],
                            'errors': [],
                            'retry_count': total_retries,
                        }

                # 验证数据结构
                is_valid, valid_cases, validation_errors = self.validator.validate_cases_list(cases_data)

                if not is_valid:
                    logger.warning(f"数据验证失败 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {validation_errors}")

                    # 立即保存验证失败的数据到KTO数据集
                    self.kto_writer.save_invalid_response(
                        input_text=input_text,
                        raw_response=json.dumps(cases_data, ensure_ascii=False),
                        error_message='; '.join(validation_errors),
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY_SECONDS)
                        total_retries += 1
                        continue

                    return {
                        'success': False,
                        'error': f'数据验证失败: {"; ".join(validation_errors)}',
                        'created_count': 0,
                        'error_count': 0,
                        'cases': [],
                        'errors': validation_errors,
                        'retry_count': total_retries,
                    }

                # 验证通过，保存正样本到KTO数据集
                self.kto_writer.save_valid_response(
                    input_text=input_text,
                    response=valid_cases,
                )

                # 保存到数据库
                if version_id and user:
                    created_cases, error_count, errors = self._save_cases_with_models(
                        valid_cases, version_id, user
                    )

                    return {
                        'success': True,
                        'created_count': len(created_cases),
                        'error_count': error_count,
                        'cases': created_cases,
                        'errors': errors,
                        'retry_count': total_retries,
                    }

                return {
                    'success': False,
                    'error': 'version_id和user不能为空',
                    'created_count': 0,
                    'error_count': 0,
                    'cases': [],
                    'errors': [],
                    'retry_count': total_retries,
                }

            except AIServiceError as e:
                last_error = e.message
                logger.warning(f"AI服务错误 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e.message}")

                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY_SECONDS)
                    total_retries += 1
                    continue

        return {
            'success': False,
            'error': last_error or '未知错误',
            'created_count': 0,
            'error_count': 0,
            'cases': [],
            'errors': [],
            'retry_count': total_retries,
        }

    def _generate_batch_with_retry(
        self,
        requirements_with_details: List[dict]
    ) -> Tuple[List, List[dict], int]:
        """
        带重试机制的批量生成

        Returns:
            (ai_results列表, item_mapping列表, 总重试次数)
        """
        import time

        batch_items = []
        item_mapping = []

        for item in requirements_with_details:
            base_text = self._build_input_text(item)

            for j, prompt in enumerate(self.TEST_PROMPTS):
                batch_items.append({'input_text': f"{base_text}\n{prompt}"})
                item_mapping.append({
                    'module': item['module'],
                    'func_point': item['func_point'],
                    'test_type_index': j,
                })

        logger.info(f"调用AI批量生成，共 {len(batch_items)} 个请求")

        # 分批调用（每批最多10个）
        ai_results = []
        batch_size = 10
        total_retries = 0

        for start in range(0, len(batch_items), batch_size):
            end = min(start + batch_size, len(batch_items))
            batch_slice = batch_items[start:end]
            mapping_slice = item_mapping[start:end]

            logger.info(f"批量调用 [{start}-{end}]，共 {len(batch_slice)} 个请求")

            # 带重试的单批处理
            batch_results, retries = self._process_batch_with_retry(
                batch_slice, mapping_slice
            )
            ai_results.extend(batch_results)
            total_retries += retries

        logger.info(f"AI批量生成完成，共 {len(ai_results)} 个结果，总重试 {total_retries} 次")

        return ai_results, item_mapping, total_retries

    def _process_batch_with_retry(
        self,
        batch_items: List[dict],
        mapping_slice: List[dict]
    ) -> Tuple[List, int]:
        """
        处理单个批次，带重试和验证

        Returns:
            (结果列表, 重试次数)
        """
        import time

        results = []
        retries = 0

        for i, item in enumerate(batch_items):
            input_text = item['input_text']
            mapping = mapping_slice[i] if i < len(mapping_slice) else {}

            last_result = None

            for attempt in range(self.MAX_RETRIES):
                try:
                    ai_result = self.ai_client.generate_cases(input_text)

                    if not ai_result.success:
                        logger.warning(
                            f"AI生成失败 [{mapping.get('module')}-{mapping.get('func_point')}] "
                            f"(尝试 {attempt + 1}/{self.MAX_RETRIES}): {ai_result.error}"
                        )

                        # 保存失败响应
                        self.kto_writer.save_invalid_response(
                            input_text=input_text,
                            raw_response=ai_result.raw_content or '',
                            error_message=ai_result.error or '生成失败',
                            mapping_info=mapping,
                        )

                        if attempt < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY_SECONDS)
                            retries += 1
                            continue

                        # 最后一次尝试失败，记录错误结果
                        last_result = ai_result
                        break

                    # 验证JSON格式
                    cases_data = ai_result.result
                    if isinstance(cases_data, str):
                        try:
                            cases_data = json.loads(cases_data)
                            # 更新解析后的结果
                            ai_result = type(ai_result)(
                                success=ai_result.success,
                                result=cases_data,
                                raw_content=ai_result.raw_content,
                                error=ai_result.error,
                            )
                        except json.JSONDecodeError as e:
                            logger.warning(
                                f"JSON解析失败 [{mapping.get('module')}-{mapping.get('func_point')}] "
                                f"(尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}"
                            )

                            self.kto_writer.save_parse_error(
                                input_text=input_text,
                                raw_content=cases_data,
                                parse_error=str(e),
                                mapping_info=mapping,
                            )

                            if attempt < self.MAX_RETRIES - 1:
                                time.sleep(self.RETRY_DELAY_SECONDS)
                                retries += 1
                                continue

                            last_result = type(ai_result)(
                                success=False,
                                result=None,
                                raw_content=cases_data,
                                error=f'JSON解析失败: {str(e)}',
                            )
                            break

                    # 验证数据结构
                    is_valid, valid_cases, validation_errors = self.validator.validate_cases_list(cases_data)

                    if not is_valid:
                        logger.warning(
                            f"数据验证失败 [{mapping.get('module')}-{mapping.get('func_point')}] "
                            f"(尝试 {attempt + 1}/{self.MAX_RETRIES}): {validation_errors}"
                        )

                        self.kto_writer.save_invalid_response(
                            input_text=input_text,
                            raw_response=json.dumps(cases_data, ensure_ascii=False),
                            error_message='; '.join(validation_errors),
                            mapping_info=mapping,
                        )

                        if attempt < self.MAX_RETRIES - 1:
                            time.sleep(self.RETRY_DELAY_SECONDS)
                            retries += 1
                            continue

                        last_result = type(ai_result)(
                            success=False,
                            result=valid_cases if valid_cases else None,
                            raw_content=ai_result.raw_content,
                            error=f'数据验证失败: {"; ".join(validation_errors)}',
                        )
                        break

                    # 验证通过，保存正样本
                    self.kto_writer.save_valid_response(
                        input_text=input_text,
                        response=valid_cases,
                        mapping_info=mapping,
                    )

                    # 更新结果为验证后的数据
                    last_result = type(ai_result)(
                        success=True,
                        result=valid_cases,
                        raw_content=ai_result.raw_content,
                        error=None,
                    )
                    break

                except AIServiceError as e:
                    logger.warning(
                        f"AI服务错误 [{mapping.get('module')}-{mapping.get('func_point')}] "
                        f"(尝试 {attempt + 1}/{self.MAX_RETRIES}): {e.message}"
                    )

                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY_SECONDS)
                        retries += 1
                        continue

                    # 创建错误结果
                    from apps.testcase.clients.ai_client import AIGenerationResult
                    last_result = AIGenerationResult(
                        success=False,
                        result=None,
                        raw_content=None,
                        error=e.message,
                    )
                    break

            results.append(last_result)

        return results, retries

    def _save_cases_with_models(
        self,
        cases_data: List[dict],
        version_id: str,
        user: User
    ) -> tuple:
        """
        保存用例并返回模型实例列表

        Returns:
            (created_cases列表, error_count, errors列表)
        """
        from apps.testcase.models import TestCase, TestModule

        created_cases = []
        error_count = 0
        errors = []

        for i, case_data in enumerate(cases_data):
            try:
                priority = self._parse_priority(case_data.get("priority"))
                steps_text = self._parse_steps(case_data)
                expected_result_text = self._parse_expected_result(case_data)
                title = self._parse_title(case_data) or f"AI生成用例_{i+1}"
                precondition = self._parse_precondition(case_data)

                # 处理模块
                module_name = case_data.get("module", "") or case_data.get("模块", "")
                module = None
                if module_name:
                    module, _ = TestModule.objects.get_or_create(
                        version_id=version_id,
                        name=module_name,
                        defaults={'sort_order': 0}
                    )

                case = TestCase.objects.create(
                    title=title,
                    precondition=precondition,
                    priority=priority,
                    tags=case_data.get("tags", []),
                    version_id=version_id,
                    module=module,
                    created_by=user,
                    updated_by=user,
                    generation_source="ai_generated",
                    review_status="pending",
                    steps=steps_text,
                    expected_result=expected_result_text,
                )

                created_cases.append({
                    'id': case.id,
                    'title': case.title,
                    'module': module_name,
                    'priority': case.priority,
                })

            except Exception as e:
                error_count += 1
                errors.append({
                    "index": i,
                    "title": self._parse_title(case_data),
                    "error": str(e),
                })

        return created_cases, error_count, errors

    @transaction.atomic
    def _save_with_transaction(
        self,
        ai_results: List,
        item_mapping: List[dict],
        version_id: str,
        user: User
    ) -> tuple:
        """
        事务保护的保存操作

        Args:
            ai_results: AI生成结果列表
            item_mapping: 映射信息列表
            version_id: 版本ID
            user: 当前用户

        Returns:
            (created_cases列表, error_count, errors列表)
        """
        from apps.testcase.models import TestCase, TestModule

        created_cases = []
        error_count = 0
        errors = []

        # 预先创建所有模块（减少重复查询）
        module_names = set(m['module'] for m in item_mapping if m.get('module'))
        module_map = {}
        for name in module_names:
            module_map[name] = self.module_repository.get_or_create(
                version_id=version_id,
                name=name,
                defaults={'sort_order': 0}
            )

        for i, ai_result in enumerate(ai_results):
            mapping = item_mapping[i] if i < len(item_mapping) else {}

            if ai_result.success and ai_result.result:
                cases_data = ai_result.result if isinstance(ai_result.result, list) else [ai_result.result]

                for case_data in cases_data:
                    try:
                        priority = self._parse_priority(case_data.get("priority"))
                        steps_text = self._parse_steps(case_data)
                        expected_result_text = self._parse_expected_result(case_data)
                        title = self._parse_title(case_data) or f"{module_name}-{mapping.get('func_point', '测试用例')}"
                        precondition = self._parse_precondition(case_data)

                        module_name = mapping.get('module', '')
                        module = module_map.get(module_name)

                        case = TestCase.objects.create(
                            title=title,
                            precondition=precondition,
                            priority=priority,
                            tags=case_data.get("tags", []),
                            version_id=version_id,
                            module=module,
                            created_by=user,
                            updated_by=user,
                            generation_source="ai_generated",
                            review_status="pending",
                            steps=steps_text,
                            expected_result=expected_result_text,
                        )

                        created_cases.append({
                            'id': case.id,
                            'title': case.title,
                            'module': module_name,
                            'priority': case.priority,
                        })

                    except Exception as e:
                        error_count += 1
                        errors.append({
                            'module': mapping.get('module', ''),
                            'func_point': mapping.get('func_point', ''),
                            'error': f'保存失败: {str(e)}',
                        })
            else:
                error_count += 1
                errors.append({
                    'module': mapping.get('module', ''),
                    'func_point': mapping.get('func_point', ''),
                    'error': ai_result.error or '生成失败',
                })

        logger.info(f"保存完成: 创建 {len(created_cases)} 条, 失败 {error_count} 条")
        return created_cases, error_count, errors

    def _build_input_text(self, item: dict) -> str:
        """构建输入文本"""
        module = item.get('module', '')
        func_point = item.get('func_point', '')
        related_detail = item.get('related_detail', '')

        if related_detail and related_detail != "无相关需求":
            return f"模块：{module}，功能点：{func_point}\n关联需求：{related_detail}"
        return f"模块：{module}，功能点：{func_point}\n关联需求：无"

    def _parse_priority(self, priority_str: str) -> str:
        """解析优先级"""
        if not priority_str:
            return 'p2'
        priority = str(priority_str).lower()

        # 支持中文优先级
        priority_map = {
            'p0': 'p0', '最高': 'p0', '紧急': 'p0',
            'p1': 'p1', '高': 'p1', '重要': 'p1',
            'p2': 'p2', '中': 'p2', '一般': 'p2',
            'p3': 'p3', '低': 'p3', '次要': 'p3',
        }

        if priority in priority_map:
            return priority_map[priority]

        return 'p2'

    def _parse_steps(self, case_data: dict) -> str:
        """解析测试步骤"""
        # 支持多种字段名：steps, test_steps, step
        steps_text = case_data.get('steps', '')
        if steps_text:
            return steps_text

        steps_data = case_data.get('test_steps', [])
        if steps_data:
            steps_lines = []
            for step in steps_data:
                if isinstance(step, dict):
                    action = step.get('action', '') or step.get('description', '') or step.get('step', '')
                    if action:
                        steps_lines.append(action)
                elif isinstance(step, str):
                    steps_lines.append(step)
            if steps_lines:
                return "\n".join(f"{idx}. {line}" for idx, line in enumerate(steps_lines, 1))

        return case_data.get('description', '执行测试')

    def _parse_expected_result(self, case_data: dict) -> str:
        """解析预期结果"""
        # 支持多种字段名：expected_result, expectation, expected
        expected_result = case_data.get('expected_result', '') or case_data.get('expectation', '') or case_data.get('expected', '')
        if expected_result:
            return expected_result

        steps_data = case_data.get('test_steps', [])
        if steps_data:
            result_lines = []
            for step in steps_data:
                if isinstance(step, dict):
                    er = step.get('expected_result', '') or step.get('expected', '')
                    if er:
                        result_lines.append(er)
            if result_lines:
                return "\n".join(result_lines)

        return ''

    def _parse_title(self, case_data: dict) -> str:
        """解析标题"""
        # 支持多种字段名：title, testpoint, name
        return case_data.get('title', '') or case_data.get('testpoint', '') or case_data.get('name', '未命名测试用例')

    def _parse_precondition(self, case_data: dict) -> str:
        """解析前置条件"""
        # 支持多种字段名：precondition, preconditions, precondition
        return case_data.get('precondition', '') or case_data.get('preconditions', '') or case_data.get('pre_condition', '')
