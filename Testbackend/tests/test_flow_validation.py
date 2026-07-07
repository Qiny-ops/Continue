"""
测试调用AI微服务之前的完整数据流程验证
验证内容：
1. 需求提取结果格式
2. 关联需求检索结果
3. 构建的输入文本
4. 批量请求数据结构
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')
sys.path.insert(0, 'E:/Continue/Testbackend')
django.setup()

import logging
from unittest.mock import Mock
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_flow_before_ai():
    """测试调用AI微服务之前的完整流程"""
    from apps.knowledge.services.requirement_service import RequirementService
    from apps.testcase.services.ai_generation_service import AIGenerationService

    print("\n" + "="*70)
    print("Full Flow Test: Before AI Service Call")
    print("="*70)

    # ============================================================
    # Step 1: Mock Repository
    # ============================================================
    print("\n[Step 1] Setup Mock Repository")
    print("-"*70)

    mock_repository = Mock()

    # Mock create_session
    mock_repository.create_session.return_value = {
        'success': True,
        'data': {'id': 'test-session-001'}
    }

    # Mock agent_chat for requirement extraction
    def mock_agent_chat(**kwargs):
        query = kwargs.get('query', '')

        # 需求提取 - 检查是否是提取需求的prompt
        if '提取出所有的功能点' in query:
            return {
                'success': True,
                'data': {
                    'content': '''[
                        {"模块": "用户登录", "功能点": "用户名密码登录验证"},
                        {"模块": "用户登录", "功能点": "验证码登录"},
                        {"模块": "用户管理", "功能点": "新增用户"},
                        {"模块": "用户管理", "功能点": "编辑用户信息"},
                        {"模块": "用户管理", "功能点": "删除用户"}
                    ]'''
                }
            }

        # 关联需求检索 - 检查功能点名称
        if '用户名密码登录验证' in query:
            return {
                'success': True,
                'data': {'content': '用户在登录页面输入用户名和密码，点击登录按钮。系统验证用户名和密码是否正确，验证通过后跳转到首页，验证失败显示错误提示。'}
            }
        elif '验证码登录' in query:
            return {
                'success': True,
                'data': {'content': '用户点击验证码登录，输入手机号，点击获取验证码。系统发送短信验证码到用户手机，用户输入验证码后点击登录，系统验证验证码是否正确。'}
            }
        elif '新增用户' in query:
            return {
                'success': True,
                'data': {'content': '管理员进入用户管理页面，点击新增用户按钮。填写用户名、密码、邮箱、角色等信息，点击保存。系统验证信息格式，创建新用户。'}
            }
        elif '编辑用户信息' in query:
            return {
                'success': True,
                'data': {'content': '管理员在用户列表中选择用户，点击编辑按钮。修改用户信息后点击保存，系统更新用户数据。'}
            }
        elif '删除用户' in query:
            return {
                'success': True,
                'data': {'content': '管理员在用户列表中选择用户，点击删除按钮。系统弹出确认框，确认后删除用户。'}
            }
        else:
            return {'success': True, 'data': {'content': '无相关需求'}}

    mock_repository.agent_chat.side_effect = mock_agent_chat

    print("  Mock Repository created")
    print("  - create_session: returns session-id")
    print("  - agent_chat: returns requirements and related details")

    # ============================================================
    # Step 2: Test Requirement Extraction
    # ============================================================
    print("\n[Step 2] Requirement Extraction")
    print("-"*70)

    req_service = RequirementService(repository=mock_repository)

    requirements, session_id = req_service.extract(
        knowledge_base_ids=['kb-001'],
        knowledge_ids=['file-001'],
    )

    print(f"  Session ID: {session_id}")
    print(f"  Extracted requirements: {len(requirements)}")

    # 验证需求提取结果
    assert session_id == 'test-session-001', "Session ID should be correct"
    assert len(requirements) == 5, f"Should extract 5 requirements, got {len(requirements)}"

    # 验证每个需求项的格式
    print("\n  Requirements format validation:")
    for i, req in enumerate(requirements, 1):
        assert '模块' in req, f"Requirement {i} missing '模块'"
        assert '功能点' in req, f"Requirement {i} missing '功能点'"
        print(f"    [{i}] Module: {req['模块']}, Function: {req['功能点']}")

    print("\n  [PASS] Requirement extraction validation passed")

    # ============================================================
    # Step 3: Test Related Requirement Retrieval
    # ============================================================
    print("\n[Step 3] Related Requirement Retrieval (Parallel)")
    print("-"*70)

    requirements_with_details = req_service.retrieve_related(
        requirements=requirements,
        knowledge_base_ids=['kb-001'],
        knowledge_ids=['file-001'],
        session_id=session_id,
        parallel=True,
        max_workers=5,
    )

    print(f"  Processed requirements: {len(requirements_with_details)}")

    # 验证每个需求项的格式
    print("\n  Related details validation:")
    for i, item in enumerate(requirements_with_details, 1):
        assert 'module' in item, f"Item {i} missing 'module'"
        assert 'func_point' in item, f"Item {i} missing 'func_point'"
        assert 'related_detail' in item, f"Item {i} missing 'related_detail'"

        detail_preview = item['related_detail'][:40] + '...' if len(item['related_detail']) > 40 else item['related_detail']
        print(f"    [{i}] {item['module']} - {item['func_point']}")
        print(f"        Detail: {detail_preview}")

    print("\n  [PASS] Related requirement retrieval validation passed")

    # ============================================================
    # Step 4: Test Input Text Building
    # ============================================================
    print("\n[Step 4] Input Text Building")
    print("-"*70)

    ai_service = AIGenerationService()

    print("\n  Built input texts:")
    for i, item in enumerate(requirements_with_details, 1):
        input_text = ai_service._build_input_text(item)

        # 验证输入文本包含必要信息
        assert item['module'] in input_text, f"Input text {i} missing module"
        assert item['func_point'] in input_text, f"Input text {i} missing func_point"

        # 验证格式
        assert '模块：' in input_text, f"Input text {i} missing '模块：' prefix"
        assert '功能点：' in input_text, f"Input text {i} missing '功能点：' prefix"
        assert '关联需求：' in input_text, f"Input text {i} missing '关联需求：' prefix"

        print(f"\n    [{i}] Input Text Preview:")
        lines = input_text.split('\n')
        for line in lines:
            print(f"        {line[:60]}{'...' if len(line) > 60 else ''}")

    print("\n  [PASS] Input text building validation passed")

    # ============================================================
    # Step 5: Test Batch Request Preparation
    # ============================================================
    print("\n[Step 5] Batch Request Preparation")
    print("-"*70)

    # 构建批量请求
    batch_items = []
    item_mapping = []

    for item in requirements_with_details:
        base_text = ai_service._build_input_text(item)

        for j, prompt in enumerate(ai_service.TEST_PROMPTS):
            batch_items.append({'input_text': f"{base_text}\n{prompt}"})
            item_mapping.append({
                'module': item['module'],
                'func_point': item['func_point'],
                'test_type_index': j,
            })

    expected_count = len(requirements_with_details) * len(ai_service.TEST_PROMPTS)

    print(f"  Requirements: {len(requirements_with_details)}")
    print(f"  Test directions: {len(ai_service.TEST_PROMPTS)}")
    print(f"  Total batch items: {len(batch_items)}")
    print(f"  Expected: {expected_count}")

    assert len(batch_items) == expected_count, f"Batch items count mismatch"
    assert len(item_mapping) == expected_count, f"Item mapping count mismatch"

    # 验证每个批量请求项
    print("\n  Batch items validation:")
    for i, (batch_item, mapping) in enumerate(zip(batch_items[:6], item_mapping[:6]), 1):
        test_type = ai_service.TEST_TYPE_NAMES[mapping['test_type_index']]

        # 验证映射信息
        assert 'module' in mapping, f"Mapping {i} missing 'module'"
        assert 'func_point' in mapping, f"Mapping {i} missing 'func_point'"
        assert 'test_type_index' in mapping, f"Mapping {i} missing 'test_type_index'"

        # 验证输入文本
        assert 'input_text' in batch_item, f"Batch item {i} missing 'input_text'"
        assert mapping['module'] in batch_item['input_text'], f"Batch item {i} missing module in text"

        print(f"    [{i}] {mapping['module']} - {mapping['func_point'][:15]}... [{test_type}]")

    if len(batch_items) > 6:
        print(f"    ... and {len(batch_items) - 6} more items")

    print("\n  [PASS] Batch request preparation validation passed")

    # ============================================================
    # Step 6: Verify Final Payload Structure
    # ============================================================
    print("\n[Step 6] Final Payload Structure Verification")
    print("-"*70)

    # 模拟构建发送给AI微服务的payload
    first_payload = {
        "messages": [
            {"role": "user", "content": batch_items[0]['input_text']}
        ]
    }

    print("\n  First Request Payload:")
    print(f"  POST /api/v1/infer")
    print(f"  Content-Type: application/json")
    print(f"\n  {json.dumps(first_payload, ensure_ascii=False, indent=4)[:500]}...")

    # 验证payload结构
    assert 'messages' in first_payload, "Payload missing 'messages'"
    assert len(first_payload['messages']) == 1, "Payload should have 1 message"
    assert first_payload['messages'][0]['role'] == 'user', "Message role should be 'user'"
    assert 'content' in first_payload['messages'][0], "Message missing 'content'"

    # 验证content包含必要信息
    content = first_payload['messages'][0]['content']
    assert '模块：' in content, "Content missing module info"
    assert '功能点：' in content, "Content missing function point info"
    assert '关联需求：' in content, "Content missing related requirement info"
    assert '测试方向：' in content, "Content missing test direction info"

    print("\n  [PASS] Payload structure validation passed")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    print(f"""
  [PASS] Step 1: Mock Repository Setup
  [PASS] Step 2: Requirement Extraction (5 requirements)
  [PASS] Step 3: Related Requirement Retrieval (parallel mode)
  [PASS] Step 4: Input Text Building (format validation)
  [PASS] Step 5: Batch Request Preparation ({len(batch_items)} items)
  [PASS] Step 6: Final Payload Structure Verification

  Total validations: 6/6 passed
    """)

    # 输出完整数据到文件
    output_data = {
        'session_id': session_id,
        'requirements': requirements,
        'requirements_with_details': requirements_with_details,
        'batch_items_count': len(batch_items),
        'test_prompts': ai_service.TEST_PROMPTS,
        'test_type_names': ai_service.TEST_TYPE_NAMES,
        'sample_payload': first_payload,
    }

    output_file = 'E:/Continue/Testbackend/test_flow_validation.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  Full data saved to: {output_file}")
    print("\n" + "="*70)
    print("All validations passed! Data is ready for AI service call.")
    print("="*70)


if __name__ == '__main__':
    test_full_flow_before_ai()
