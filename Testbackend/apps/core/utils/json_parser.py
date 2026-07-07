"""
JSON解析工具

支持多种容错机制，用于解析AI返回的JSON内容。
"""
import json
import re
import ast
import logging
from typing import Tuple, Any, Optional

logger = logging.getLogger(__name__)


class JSONParser:
    """
    JSON解析器

    支持多种容错机制：
    1. 直接解析
    2. 清理markdown代码块后解析
    3. 替换中文标点后解析
    4. 修复常见JSON错误后解析
    5. 使用ast.literal_eval解析
    """

    @staticmethod
    def try_parse(text: str) -> Tuple[bool, Any, Optional[str]]:
        """
        尝试解析JSON

        Args:
            text: 待解析的文本

        Returns:
            (成功标志, 解析结果或原始文本, 错误信息)
        """
        if not text:
            return False, text, "输入文本为空"

        # 预处理
        processed_text = JSONParser._preprocess(text)

        # 尝试直接解析
        try:
            result = json.loads(processed_text)
            return True, result, None
        except json.JSONDecodeError as e:
            first_error = str(e)

        # 尝试替换中文标点
        try:
            text2 = processed_text.replace('，', ',').replace('：', ':')
            text2 = re.sub(r':\\"', ':"', text2)
            text2 = re.sub(r'\\"', '"', text2)
            result = json.loads(text2)
            return True, result, None
        except Exception:
            pass

        # 尝试修复常见的JSON错误
        try:
            text3 = JSONParser._fix_json_errors(processed_text)
            result = json.loads(text3)
            return True, result, None
        except Exception:
            pass

        # 尝试提取并解析JSON对象数组
        try:
            # 查找所有 {...} 模式并组合成数组
            objects = re.findall(r'\{[^{}]*\}', processed_text, re.DOTALL)
            if objects:
                # 尝试解析每个对象
                parsed_objects = []
                for obj_text in objects:
                    try:
                        obj = json.loads(obj_text)
                        parsed_objects.append(obj)
                    except:
                        # 尝试修复单个对象
                        fixed_obj = JSONParser._fix_json_errors(obj_text)
                        try:
                            obj = json.loads(fixed_obj)
                            parsed_objects.append(obj)
                        except:
                            continue
                if parsed_objects:
                    return True, parsed_objects, None
        except Exception:
            pass

        # 尝试使用ast.literal_eval
        try:
            text4 = processed_text.replace('"', "'")
            result = ast.literal_eval(text4)
            return True, result, None
        except Exception:
            pass

        logger.warning(f"JSON解析失败: {first_error}, 原始文本前200字符: {processed_text[:200]}")
        return False, processed_text, f"JSON解析失败: {first_error}"

    @staticmethod
    def _fix_json_errors(text: str) -> str:
        """
        修复常见的JSON格式错误

        - 修复缺少引号的键名
        - 修复多余的逗号
        - 修复缺少的逗号
        - 修复转义字符
        """
        # 移除末尾多余的逗号（在 ] 或 } 之前）
        text = re.sub(r',\s*([}\]])', r'\1', text)

        # 修复缺少逗号的情况（两个对象之间）
        text = re.sub(r'\}\s*\{', r'},\n{', text)

        # 修复键名缺少引号的情况
        # 匹配类似 {key: 或 ,key: 的模式
        text = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', text)

        # 修复中文引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")

        # 修复错误的转义
        text = re.sub(r'\\([^"\\nrt])', r'\1', text)

        return text

    @staticmethod
    def try_parse_array(text: str) -> Tuple[bool, list, Optional[str]]:
        """
        尝试解析JSON数组

        Args:
            text: 待解析的文本

        Returns:
            (成功标志, 解析结果列表或空列表, 错误信息)
        """
        success, result, error = JSONParser.try_parse(text)

        if not success:
            return False, [], error

        if isinstance(result, list):
            return True, result, None

        if isinstance(result, dict):
            return True, [result], None

        return False, [], "解析结果不是数组或对象"

    @staticmethod
    def _preprocess(text: str) -> str:
        """
        预处理文本

        - 处理thinking标签
        - 清理markdown代码块
        - 提取JSON数组
        """
        text = text.strip()

        # 处理 <thought> 标签
        think_match = re.search(r"</thought>\s*(.*?)$", text, re.DOTALL)
        if think_match:
            text = think_match.group(1).strip()

        # 处理  标签
        think_match = re.search(r" \s*(.*?)$", text, re.DOTALL)
        if think_match:
            text = think_match.group(1).strip()

        # 处理 <thinking> 标签
        think_match = re.search(r"</thinking>\s*(.*?)$", text, re.DOTALL)
        if think_match:
            text = think_match.group(1).strip()

        # 清理markdown代码块
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 提取JSON数组
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)

        return text

    @staticmethod
    def safe_get(data: dict, *keys, default=None):
        """
        安全获取嵌套字典的值

        Args:
            data: 字典数据
            keys: 键路径
            default: 默认值

        Returns:
            找到的值或默认值
        """
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        return data
