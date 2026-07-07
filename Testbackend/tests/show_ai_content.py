#!/usr/bin/env python3
"""
查看发送给AI模型的完整内容
"""
import asyncio
import json

# 模拟AI微服务内部的逻辑

# 测试方向对应的Prompt
TEST_DIRECTION_PROMPTS = {
    "功能点测试": """测试方向：功能点测试用例场景。请依据这些信息帮我生成功能测试用例。
注意：
1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。
2、你需要严格按照 json 格式生成，并且要能解析。""",
    "业务逻辑测试": """测试方向：业务逻辑测试用例场景。请依据这些信息帮我生成功能测试用例。
注意：
1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。
2、你需要严格按照 json 格式生成，并且要能解析。""",
    "其他测试": """测试方向：其他测试场景。请依据这些信息帮我生成功能测试用例。
注意：
1、测试场景一定要考虑合理，有些功能不需要考虑的测试场景就不要考虑。
2、你需要严格按照 json 格式生成，并且要能解析。""",
}

SYSTEM_PROMPT = "你的任务是帮我生成功能测试用例"


def show_ai_request():
    """展示发送给AI的完整内容"""

    # 输入参数
    module = "用户管理"
    func_point = "用户登录功能"
    related_detail = "支持账号密码和手机验证码两种登录方式，密码错误3次后锁定账号，锁定时间为30分钟"
    test_directions = ["功能点测试", "业务逻辑测试", "其他测试"]

    # 构建基础输入文本
    base_text = f"模块：{module}，功能点：{func_point}"
    if related_detail and related_detail != "无相关需求":
        base_text += f"\n关联需求：{related_detail}"
    else:
        base_text += "\n关联需求：无"

    print("=" * 80)
    print("发送给AI的内容")
    print("=" * 80)

    for i, direction in enumerate(test_directions, 1):
        prompt = TEST_DIRECTION_PROMPTS.get(direction, TEST_DIRECTION_PROMPTS["功能点测试"])
        input_text = f"{base_text}\n{prompt}"

        print(f"\n{'='*80}")
        print(f"【请求 {i}】测试方向: {direction}")
        print("=" * 80)

        print("\n【System Message】:")
        print("-" * 40)
        print(SYSTEM_PROMPT)

        print("\n【User Message】:")
        print("-" * 40)
        print(input_text)

        print("\n【完整请求格式】:")
        print("-" * 40)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": input_text}
        ]
        print(json.dumps(messages, ensure_ascii=False, indent=2))

    print("\n" + "=" * 80)
    print("请求统计")
    print("=" * 80)
    print(f"功能点数量: 1")
    print(f"测试方向数量: {len(test_directions)}")
    print(f"总请求数: {len(test_directions)} (每个功能点发送 {len(test_directions)} 次请求)")


def show_optimized_request():
    """展示优化后的请求方式"""

    print("\n\n")
    print("=" * 80)
    print("优化后的请求方式（一次请求处理所有测试方向）")
    print("=" * 80)

    module = "用户管理"
    func_point = "用户登录功能"
    related_detail = "支持账号密码和手机验证码两种登录方式，密码错误3次后锁定账号，锁定时间为30分钟"
    test_directions = ["功能点测试", "业务逻辑测试", "其他测试"]

    # 构建请求
    request = {
        "module": module,
        "func_point": func_point,
        "related_detail": related_detail,
        "test_directions": test_directions
    }

    print("\n【请求体】:")
    print(json.dumps(request, ensure_ascii=False, indent=2))

    print("\n【AI微服务内部处理】:")
    print("-" * 40)
    print("收到请求后，AI微服务会:")
    print("1. 为每个测试方向构建独立的Prompt")
    print("2. 并行调用模型API（3个请求同时发送）")
    print("3. 收集所有结果并合并")
    print("4. 返回完整的用例列表")

    print("\n【优势】:")
    print("-" * 40)
    print("- 网络往返: 1次（而不是3次）")
    print("- Django后端只需发送1次请求")
    print("- AI微服务内部并行处理，速度更快")
    print("- 返回结果统一，便于去重")


if __name__ == "__main__":
    show_ai_request()
    show_optimized_request()
