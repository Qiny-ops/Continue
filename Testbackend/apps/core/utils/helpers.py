"""
辅助函数工具

提供常用的辅助函数。
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Any, Dict


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


def generate_short_uuid() -> str:
    """生成短UUID（8位）"""
    return uuid.uuid4().hex[:8]


def hash_password(password: str, salt: str = '') -> str:
    """对密码进行哈希"""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def generate_file_hash(file_content: bytes) -> str:
    """生成文件哈希值"""
    return hashlib.md5(file_content).hexdigest()


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filename)[1].lower()


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = get_file_extension(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    short_uuid = generate_short_uuid()
    return f'{timestamp}_{short_uuid}{ext}'


def format_datetime(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """格式化日期时间"""
    if not dt:
        return ''
    return dt.strftime(fmt)


def format_date(dt: datetime, fmt: str = '%Y-%m-%d') -> str:
    """格式化日期"""
    if not dt:
        return ''
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """解析日期时间字符串"""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, fmt)
    except ValueError:
        return None


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断字符串"""
    if not s or len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def remove_none_values(data: Dict) -> Dict:
    """移除字典中值为None的键"""
    return {k: v for k, v in data.items() if v is not None}


def remove_empty_values(data: Dict) -> Dict:
    """移除字典中空值的键"""
    return {k: v for k, v in data.items() if v not in (None, '', [], {})}


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分割成指定大小的块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(lst: List[List]) -> List:
    """展平嵌套列表"""
    return [item for sublist in lst for item in sublist]


def get_nested_value(data: Dict, keys: str, default: Any = None) -> Any:
    """获取嵌套字典中的值"""
    keys = keys.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = '') -> str:
    """安全转换为字符串"""
    if value is None:
        return default
    return str(value)


def build_tree(items: List[Dict], id_field: str = 'id', parent_field: str = 'parent_id', children_field: str = 'children') -> List[Dict]:
    """构建树形结构"""
    item_map = {item[id_field]: item for item in items}
    roots = []

    for item in items:
        parent_id = item.get(parent_field)
        if parent_id and parent_id in item_map:
            parent = item_map[parent_id]
            if children_field not in parent:
                parent[children_field] = []
            parent[children_field].append(item)
        else:
            roots.append(item)

    return roots
