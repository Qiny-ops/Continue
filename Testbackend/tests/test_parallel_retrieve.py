"""
测试并行检索 vs 串行检索性能对比
"""
import os
import sys
import django
import time

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Testbackend.settings')
sys.path.insert(0, 'E:/Continue/Testbackend')
django.setup()

import logging
from unittest.mock import Mock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def mock_agent_chat_delay(delay=0.5):
    """创建带延迟的Mock agent_chat"""
    def agent_chat(**kwargs):
        time.sleep(delay)  # 模拟网络延迟
        query = kwargs.get('query', '')
        if '用户名密码登录验证' in query:
            return {'success': True, 'data': {'content': '用户输入用户名和密码，点击登录按钮，系统验证用户名密码是否正确。'}}
        elif '验证码登录' in query:
            return {'success': True, 'data': {'content': '用户输入手机号，点击获取验证码，输入验证码后登录。'}}
        elif '新增用户' in query:
            return {'success': True, 'data': {'content': '管理员点击新增用户按钮，填写用户信息。'}}
        elif '编辑用户' in query:
            return {'success': True, 'data': {'content': '管理员选择用户，编辑用户信息。'}}
        elif '删除用户' in query:
            return {'success': True, 'data': {'content': '管理员选择用户，确认删除。'}}
        else:
            return {'success': True, 'data': {'content': '无相关需求'}}
    return agent_chat


def test_serial_vs_parallel():
    """测试串行 vs 并行性能"""
    from apps.knowledge.services.requirement_service import RequirementService

    print("\n" + "="*70)
    print("Serial vs Parallel Retrieval Performance Test")
    print("="*70)

    # 测试数据
    requirements = [
        {'模块': '用户登录', '功能点': '用户名密码登录验证'},
        {'模块': '用户登录', '功能点': '验证码登录'},
        {'模块': '用户管理', '功能点': '新增用户'},
        {'模块': '用户管理', '功能点': '编辑用户'},
        {'模块': '用户管理', '功能点': '删除用户'},
    ]

    print(f"\nTest Data: {len(requirements)} requirements")
    print(f"Simulated network delay: 0.5s per request")
    print("-"*70)

    # 测试串行模式
    print("\n[1] Serial Mode Test")
    mock_repository = Mock()
    mock_repository.agent_chat.side_effect = mock_agent_chat_delay(0.5)

    service = RequirementService(repository=mock_repository)

    start_time = time.time()
    results_serial = service.retrieve_related(
        requirements=requirements,
        knowledge_base_ids=['kb-test'],
        knowledge_ids=['file-test'],
        session_id='test-session',
        parallel=False,
    )
    serial_time = time.time() - start_time

    print(f"  Time: {serial_time:.2f}s")
    print(f"  Results: {len(results_serial)} items")

    # 测试并行模式（不同并发数）
    for max_workers in [2, 3, 5, 10]:
        print(f"\n[2] Parallel Mode Test (max_workers={max_workers})")
        mock_repository = Mock()
        mock_repository.agent_chat.side_effect = mock_agent_chat_delay(0.5)

        service = RequirementService(repository=mock_repository)

        start_time = time.time()
        results_parallel = service.retrieve_related(
            requirements=requirements,
            knowledge_base_ids=['kb-test'],
            knowledge_ids=['file-test'],
            session_id='test-session',
            parallel=True,
            max_workers=max_workers,
        )
        parallel_time = time.time() - start_time

        speedup = (serial_time - parallel_time) / serial_time * 100

        print(f"  Time: {parallel_time:.2f}s")
        print(f"  Results: {len(results_parallel)} items")
        print(f"  Speedup: {speedup:.1f}% faster than serial")

    # 结果汇总
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print(f"  Requirements count: {len(requirements)}")
    print(f"  Serial time:        {serial_time:.2f}s (baseline)")
    print(f"  Expected parallel:   ~0.5s (with enough workers)")
    print(f"  Time saved:         ~{(serial_time - 0.5):.2f}s ({(serial_time - 0.5)/serial_time*100:.0f}%)")

    # 验证结果一致性
    print("\n" + "-"*70)
    print("Verify Results Consistency")
    print("-"*70)
    for i, (serial_item, parallel_item) in enumerate(zip(results_serial, results_parallel)):
        match = serial_item['module'] == parallel_item['module'] and \
                serial_item['func_point'] == parallel_item['func_point']
        status = "[OK]" if match else "[FAIL]"
        print(f"  {status} Item {i+1}: {serial_item['module']} - {serial_item['func_point']}")

    print("\n" + "="*70)
    print("Test completed!")
    print("="*70)


if __name__ == '__main__':
    test_serial_vs_parallel()
