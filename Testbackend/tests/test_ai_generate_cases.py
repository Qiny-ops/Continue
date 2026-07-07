#!/usr/bin/env python3
"""
测试AI微服务的新接口：一次请求处理多个测试方向
"""
import httpx
import json
import asyncio

# AI微服务地址
AI_SERVICE_URL = "http://localhost:8001"


async def test_generate_test_cases():
    """测试测试用例生成接口"""

    # 构建请求
    payload = {
        "module": "用户管理",
        "func_point": "用户登录功能",
        "related_detail": "支持账号密码和手机验证码两种登录方式，密码错误3次后锁定账号",
        "test_directions": ["功能点测试", "业务逻辑测试", "其他测试"]
    }

    print("=" * 60)
    print("测试AI微服务新接口: /api/v1/testcase/generate")
    print("=" * 60)
    print(f"\n请求参数:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            print("\n发送请求中...")
            response = await client.post(
                f"{AI_SERVICE_URL}/api/v1/testcase/generate",
                json=payload
            )

            print(f"\n响应状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n响应结果:")
                print(json.dumps(data, ensure_ascii=False, indent=2))

                if data.get("success"):
                    cases = data.get("cases", [])
                    print(f"\n成功生成 {len(cases)} 个测试用例:")
                    for i, case in enumerate(cases, 1):
                        print(f"\n--- 用例 {i} ({case.get('test_type', '未知')}) ---")
                        print(f"标题: {case.get('title')}")
                        print(f"优先级: {case.get('priority')}")
                        print(f"步骤: {case.get('steps', '')[:100]}...")
                else:
                    print(f"\n生成失败: {data.get('error')}")
            else:
                print(f"\n请求失败: {response.text}")

        except httpx.ConnectError:
            print(f"\n无法连接AI微服务: {AI_SERVICE_URL}")
            print("请确保AI微服务已启动: cd ai-generator-service && python -m uvicorn app.main:app --port 8001")
        except Exception as e:
            print(f"\n请求异常: {e}")


async def test_health():
    """测试健康检查接口"""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{AI_SERVICE_URL}/api/v1/health")
            print(f"健康检查: {response.status_code} - {response.json()}")
            return response.status_code == 200
        except:
            print(f"健康检查失败，AI微服务未运行")
            return False


async def main():
    print("\n" + "=" * 60)
    print("AI微服务测试")
    print("=" * 60)

    # 先检查服务是否运行
    print("\n1. 检查AI微服务状态...")
    is_healthy = await test_health()

    if not is_healthy:
        print("\n请先启动AI微服务:")
        print("  cd E:\\Continue\\ai-generator-service")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return

    print("\n2. 测试测试用例生成接口...")
    await test_generate_test_cases()


if __name__ == "__main__":
    asyncio.run(main())
