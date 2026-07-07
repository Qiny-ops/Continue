"""
测试需求提炼流程（不调用AI微服务）

测试范围：
1. RequirementService.extract() - 需求提取
2. RequirementService.retrieve_related() - 检索关联需求
3. AIGenerationService._build_input_text() - 构建输入文本
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')
sys.path.insert(0, 'E:/Continue/Testbackend')
django.setup()

import logging
from unittest.mock import Mock, patch, MagicMock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_json_parser():
    """测试JSON解析器"""
    from apps.core.utils.json_parser import JSONParser

    print("\n" + "="*60)
    print("Test 1: JSONParser - JSON Parser")
    print("="*60)

    # 测试1: 标准JSON
    test_cases = [
        # (名称, 输入文本, 期望成功)
        ("Standard JSON Array", '[{"模块":"登录","功能点":"用户登录验证"}]', True),
        ("With Markdown Block", '```json\n[{"模块":"登录","功能点":"用户登录"}]\n```', True),
        ("Chinese Punctuation", '[{"模块":"登录"，"功能点":"验证"}]', True),
        ("Mixed Format", '这是结果：[{"模块":"登录","功能点":"验证"}]其他内容', True),
        ("Invalid JSON", '这不是JSON', False),
        ("Empty String", '', False),
    ]

    for name, text, expect_success in test_cases:
        success, result, error = JSONParser.try_parse(text)
        status = "[PASS]" if success == expect_success else "[FAIL]"
        print(f"  {status} {name}: success={success}, expect={expect_success}")
        if success:
            print(f"      Result: {result}")
        else:
            print(f"      Error: {error}")

    print("\nJSONParser test completed")


def test_requirement_service_extract():
    """测试需求提取（Mock外部服务）"""
    from apps.knowledge.services.requirement_service import RequirementService

    print("\n" + "="*60)
    print("Test 2: RequirementService.extract() - Extract Requirements")
    print("="*60)

    # 创建Mock Repository
    mock_repository = Mock()

    # Mock create_session
    mock_repository.create_session.return_value = {
        'success': True,
        'data': {'id': 'test-session-123'}
    }

    # Mock agent_chat - 返回模拟的需求提取结果
    mock_repository.agent_chat.return_value = {
        'success': True,
        'data': {
            'content': '''[
                {"模块": "用户登录", "功能点": "用户名密码登录验证"},
                {"模块": "用户登录", "功能点": "验证码登录"},
                {"模块": "用户管理", "功能点": "新增用户"},
                {"模块": "用户管理", "功能点": "编辑用户信息"}
            ]'''
        }
    }

    # 创建Service实例
    service = RequirementService(repository=mock_repository)

    # 执行测试
    knowledge_base_ids = ['kb-test-001']
    knowledge_ids = ['file-test-001']

    requirements, session_id = service.extract(
        knowledge_base_ids=knowledge_base_ids,
        knowledge_ids=knowledge_ids,
    )

    print(f"  Session ID: {session_id}")
    print(f"  Extracted requirements count: {len(requirements)}")
    print(f"  Requirements list:")
    for i, req in enumerate(requirements, 1):
        print(f"    {i}. [{req.get('模块')}] {req.get('功能点')}")

    # 验证调用
    assert mock_repository.create_session.called, "Should call create_session"
    assert mock_repository.agent_chat.called, "Should call agent_chat"
    assert session_id == 'test-session-123', "Session ID should be correct"
    assert len(requirements) == 4, "Should extract 4 requirements"

    print("\n  [PASS] Requirement extract test passed")


def test_requirement_service_retrieve_related():
    """测试检索关联需求"""
    from apps.knowledge.services.requirement_service import RequirementService

    print("\n" + "="*60)
    print("Test 3: RequirementService.retrieve_related() - Retrieve Related")
    print("="*60)

    # 创建Mock Repository
    mock_repository = Mock()

    # Mock agent_chat - 模拟返回关联需求
    def mock_agent_chat(**kwargs):
        query = kwargs.get('query', '')
        if '用户名密码登录验证' in query:
            return {
                'success': True,
                'data': {'content': '用户输入用户名和密码，点击登录按钮，系统验证用户名密码是否正确。'}
            }
        elif '验证码登录' in query:
            return {
                'success': True,
                'data': {'content': '用户输入手机号，点击获取验证码，输入验证码后登录。'}
            }
        else:
            return {
                'success': True,
                'data': {'content': '无相关需求'}
            }

    mock_repository.agent_chat.side_effect = mock_agent_chat

    # 创建Service实例
    service = RequirementService(repository=mock_repository)

    # 测试数据
    requirements = [
        {'模块': '用户登录', '功能点': '用户名密码登录验证'},
        {'模块': '用户登录', '功能点': '验证码登录'},
        {'模块': '用户管理', '功能点': '新增用户'},
    ]

    # 执行测试（串行模式）
    print("\n  --- Serial Mode ---")
    requirements_with_details = service.retrieve_related(
        requirements=requirements,
        knowledge_base_ids=['kb-test-001'],
        knowledge_ids=['file-test-001'],
        session_id='test-session-123',
        parallel=False,  # 串行模式
    )

    print(f"  Processed requirements count: {len(requirements_with_details)}")
    print(f"  Details:")
    for i, item in enumerate(requirements_with_details, 1):
        detail_preview = item['related_detail'][:50] + '...' if len(item['related_detail']) > 50 else item['related_detail']
        print(f"    {i}. [{item['module']}] {item['func_point']}")
        print(f"       Related: {detail_preview}")

    # 验证
    assert len(requirements_with_details) == 3, "Should process 3 requirements"
    assert mock_repository.agent_chat.call_count == 3, "Should call agent_chat 3 times"

    # 测试并行模式
    print("\n  --- Parallel Mode ---")
    mock_repository.agent_chat.reset_mock()
    mock_repository.agent_chat.side_effect = mock_agent_chat

    requirements_with_details_parallel = service.retrieve_related(
        requirements=requirements,
        knowledge_base_ids=['kb-test-001'],
        knowledge_ids=['file-test-001'],
        session_id='test-session-123',
        parallel=True,  # 并行模式
        max_workers=3,
    )

    print(f"  Processed requirements count: {len(requirements_with_details_parallel)}")
    assert len(requirements_with_details_parallel) == 3, "Should process 3 requirements in parallel"
    assert mock_repository.agent_chat.call_count == 3, "Should call agent_chat 3 times in parallel"

    print("\n  [PASS] Retrieve related test passed")


def test_build_input_text():
    """测试构建输入文本"""
    from apps.testcase.services.ai_generation_service import AIGenerationService

    print("\n" + "="*60)
    print("Test 4: AIGenerationService._build_input_text() - Build Input Text")
    print("="*60)

    service = AIGenerationService()

    # 测试用例
    test_cases = [
        # (名称, 输入数据, 期望包含的内容)
        ("With Related Detail",
         {'module': '登录', 'func_point': '用户登录验证', 'related_detail': '用户输入账号密码登录'},
         ['模块：登录', '功能点：用户登录验证', '关联需求：用户输入账号密码登录']),

        ("No Related Detail",
         {'module': '登录', 'func_point': '验证码登录', 'related_detail': '无相关需求'},
         ['模块：登录', '功能点：验证码登录', '关联需求：无']),

        ("Empty Related Detail",
         {'module': '用户', 'func_point': '新增用户', 'related_detail': ''},
         ['模块：用户', '功能点：新增用户', '关联需求：无']),
    ]

    for name, item, expected_contents in test_cases:
        result = service._build_input_text(item)
        print(f"\n  Test: {name}")
        print(f"    Input: {item}")
        print(f"    Output: {result}")

        # 验证期望内容
        all_present = all(content in result for content in expected_contents)
        status = "[PASS]" if all_present else "[FAIL]"
        print(f"    {status} Contains all expected content: {all_present}")

    print("\n  [PASS] Build input text test passed")


def test_generate_batch_preparation():
    """测试批量生成前的数据准备（不实际调用AI）"""
    from apps.testcase.services.ai_generation_service import AIGenerationService

    print("\n" + "="*60)
    print("Test 5: Batch Generation Preparation")
    print("="*60)

    service = AIGenerationService()

    # 模拟需求提取结果
    requirements_with_details = [
        {'module': '用户登录', 'func_point': '用户名密码登录验证', 'related_detail': '用户输入账号密码'},
        {'module': '用户登录', 'func_point': '验证码登录', 'related_detail': '用户输入手机号获取验证码'},
        {'module': '用户管理', 'func_point': '新增用户', 'related_detail': '无相关需求'},
    ]

    # 构建批量请求数据（不实际调用AI）
    batch_items = []
    item_mapping = []

    for item in requirements_with_details:
        base_text = service._build_input_text(item)

        for j, prompt in enumerate(service.TEST_PROMPTS):
            batch_items.append({'input_text': f"{base_text}\n{prompt}"})
            item_mapping.append({
                'module': item['module'],
                'func_point': item['func_point'],
                'test_type_index': j,
            })

    print(f"  Requirements count: {len(requirements_with_details)}")
    print(f"  Test directions count: {len(service.TEST_PROMPTS)}")
    print(f"  Total requests: {len(batch_items)} (expected: {len(requirements_with_details) * len(service.TEST_PROMPTS)})")

    print(f"\n  Batch request details:")
    for i, (batch_item, mapping) in enumerate(zip(batch_items, item_mapping)):
        test_type = service.TEST_TYPE_NAMES[mapping['test_type_index']]
        func_preview = mapping['func_point'][:15] + '...' if len(mapping['func_point']) > 15 else mapping['func_point']
        print(f"    [{i+1}] {mapping['module']} - {func_preview} [{test_type}]")
        if i >= 5:  # 只显示前6个
            print(f"    ... and {len(batch_items) - 6} more requests")
            break

    # 验证
    expected_count = len(requirements_with_details) * len(service.TEST_PROMPTS)
    assert len(batch_items) == expected_count, f"Request count should be {expected_count}"
    assert len(item_mapping) == expected_count, f"Mapping count should be {expected_count}"

    print(f"\n  [PASS] Batch generation preparation test passed")

    # 返回数据供后续使用
    return batch_items, item_mapping, requirements_with_details


def test_print_ai_request_data():
    """打印调用AI微服务之前的完整请求数据"""
    from apps.testcase.services.ai_generation_service import AIGenerationService
    import json

    print("\n" + "="*60)
    print("Test 7: Print AI Request Data (Before AI Service Call)")
    print("="*60)

    service = AIGenerationService()

    # 模拟需求提取结果
    requirements_with_details = [
        {'module': '用户登录', 'func_point': '用户名密码登录验证', 'related_detail': '用户输入用户名和密码，点击登录按钮，系统验证用户名密码是否正确，验证通过后跳转到首页。'},
        {'module': '用户登录', 'func_point': '验证码登录', 'related_detail': '用户输入手机号，点击获取验证码，系统发送短信验证码，用户输入验证码后点击登录，系统验证验证码是否正确。'},
        {'module': '用户管理', 'func_point': '新增用户', 'related_detail': '管理员点击新增用户按钮，填写用户名、密码、邮箱等信息，点击保存，系统创建新用户。'},
    ]

    # 构建批量请求数据
    batch_items = []
    item_mapping = []

    for item in requirements_with_details:
        base_text = service._build_input_text(item)

        for j, prompt in enumerate(service.TEST_PROMPTS):
            batch_items.append({'input_text': f"{base_text}\n{prompt}"})
            item_mapping.append({
                'module': item['module'],
                'func_point': item['func_point'],
                'test_type_index': j,
            })

    # 将详细数据写入文件（UTF-8编码）
    output_lines = []

    output_lines.append("\n" + "-"*60)
    output_lines.append("1. Requirements with Details (Input Data)")
    output_lines.append("-"*60)
    for i, item in enumerate(requirements_with_details, 1):
        output_lines.append(f"\n  [{i}] Module: {item['module']}")
        output_lines.append(f"      Function Point: {item['func_point']}")
        output_lines.append(f"      Related Detail: {item['related_detail']}")

    output_lines.append("\n" + "-"*60)
    output_lines.append("2. Test Prompts (3 Directions)")
    output_lines.append("-"*60)
    for i, prompt in enumerate(service.TEST_PROMPTS, 1):
        output_lines.append(f"\n  [{i}] {service.TEST_TYPE_NAMES[i-1]}:")
        output_lines.append(f"      {prompt}")

    output_lines.append("\n" + "-"*60)
    output_lines.append("3. Batch Request Items (Full Input Text for AI)")
    output_lines.append("-"*60)
    for i, (batch_item, mapping) in enumerate(zip(batch_items, item_mapping), 1):
        test_type = service.TEST_TYPE_NAMES[mapping['test_type_index']]
        output_lines.append(f"\n  {'='*50}")
        output_lines.append(f"  Request #{i}")
        output_lines.append(f"  Module: {mapping['module']}")
        output_lines.append(f"  Function Point: {mapping['func_point']}")
        output_lines.append(f"  Test Type: {test_type}")
        output_lines.append(f"  {'='*50}")
        output_lines.append(f"\n  Input Text:")
        output_lines.append(f"  {'-'*46}")
        input_text = batch_item['input_text']
        for line in input_text.split('\n'):
            output_lines.append(f"  {line}")
        output_lines.append(f"  {'-'*46}")

    output_lines.append("\n" + "-"*60)
    output_lines.append("4. Summary Statistics")
    output_lines.append("-"*60)
    output_lines.append(f"  Total Requirements: {len(requirements_with_details)}")
    output_lines.append(f"  Test Directions: {len(service.TEST_PROMPTS)}")
    output_lines.append(f"  Total AI Requests: {len(batch_items)}")
    output_lines.append(f"  Batch Size Limit: 10 (will split into {(len(batch_items) + 9) // 10} batches)")

    output_lines.append("\n" + "-"*60)
    output_lines.append("5. JSON Payload Preview (First Request)")
    output_lines.append("-"*60)
    first_payload = {
        "messages": [
            {"role": "user", "content": batch_items[0]['input_text']}
        ]
    }
    output_lines.append(f"\n  POST /api/v1/infer")
    output_lines.append(f"  Content-Type: application/json")
    output_lines.append(f"\n  {json.dumps(first_payload, ensure_ascii=False, indent=2)}")

    output_lines.append("\n" + "-"*60)
    output_lines.append("6. Batch API Payload Preview")
    output_lines.append("-"*60)
    batch_payload = {
        "items": [
            {"messages": [{"role": "user", "content": item['input_text']}]}
            for item in batch_items[:3]
        ]
    }
    output_lines.append(f"\n  POST /api/v1/batch")
    output_lines.append(f"  Content-Type: application/json")
    output_lines.append(f"  (Showing first 3 of {len(batch_items)} items)")
    output_lines.append(f"\n  {json.dumps(batch_payload, ensure_ascii=False, indent=2)}")

    # 写入文件
    output_file = 'E:/Continue/Testbackend/ai_request_data.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\n  Detailed data written to: {output_file}")
    print("\n  [PASS] AI request data printed successfully")

    return batch_items, item_mapping


def test_full_flow_mock():
    """测试完整流程（Mock AI微服务调用）"""
    from apps.knowledge.services.requirement_service import RequirementService
    from apps.testcase.services.ai_generation_service import AIGenerationService
    from apps.testcase.clients.ai_client import AIGenerationResult

    print("\n" + "="*60)
    print("Test 6: Full Flow Test (Mock AI Service)")
    print("="*60)

    # 1. Mock RequirementService
    mock_req_service = Mock()
    mock_req_service.extract.return_value = (
        [
            {'模块': '用户登录', '功能点': '用户名密码登录验证'},
            {'模块': '用户登录', '功能点': '验证码登录'},
        ],
        'test-session-123'
    )
    mock_req_service.retrieve_related.return_value = [
        {'module': '用户登录', 'func_point': '用户名密码登录验证', 'related_detail': '用户输入账号密码'},
        {'module': '用户登录', 'func_point': '验证码登录', 'related_detail': '用户输入手机号'},
    ]

    # 2. Mock AI Client
    mock_ai_client = Mock()
    mock_ai_client.generate_cases_batch.return_value = [
        AIGenerationResult(success=True, result={'title': '测试用例1', 'steps': '步骤1'}, raw_content=None, error=None),
        AIGenerationResult(success=True, result={'title': '测试用例2', 'steps': '步骤2'}, raw_content=None, error=None),
        AIGenerationResult(success=False, result=None, raw_content=None, error='生成失败'),
        AIGenerationResult(success=True, result={'title': '测试用例4', 'steps': '步骤4'}, raw_content=None, error=None),
        AIGenerationResult(success=True, result={'title': '测试用例5', 'steps': '步骤5'}, raw_content=None, error=None),
        AIGenerationResult(success=True, result={'title': '测试用例6', 'steps': '步骤6'}, raw_content=None, error=None),
    ]

    # 3. Mock Repository
    mock_case_repo = Mock()
    mock_case_repo.bulk_create_ai_cases.return_value = [Mock(id=i) for i in range(5)]

    mock_module_repo = Mock()
    mock_module_repo.get_or_create.return_value = Mock(id=1)

    # 4. 创建Service实例
    service = AIGenerationService(
        ai_client=mock_ai_client,
        case_repository=mock_case_repo,
        module_repository=mock_module_repo,
        requirement_service=mock_req_service,
    )

    # 5. 执行测试（只到生成阶段，不保存）
    requirements_with_details = mock_req_service.retrieve_related()
    ai_results, item_mapping = service._generate_batch(requirements_with_details)

    print(f"  Step 1 - Extract Requirements:")
    requirements, session_id = mock_req_service.extract()
    print(f"    Requirements count: {len(requirements)}")
    print(f"    Session ID: {session_id}")

    print(f"\n  Step 2 - Retrieve Related:")
    print(f"    Processed count: {len(requirements_with_details)}")

    print(f"\n  Step 3 - Build Batch Requests:")
    print(f"    Request count: {len(item_mapping)}")
    print(f"    AI Results count: {len(ai_results)}")

    print(f"\n  Step 4 - AI Generation Results:")
    success_count = sum(1 for r in ai_results if r.success)
    fail_count = sum(1 for r in ai_results if not r.success)
    print(f"    Success: {success_count}")
    print(f"    Failed: {fail_count}")

    # 验证
    assert mock_req_service.extract.called, "Should call extract"
    assert mock_req_service.retrieve_related.called, "Should call retrieve_related"
    assert mock_ai_client.generate_cases_batch.called, "Should call generate_cases_batch"

    print("\n  [PASS] Full flow test passed")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Requirement Extraction Flow Test")
    print("Scope: Extract -> Retrieve Related -> Build Input -> Batch Prep")
    print("="*60)

    try:
        test_json_parser()
        test_requirement_service_extract()
        test_requirement_service_retrieve_related()
        test_build_input_text()
        test_generate_batch_preparation()
        test_full_flow_mock()
        test_print_ai_request_data()

        print("\n" + "="*60)
        print("All tests passed!")
        print("="*60)

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Test exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
