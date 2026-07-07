"""
向量检索测试脚本

用于测试 WeKnora 知识库的向量检索效果。
"""
import os
import sys

# 设置 Django 环境 - 需要在导入 django 之前设置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')

import django
django.setup()

import requests

# WeKnora 配置
BASE_URL = 'http://127.0.0.1:3000/api/v1'
API_KEY = 'sk-yai8wFpY7M8LH4Ke2po4_JoskFAit3658aFgiG0AevS6rEm6'

# 测试配置
KNOWLEDGE_BASE_ID = 'f57da749-d2c1-4c58-8e4c-29334606fc16'

# 测试查询列表
TEST_QUERIES = [
    '支持企业邮箱注册，注册后需由系统管理员审核通过方可登录，审核不通过需反馈拒绝原因',
    '账号密码登录',
    '角色权限管理',
    '测试用例编写',
    '项目成员管理',
]


def search(query: str, knowledge_base_id: str, top_k: int = 5) -> dict:
    """执行向量检索"""
    response = requests.post(
        f'{BASE_URL}/knowledge-search',
        headers={'X-API-Key': API_KEY, 'Content-Type': 'application/json'},
        json={
            'query': query,
            'knowledge_base_ids': [knowledge_base_id],
            'top_k': top_k,
        },
        timeout=30,
    )
    return response.json()


def check_keywords(content: str, query: str) -> bool:
    """检查匹配内容是否包含查询中的关键词"""
    # 提取查询中的关键词
    keywords = []
    for word in ['企业邮箱', '注册', '登录', '审核', '权限', '角色', '用例', '项目', '成员']:
        if word in query:
            keywords.append(word)

    # 检查内容是否包含关键词
    for kw in keywords:
        if kw in content:
            return True
    return False


def main():
    print('=' * 70)
    print('向量检索测试')
    print('=' * 70)
    print(f'知识库ID: {KNOWLEDGE_BASE_ID}')
    print()

    for query in TEST_QUERIES:
        print(f'查询: {query}')
        print('-' * 70)

        result = search(query, KNOWLEDGE_BASE_ID)

        if result.get('success'):
            data = result.get('data', [])
            # 过滤掉摘要
            filtered = [item for item in data if item.get('chunk_type') != 'summary']

            print(f'过滤后结果: {len(filtered)} 条')

            matched_count = 0
            for i, item in enumerate(filtered[:3]):
                matched = item.get('matched_content', '')
                score = item.get('score', 0)
                chunk_index = item.get('chunk_index')
                has_keyword = check_keywords(matched, query)

                if has_keyword:
                    matched_count += 1

                print(f'  [{i}] chunk_index={chunk_index}, score={score:.3f}, 匹配关键词={has_keyword}')
                if matched:
                    preview = matched[:100] + '...' if len(matched) > 100 else matched
                    print(f'      内容: {preview}')

            print(f'  匹配率: {matched_count}/{len(filtered[:3])}')
        else:
            print(f'  错误: {result.get("error")}')

        print()

    print('=' * 70)
    print('测试完成')


if __name__ == '__main__':
    main()