"""
AI TestCase Generator Client - 向后兼容模块

此模块已移动到 clients/ai_client.py，此处保留导入以保持向后兼容。
新代码请使用: from apps.testcase.clients import AITestCaseClientSync
"""

# 向后兼容：从新位置导入
from apps.testcase.clients.ai_client import (
    AITestCaseClient,
    AITestCaseClientSync,
    AIGenerationResult,
    AIServiceError,
    ModelNotReadyError,
)

__all__ = [
    'AITestCaseClient',
    'AITestCaseClientSync',
    'AIGenerationResult',
    'AIServiceError',
    'ModelNotReadyError',
]
