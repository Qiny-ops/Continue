"""
API测试用例生成服务

从 apitest/views/api_testcase.py 移出的业务逻辑函数：
- _parse_generated_cases: 从 LLM 响应解析生成的测试用例
- _save_generated_cases: 批量保存生成的测试用例到数据库
- _parse_priority: 中文优先级字符串 → p0-p3 映射
"""

import json
import logging

from apps.apitest.models import ApiTestCase

logger = logging.getLogger(__name__)


def parse_generated_cases(content: str) -> list:
    """从 LLM 响应内容中解析生成的测试用例列表"""
    cases = []

    # 尝试提取 JSON 代码块
    if "```json" in content:
        parts = content.split("```json")
        if len(parts) > 1:
            json_part = parts[1].split("```")[0].strip()
            content = json_part
    elif "```" in content:
        parts = content.split("```")
        if len(parts) > 1:
            json_part = parts[1].strip()
            content = json_part

    # 提取最外层 JSON 数组
    start = content.rfind('[')
    if start != -1:
        bracket_count = 0
        end = -1
        for i in range(start, len(content)):
            if content[i] == '[':
                bracket_count += 1
            elif content[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
        if end > start:
            content = content[start:end]
            logger.info(f"提取 JSON 数组，长度: {len(content)}")
        else:
            start = content.rfind('{')
            if start != -1:
                bracket_count = 0
                end = -1
                for i in range(start, len(content)):
                    if content[i] == '{':
                        bracket_count += 1
                    elif content[i] == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                if end > start:
                    content = content[start:end]
                    logger.info(f"提取 JSON 对象，长度: {len(content)}")

    try:
        cases = json.loads(content)
        if isinstance(cases, list):
            valid_cases = [c for c in cases if isinstance(c, dict)]
            if len(valid_cases) < len(cases):
                logger.warning(f"过滤了 {len(cases) - len(valid_cases)} 个非字典元素")
            logger.info(f"成功解析 {len(valid_cases)} 个测试用例")
            return valid_cases
        elif isinstance(cases, dict):
            logger.info("解析到单个测试用例对象，转换为列表")
            return [cases]
        logger.warning(f"解析结果不是列表或字典: {type(cases)}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}, 内容预览: {content[:500]}")
        return []


def save_generated_cases(cases_data: list, project_id: int, user, knowledge_base_id: str) -> list:
    """批量保存 AI 生成的测试用例

    去重策略：按 (name, testpoint, expectation) 归一化指纹，跳过
    1) 本项目内已存在的 ai_generated 用例
    2) 本次批次内重复出现的用例
    避免模型反复生成同一测试点、或用户多次点击"重新生成"导致重复行累积。
    """
    from apps.projects.models import Project
    try:
        Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        logger.error(f"项目不存在: project_id={project_id}")
        return []

    def fingerprint(name, testpoint, expectation):
        return (
            (name or "").strip().lower(),
            (testpoint or "").strip().lower(),
            (expectation or "").strip().lower(),
        )

    # 已存在用例指纹（仅 ai_generated 来源参与去重）
    existing = set()
    try:
        rows = ApiTestCase.objects.filter(
            project_id=project_id, source='ai_generated'
        ).values_list('name', 'testpoint', 'expectation')
        for n, tp, exp in rows:
            existing.add(fingerprint(n, tp, exp))
    except Exception as e:
        logger.warning(f"去重查询失败，跳过历史去重: {e}")

    saved_ids = []
    failed_count = 0
    seen_in_batch = set()

    for case_data in cases_data:
        try:
            case_name = case_data.get("apiname") or case_data.get("name") or case_data.get("title") or "未命名用例"
            testpoint = case_data.get("testpoint") or case_data.get("test_point", "")
            expectation = case_data.get("expectation") or case_data.get("expected", "")
            fp = fingerprint(case_name, testpoint, expectation)

            if fp in existing or fp in seen_in_batch:
                logger.info(f"跳过重复用例（去重）: name={case_name}, testpoint={testpoint}")
                continue
            seen_in_batch.add(fp)

            test_case = ApiTestCase.objects.create(
                project_id=project_id,
                name=case_name,
                precondition=case_data.get("precondition", ""),
                testpoint=testpoint,
                expectation=expectation,
                priority=_parse_priority(case_data.get("priority")),
                test_data=case_data.get("test_data", {}),
                run_list=case_data.get("run_list", []),
                status='draft',
                knowledge_base_id=knowledge_base_id,
                source='ai_generated',
                created_by=user,
                updated_by=user
            )
            saved_ids.append(test_case.id)
            logger.info(f"保存用例成功: id={test_case.id}, name={case_name}")

        except Exception as e:
            failed_count += 1
            logger.error(f"保存用例失败: {case_data}, error: {e}")

    skipped = len(cases_data) - len(saved_ids) - failed_count
    if skipped > 0:
        logger.info(f"保存用例完成：成功 {len(saved_ids)} 条，跳过重复 {skipped} 条，失败 {failed_count} 条")
    elif failed_count > 0:
        logger.warning(f"保存用例完成，成功 {len(saved_ids)} 条，失败 {failed_count} 条")
    else:
        logger.info(f"保存用例完成，全部成功，共 {len(saved_ids)} 条")

    return saved_ids


def _parse_priority(priority_str: str) -> str:
    """中文优先级字符串 → p0/p1/p2/p3 映射"""
    if not priority_str:
        return 'p2'

    priority = str(priority_str).lower()
    mapping = {
        'p0': 'p0', '最高': 'p0', '紧急': 'p0',
        'p1': 'p1', '高': 'p1', '重要': 'p1',
        'p2': 'p2', '中': 'p2', '一般': 'p2',
        'p3': 'p3', '低': 'p3', '次要': 'p3',
    }
    return mapping.get(priority, 'p2')
