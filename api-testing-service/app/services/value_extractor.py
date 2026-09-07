"""
执行结果变量提取

从 engine.py 拆出的 JSONPath 风格路径提取逻辑。
原来混在 TestEngine 上帝类中，但实际无需任何实例状态——纯函数。
"""

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_value_from_response(result: Any, path: str) -> Optional[Any]:
    """根据 JSONPath 风格路径从执行结果中提取值

    支持格式：
        $.response.body.data.id
        response.headers.Authorization
        run_list[0].response.body.token
        body.data[0].name
    不依赖 TestEngine 实例状态，可独立复用。
    """
    if not path or not result:
        return None

    try:
        if path.startswith("$."):
            path = path[2:]

        # 处理 run_list[N].xxx 前缀
        match = re.match(r'run_list\[\d+\]\.(.*)', path)
        if match:
            path = match.group(1)

        if path.startswith("response."):
            path = path[len("response."):]

        # 确定提取的起始数据源
        data = {}
        if hasattr(result, 'response') and result.response:
            data = result.response
        elif hasattr(result, 'status_code'):
            data = result

        parts = path.split(".")
        current = data
        for part in parts:
            if current is None:
                return None

            # 支持 array[index] 语法
            array_match = re.match(r'(\w+)\[(\d+)\]', part)
            if array_match:
                key = array_match.group(1)
                idx = int(array_match.group(2))
                if isinstance(current, dict):
                    current = current.get(key)
                else:
                    return None
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None

        return current

    except Exception as e:
        logger.error(f"提取变量失败: path={path}, error={e}")
        return None
