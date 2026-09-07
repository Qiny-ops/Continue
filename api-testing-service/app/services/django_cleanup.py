"""
Django 测试用户清理

从 engine.py 拆出的跨服务清理逻辑（原来混在 TestEngine 上帝类中）。
负责：识别时间戳格式的测试账号 → 调用 Django cleanup 端点销毁。
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# 测试用户时间戳命名模式：test_YYYYMMDD_HHMMSS_xxxx
_TEST_USER_PATTERN = r'^test_\d{8}_\d{6}_[a-z0-9]{12}$'


def extract_test_usernames(run_list: List[Dict[str, Any]]) -> List[str]:
    """从 run_list 中提取需要清理的时间戳格式测试用户名

    遍历 run_list 中含有"注册"接口的 request_body，匹配时间戳命名模式。
    """
    usernames = []

    for api_info in run_list:
        api_name = api_info.get("api_name", "")
        if "注册" not in api_name:
            continue

        request_body = api_info.get("request_body", {})
        if isinstance(request_body, dict):
            username = request_body.get("username", "")
            if re.match(_TEST_USER_PATTERN, username):
                usernames.append(username)

    return usernames


async def cleanup_test_user(base_url: str, username: Optional[str],
                           internal_api_key: str = "", auth_token: Optional[str] = None) -> bool:
    """清理单个测试用户（调用 Django /api/users/cleanup-test-user/ 端点）

    Args:
        base_url: Django 服务地址
        username: 待删除的用户名（非时间戳格式则跳过）
        internal_api_key: X-Internal-API-Key（服务间鉴权）
        auth_token: Bearer token（可选，附加认证）

    Returns:
        是否成功清理
    """
    if not username:
        return False

    if not re.match(_TEST_USER_PATTERN, username):
        logger.info(f"用户名 {username} 不是时间戳格式测试账号，跳过清理")
        return False

    try:
        import httpx
        url = f"{base_url}/api/users/cleanup-test-user/?username={username}"
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        if internal_api_key:
            headers["X-Internal-API-Key"] = internal_api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=headers)
            # 兼容 cleanup 端点返回空/非 JSON 响应（如 204、纯文本、5xx 报错页）
            try:
                result = response.json()
            except Exception:
                result = {}
            if result.get("code") == 200 or result.get("success"):
                logger.info(f"测试用户 {username} 清理成功")
                return True
            else:
                logger.warning(f"清理测试用户失败: {result.get('message', 'Unknown error')} (status={response.status_code})")
                return False

    except Exception as e:
        logger.error(f"清理测试用户异常: {e}")
        return False
