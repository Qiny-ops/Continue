#!/usr/bin/env python3
"""
测试AI微服务内部并行处理测试方向的逻辑
不实际调用模型API，只测试流程
"""
import asyncio
import httpx
import json

AI_SERVICE_URL = "http://localhost:8001"


async def test_health():
    """测试健康检查"""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{AI_SERVICE_URL}/api/v1/health")
        print(f"健康检查: {response.status_code} - {response.json()}")
        return response.status_code == 200


async def test_infer_endpoint():
    """测试原有的推理接口（验证模型API是否可用）"""
    payload = {
        "messages": [
            {"role": "user", "content": "你好"}
        ]
    }

    print("\n" + "=" * 60)
    print("测试原有推理接口: /api/v1/infer")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.post(f"{AI_SERVICE_URL}/api/v1/infer", json=payload)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"成功: {data.get('success')}")
                if data.get('error'):
                    print(f"错误: {data.get('error')}")
                if data.get('result'):
                    print(f"结果预览: {str(data.get('result'))[:200]}")
            else:
                print(f"响应: {response.text[:500]}")
        except Exception as e:
            print(f"请求异常: {e}")


async def test_testcase_generate_mock():
    """
    测试测试用例生成接口的流程逻辑
    使用单个测试方向，减少调用次数
    """
    payload = {
        "module": "用户管理",
        "func_point": "用户登录功能",
        "related_detail": "支持账号密码登录",
        "test_directions": ["功能点测试"]  # 只测试一个方向
    }

    print("\n" + "=" * 60)
    print("测试用例生成接口: /api/v1/testcase/generate")
    print("=" * 60)
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            print("\n发送请求...")
            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/testcase/generate",
                json=payload
            )
            print(f"状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n响应结果:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"响应: {response.text}")

        except httpx.TimeoutException:
            print("请求超时（模型API响应慢）")
        except Exception as e:
            print(f"请求异常: {e}")


async def test_flow_without_model():
    """
    测试流程逻辑（不依赖模型API）
    验证：
    1. 请求参数解析
    2. 测试方向Prompt构建
    3. 并行任务创建
    """
    print("\n" + "=" * 60)
    print("测试流程逻辑（模拟）")
    print("=" * 60)

    # 模拟AI微服务内部的逻辑
    test_directions = ["功能点测试", "业务逻辑测试", "其他测试"]

    TEST_DIRECTION_PROMPTS = {
        "功能点测试": "测试方向：功能点测试用例场景...",
        "业务逻辑测试": "测试方向：业务逻辑测试用例场景...",
        "其他测试": "测试方向：其他测试场景...",
    }

    module = "用户管理"
    func_point = "用户登录功能"
    related_detail = "支持账号密码登录"

    # 构建基础输入文本
    base_text = f"模块：{module}，功能点：{func_point}"
    if related_detail and related_detail != "无相关需求":
        base_text += f"\n关联需求：{related_detail}"
    else:
        base_text += "\n关联需求：无"

    print(f"\n基础输入文本:\n{base_text}")

    # 模拟并行处理
    print(f"\n并行处理 {len(test_directions)} 个测试方向:")

    async def mock_generate(direction: str, delay: float = 0.5):
        """模拟生成过程"""
        prompt = TEST_DIRECTION_PROMPTS.get(direction, "未知方向")
        input_text = f"{base_text}\n{prompt}"

        print(f"  [{direction}] 开始处理...")
        await asyncio.sleep(delay)  # 模拟API调用延迟

        # 模拟返回结果
        mock_cases = [
            {
                "title": f"[{direction}] 测试{func_point} - 正常场景",
                "steps": "1. 步骤一\n2. 步骤二",
                "expected_result": "预期结果",
                "priority": "p2",
                "test_type": direction
            }
        ]

        print(f"  [{direction}] 完成，生成 {len(mock_cases)} 个用例")
        return direction, mock_cases, None

    # 并行执行
    start_time = asyncio.get_event_loop().time()
    tasks = [mock_generate(d) for d in test_directions]
    results = await asyncio.gather(*tasks)
    elapsed = asyncio.get_event_loop().time() - start_time

    # 收集结果
    all_cases = []
    for direction, cases, error in results:
        if cases:
            all_cases.extend(cases)

    print(f"\n结果汇总:")
    print(f"  总用例数: {len(all_cases)}")
    print(f"  总耗时: {elapsed:.2f}秒（并行执行）")

    # 模拟去重
    print(f"\n模拟向量去重:")
    print(f"  原始用例数: {len(all_cases)}")
    # 假设有1个重复
    deduplicated_cases = all_cases[:2]  # 模拟去重后保留2个
    print(f"  去重后用例数: {len(deduplicated_cases)}")

    print("\n用例列表:")
    for i, case in enumerate(deduplicated_cases, 1):
        print(f"  {i}. [{case['test_type']}] {case['title']}")


async def main():
    print("=" * 60)
    print("AI微服务流程测试")
    print("=" * 60)

    # 1. 检查服务状态
    print("\n1. 检查AI微服务状态...")
    is_healthy = await test_health()

    if not is_healthy:
        print("\nAI微服务未运行，请先启动:")
        print("  cd E:\\Continue\\ai-generator-service")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return

    # 2. 测试流程逻辑（不依赖模型）
    await test_flow_without_model()

    # 3. 测试原有推理接口（验证模型API）
    print("\n2. 测试模型API连接...")
    await test_infer_endpoint()

    # 4. 如果模型API可用，测试完整流程
    print("\n3. 测试完整流程（需要模型API）...")
    await test_testcase_generate_mock()


if __name__ == "__main__":
    asyncio.run(main())
