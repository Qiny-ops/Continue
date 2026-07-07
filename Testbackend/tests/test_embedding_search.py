"""
测试 Embedding 向量检索原文

对比两种检索方式：
1. search_chunks - 返回文档片段
2. hybrid_search - 混合检索（向量+关键词）
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


def test_embedding_search():
    """测试 Embedding 向量检索"""
    from apps.knowledge.repositories.weknora_repository import weknora_repository
    from django.conf import settings

    # 目标知识库和文件
    TARGET_KB_NAME = "测试版本"
    TARGET_FILE_NAME = "测试用例管理平台需求文档"

    # 测试查询
    TEST_QUERIES = [
        "用户登录功能",
        "测试用例管理",
        "权限控制",
        "数据导出",
    ]

    print("\n" + "="*70)
    print("Embedding Vector Search Test")
    print("="*70)

    # ============================================================
    # Step 1: 检查配置
    # ============================================================
    print("\n[Step 1] Check Configuration")
    print("-"*70)

    base_url = getattr(settings, 'WEKNORA_BASE_URL', '')
    api_key = getattr(settings, 'WEKNORA_API_KEY', '')
    embedding_model_id = getattr(settings, 'WEKNORA_DEFAULT_EMBEDDING_MODEL_ID', '')

    print(f"  WEKNORA_BASE_URL: {base_url}")
    print(f"  WEKNORA_API_KEY: {'*' * 8 + api_key[-4:] if api_key and len(api_key) > 4 else 'Not Set'}")
    print(f"  EMBEDDING_MODEL_ID: {embedding_model_id}")

    if not api_key:
        print("\n  [ERROR] WEKNORA_API_KEY not configured!")
        return

    # ============================================================
    # Step 2: 获取知识库和文件
    # ============================================================
    print("\n[Step 2] Get Knowledge Base and Files")
    print("-"*70)

    # 获取知识库列表
    kb_result = weknora_repository.list_knowledge_bases()
    if not kb_result.get('success'):
        print(f"  [ERROR] Failed to get knowledge bases: {kb_result.get('error')}")
        return

    kb_list = kb_result.get('data', [])

    # 查找目标知识库
    selected_kb = None
    for kb in kb_list:
        if kb.get('name') == TARGET_KB_NAME:
            selected_kb = kb
            break

    if not selected_kb:
        print(f"  [ERROR] Knowledge base '{TARGET_KB_NAME}' not found!")
        print("  Available knowledge bases:")
        for kb in kb_list:
            print(f"    - {kb.get('name')}")
        return

    selected_kb_id = selected_kb.get('id')
    print(f"  Selected KB: {TARGET_KB_NAME} (ID: {selected_kb_id})")

    # 获取文件列表
    files_result = weknora_repository.list_knowledge(selected_kb_id)
    if not files_result.get('success'):
        print(f"  [ERROR] Failed to get files: {files_result.get('error')}")
        return

    files = files_result.get('data', {})
    if isinstance(files, dict):
        files_list = files.get('list', files.get('items', []))
    else:
        files_list = files if isinstance(files, list) else []

    # 查找目标文件
    selected_file = None
    for f in files_list:
        name = f.get('title') or f.get('name') or f.get('fileName') or ''
        if TARGET_FILE_NAME in name:
            selected_file = f
            break

    if not selected_file:
        print(f"  [ERROR] File '{TARGET_FILE_NAME}' not found!")
        return

    selected_file_id = selected_file.get('id')
    selected_file_name = selected_file.get('title') or selected_file.get('name') or 'Unknown'
    print(f"  Selected File: {selected_file_name} (ID: {selected_file_id})")

    # ============================================================
    # Step 3: 测试 search_chunks (文档片段检索)
    # ============================================================
    print("\n[Step 3] Test search_chunks (Document Chunk Search)")
    print("-"*70)
    print("  This method returns document chunks directly from vector search")
    print()

    for query in TEST_QUERIES:
        print(f"\n  Query: '{query}'")
        print("  " + "-"*50)

        result = weknora_repository.search_chunks(
            query_text=query,
            knowledge_ids=[selected_file_id],
            top_k=3,
        )

        if result.get('success'):
            data = result.get('data', {})
            chunks = data.get('list', data.get('chunks', data.get('items', [])))

            if isinstance(data, list):
                chunks = data

            print(f"    Found {len(chunks)} chunks")

            for i, chunk in enumerate(chunks[:3], 1):
                # 尝试获取内容
                content = chunk.get('content', chunk.get('text', chunk.get('chunk', '')))
                score = chunk.get('score', chunk.get('similarity', 'N/A'))

                if content:
                    preview = content[:150] + '...' if len(content) > 150 else content
                    print(f"    [{i}] Score: {score}")
                    print(f"        Content: {preview}")
                else:
                    print(f"    [{i}] Raw data: {chunk}")
        else:
            print(f"    [ERROR] {result.get('error')}")

    # ============================================================
    # Step 4: 测试 hybrid_search (混合检索)
    # ============================================================
    print("\n[Step 4] Test hybrid_search (Hybrid Search)")
    print("-"*70)
    print("  This method combines vector and keyword search")
    print()

    for query in TEST_QUERIES:
        print(f"\n  Query: '{query}'")
        print("  " + "-"*50)

        result = weknora_repository.hybrid_search(
            query_text=query,
            knowledge_ids=[selected_file_id],
            knowledge_base_ids=[selected_kb_id],
        )

        if result.get('success'):
            data = result.get('data', {})
            items = data.get('list', data.get('items', data.get('results', [])))

            if isinstance(data, list):
                items = data

            print(f"    Found {len(items)} results")

            for i, item in enumerate(items[:3], 1):
                # 尝试获取内容
                content = item.get('content', item.get('text', item.get('summary', '')))
                score = item.get('score', item.get('similarity', 'N/A'))
                title = item.get('title', item.get('name', 'N/A'))

                if content:
                    preview = content[:150] + '...' if len(content) > 150 else content
                    print(f"    [{i}] Title: {title}")
                    print(f"        Score: {score}")
                    print(f"        Content: {preview}")
                else:
                    print(f"    [{i}] Raw data: {item}")
        else:
            print(f"    [ERROR] {result.get('error')}")

    # ============================================================
    # Step 5: 对比分析
    # ============================================================
    print("\n[Step 5] Comparison Summary")
    print("-"*70)
    print("""
  | Method        | Description                    | Use Case                    |
  |---------------|--------------------------------|-----------------------------|
  | search_chunks | Returns document chunks        | Get original text fragments |
  | hybrid_search | Vector + Keyword combined      | Get aggregated results      |
  | agent_chat    | RAG with LLM generation        | Get AI-generated answers    |
    """)

    print("="*70)
    print("Test completed!")
    print("="*70)


if __name__ == '__main__':
    test_embedding_search()
