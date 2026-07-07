"""
测试知识库文件的功能点提取（真实环境）
指定知识库：测试版本
指定文件：测试用例管理平台需求文档
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')
sys.path.insert(0, 'E:/Continue/Testbackend')
django.setup()

import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_knowledge_base_extraction():
    """测试知识库功能点提取"""
    from apps.knowledge.services.requirement_service import RequirementService
    from apps.knowledge.repositories.weknora_repository import weknora_repository
    from apps.testcase.services.ai_generation_service import AIGenerationService

    # 目标知识库和文件
    TARGET_KB_NAME = "测试版本"
    TARGET_FILE_NAME = "测试用例管理平台需求文档"

    print("\n" + "="*70)
    print("Knowledge Base Function Points Extraction Test")
    print(f"Target: {TARGET_KB_NAME} / {TARGET_FILE_NAME}")
    print("="*70)

    # ============================================================
    # Step 1: 检查配置
    # ============================================================
    print("\n[Step 1] Check Configuration")
    print("-"*70)

    from django.conf import settings

    base_url = getattr(settings, 'WEKNORA_BASE_URL', '')
    api_key = getattr(settings, 'WEKNORA_API_KEY', '')

    print(f"  WEKNORA_BASE_URL: {base_url}")
    print(f"  WEKNORA_API_KEY: {'*' * 8 + api_key[-4:] if api_key and len(api_key) > 4 else 'Not Set'}")

    if not api_key:
        print("\n  [ERROR] WEKNORA_API_KEY not configured!")
        return

    print("  [OK] Configuration check passed")

    # ============================================================
    # Step 2: 获取知识库列表
    # ============================================================
    print("\n[Step 2] Get Knowledge Base List")
    print("-"*70)

    try:
        kb_result = weknora_repository.list_knowledge_bases()
        if kb_result.get('success'):
            kb_list = kb_result.get('data', [])
            print(f"  Found {len(kb_list)} knowledge bases:")
            for i, kb in enumerate(kb_list, 1):
                name = kb.get('name', 'N/A')
                marker = " <-- TARGET" if name == TARGET_KB_NAME else ""
                print(f"    [{i}] ID: {kb.get('id')}, Name: {name}{marker}")
        else:
            print(f"  [ERROR] Failed to get knowledge bases: {kb_result.get('error')}")
            return
    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        return

    if not kb_list:
        print("\n  [ERROR] No knowledge bases found!")
        return

    # 查找目标知识库
    selected_kb = None
    for kb in kb_list:
        if kb.get('name') == TARGET_KB_NAME:
            selected_kb = kb
            break

    if not selected_kb:
        print(f"\n  [ERROR] Knowledge base '{TARGET_KB_NAME}' not found!")
        return

    selected_kb_id = selected_kb.get('id')
    print(f"\n  Selected KB: {TARGET_KB_NAME}")
    print(f"  KB ID: {selected_kb_id}")

    # ============================================================
    # Step 3: 获取知识库文件列表
    # ============================================================
    print("\n[Step 3] Get Knowledge Base Files")
    print("-"*70)

    try:
        files_result = weknora_repository.list_knowledge(selected_kb_id)
        if files_result.get('success'):
            files = files_result.get('data', {})
            # 打印实际返回结构
            print(f"  Raw response data keys: {files.keys() if isinstance(files, dict) else 'list'}")

            # 获取文件列表
            if isinstance(files, dict):
                files_list = files.get('list', files.get('items', []))
            else:
                files_list = files if isinstance(files, list) else []

            print(f"  Found {len(files_list)} files:")
            for i, f in enumerate(files_list, 1):
                # 打印文件对象的所有字段
                if i == 1:
                    print(f"    [DEBUG] First file fields: {f.keys() if isinstance(f, dict) else 'not dict'}")

                # 尝试多种可能的字段名
                name = f.get('title') or f.get('name') or f.get('fileName') or f.get('filename') or 'N/A'
                marker = " <-- TARGET" if TARGET_FILE_NAME in name else ""
                print(f"    [{i}] ID: {f.get('id')}, Name: {name}{marker}")
        else:
            print(f"  [ERROR] Failed to get files: {files_result.get('error')}")
            return
    except Exception as e:
        print(f"  [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return

    if not files_list:
        print("\n  [ERROR] No files found in knowledge base!")
        return

    # 查找目标文件
    selected_file = None
    for f in files_list:
        name = f.get('title') or f.get('name') or f.get('fileName') or f.get('filename') or ''
        if TARGET_FILE_NAME in name:
            selected_file = f
            break

    if not selected_file:
        print(f"\n  [ERROR] File '{TARGET_FILE_NAME}' not found!")
        print("  Available files:")
        for f in files_list:
            name = f.get('title') or f.get('name') or f.get('fileName') or f.get('filename') or 'N/A'
            print(f"    - {name}")
        return

    selected_file_id = selected_file.get('id')
    selected_file_name = selected_file.get('title') or selected_file.get('name') or selected_file.get('fileName') or 'Unknown'
    print(f"\n  Selected File: {selected_file_name}")
    print(f"  File ID: {selected_file_id}")

    # ============================================================
    # Step 4: 提取功能点
    # ============================================================
    print("\n[Step 4] Extract Function Points")
    print("-"*70)

    service = RequirementService()

    try:
        requirements, session_id = service.extract(
            knowledge_base_ids=[selected_kb_id],
            knowledge_ids=[selected_file_id],
        )

        print(f"  Session ID: {session_id}")
        print(f"  Extracted function points: {len(requirements)}")

        if not requirements:
            print("\n  [WARNING] No function points extracted!")
            return

        print("\n  Function Points:")
        for i, req in enumerate(requirements, 1):
            module = req.get('模块', 'N/A')
            func_point = req.get('功能点', 'N/A')
            print(f"    [{i}] Module: {module}")
            print(f"        Function: {func_point}")

    except Exception as e:
        print(f"  [ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================================
    # Step 5: 检索关联需求
    # ============================================================
    print("\n[Step 5] Retrieve Related Requirements (Parallel)")
    print("-"*70)

    try:
        requirements_with_details = service.retrieve_related(
            requirements=requirements,
            knowledge_base_ids=[selected_kb_id],
            knowledge_ids=[selected_file_id],
            session_id=session_id,
            parallel=True,
            max_workers=5,
        )

        print(f"  Processed: {len(requirements_with_details)} function points")

        for i, item in enumerate(requirements_with_details, 1):
            detail = item.get('related_detail', '')
            detail_preview = detail[:80] + '...' if len(detail) > 80 else detail
            print(f"\n    [{i}] {item['module']} - {item['func_point']}")
            print(f"        Related: {detail_preview}")

    except Exception as e:
        print(f"  [ERROR] Retrieve related failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================================
    # Step 6: 构建AI请求数据
    # ============================================================
    print("\n[Step 6] Build AI Request Data")
    print("-"*70)

    ai_service = AIGenerationService()

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

    print(f"  Total batch requests: {len(batch_items)}")
    print(f"  ( {len(requirements_with_details)} function points x {len(ai_service.TEST_PROMPTS)} test directions )")

    # ============================================================
    # Step 7: 保存结果到文件
    # ============================================================
    print("\n[Step 7] Save Results")
    print("-"*70)

    output_data = {
        'knowledge_base': {
            'id': selected_kb_id,
            'name': TARGET_KB_NAME,
        },
        'file': {
            'id': selected_file_id,
            'name': selected_file_name,
        },
        'session_id': session_id,
        'requirements_count': len(requirements),
        'requirements': requirements,
        'requirements_with_details': requirements_with_details,
        'batch_items_count': len(batch_items),
        'sample_input_text': batch_items[0]['input_text'] if batch_items else None,
    }

    output_file = 'E:/Continue/Testbackend/knowledge_extraction_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  Results saved to: {output_file}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"""
  Knowledge Base: {TARGET_KB_NAME}
  File: {selected_file_name}
  Session ID: {session_id}

  Extracted Function Points: {len(requirements)}
  Related Requirements: {len(requirements_with_details)}
  Total AI Requests: {len(batch_items)}

  Status: READY FOR AI SERVICE CALL
    """)

    print("="*70)
    print("Test completed successfully!")
    print("="*70)


if __name__ == '__main__':
    test_knowledge_base_extraction()
