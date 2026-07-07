"""
Agent 服务

提供 Agent 对话和需求提炼的业务逻辑。
"""

import logging
from typing import Dict, Any, List, Optional
from apps.knowledge.repositories import weknora_repository

logger = logging.getLogger(__name__)


class AgentService:
    """Agent 服务"""

    # 默认的需求提炼 prompt（保留用于向后兼容）
    DEFAULT_REQUIREMENT_QUERY = """请仔细阅读以下需求文档内容，提取出所有的功能点。

要求:
1. 功能点必须覆盖完整，功能点是对需求功能的总结
2. 要尊重事实不要猜测
3. 必须严格按照 JSON 数组格式返回:[{"模块":"模块名称","功能点":"具体功能描述"}]
4. 功能点必须完整，不能遗漏任何功能
5. 模块名称要简洁明确，必须拆分很细
6. 功能点描述要具体，包含交互逻辑和校验规则
7. 严禁添加任何解释说明，只能返回纯 JSON 数组。
"""

    @staticmethod
    def create_session(knowledge_base_id: str) -> Dict[str, Any]:
        """
        创建 Agent 会话

        Args:
            knowledge_base_id: 知识库 ID

        Returns:
            {'success': bool, 'data': {'session_id': str}} 或 {'success': False, 'error': str}
        """
        try:
            if not knowledge_base_id:
                return {'success': False, 'error': '知识库 ID 不能为空'}

            result = weknora_repository.create_session(knowledge_base_id)
            if result.get('success'):
                session_id = result.get('data', {}).get('id')
                logger.info(f"创建会话成功: session_id={session_id}, kb_id={knowledge_base_id}")
                return {'success': True, 'data': {'session_id': session_id}}
            return result
        except Exception as e:
            logger.error(f'创建会话失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def build_mentioned_items(
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        kb_name_map: Optional[Dict[str, str]] = None,
        file_name_map: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        构造 mentioned_items 数组

        Args:
            knowledge_base_ids: 知识库 ID 列表
            knowledge_ids: 文件 ID 列表
            kb_name_map: 知识库名称映射 {kb_id: name}
            file_name_map: 文件名称映射 {file_id: name}

        Returns:
            mentioned_items 列表
        """
        items = []

        for kb_id in knowledge_base_ids:
            name = kb_name_map.get(kb_id, f"KB-{kb_id[-8:]}") if kb_name_map else f"KB-{kb_id[-8:]}"
            items.append({
                'id': kb_id,
                'name': name,
                'type': 'kb',
                'kb_type': 'document'
            })

        for k_id in knowledge_ids:
            name = file_name_map.get(k_id, f"File-{k_id[-8:]}") if file_name_map else f"File-{k_id[-8:]}"
            items.append({
                'id': k_id,
                'name': name,
                'type': 'file'
            })

        return items

    @staticmethod
    def agent_chat(
        session_id: str,
        query: str,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        agent_id: str = 'builtin-smart-reasoning',
        web_search_enabled: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        kb_name_map: Optional[Dict[str, str]] = None,
        file_name_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Agent 对话

        Args:
            session_id: 会话 ID
            query: 查询内容
            knowledge_base_ids: 知识库 ID 列表
            knowledge_ids: 文件 ID 列表
            agent_id: Agent ID
            web_search_enabled: 是否启用网络搜索
            temperature: 生成温度
            max_tokens: 最大输出 token
            kb_name_map: 知识库名称映射
            file_name_map: 文件名称映射

        Returns:
            {'success': bool, 'data': {'content': str}} 或 {'success': False, 'error': str}
        """
        try:
            if not session_id:
                return {'success': False, 'error': '会话 ID 不能为空'}
            if not query:
                return {'success': False, 'error': '查询内容不能为空'}

            mentioned_items = AgentService.build_mentioned_items(
                knowledge_base_ids, knowledge_ids, kb_name_map, file_name_map
            )

            logger.info(f"Agent chat: session_id={session_id}, kb_ids={knowledge_base_ids}, file_ids={knowledge_ids}")

            return weknora_repository.agent_chat(
                session_id=session_id,
                query=query,
                knowledge_base_ids=knowledge_base_ids,
                knowledge_ids=knowledge_ids,
                mentioned_items=mentioned_items,
                agent_id=agent_id,
                web_search_enabled=web_search_enabled,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.error(f'Agent 对话失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def extract_requirements(
        query: str,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        session_id: Optional[str] = None,
        agent_id: str = 'builtin-smart-reasoning',
        web_search_enabled: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        kb_name_map: Optional[Dict[str, str]] = None,
        file_name_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        需求提炼（一站式接口）

        如果未提供 session_id，会自动创建会话。

        Args:
            query: 提问内容
            knowledge_base_ids: 知识库 ID 列表
            knowledge_ids: 文件 ID 列表
            session_id: 会话 ID（可选）
            agent_id: Agent ID
            web_search_enabled: 是否启用网络搜索
            temperature: 生成温度
            max_tokens: 最大输出 token
            kb_name_map: 知识库名称映射
            file_name_map: 文件名称映射

        Returns:
            {'success': bool, 'data': {'content': str, 'session_id': str}} 或 {'success': False, 'error': str}
        """
        try:
            if not knowledge_base_ids:
                return {'success': False, 'error': '至少需要提供一个知识库 ID'}

            # 如果没有会话 ID，自动创建
            if not session_id:
                create_result = AgentService.create_session(knowledge_base_ids[0])
                if not create_result.get('success'):
                    return create_result
                session_id = create_result['data']['session_id']
                logger.info(f"自动创建会话: session_id={session_id}")

            # 调用 Agent 对话
            result = AgentService.agent_chat(
                session_id=session_id,
                query=query,
                knowledge_base_ids=knowledge_base_ids,
                knowledge_ids=knowledge_ids,
                agent_id=agent_id,
                web_search_enabled=web_search_enabled,
                temperature=temperature,
                max_tokens=max_tokens,
                kb_name_map=kb_name_map,
                file_name_map=file_name_map,
            )

            if result.get('success'):
                result['data']['session_id'] = session_id

            return result
        except Exception as e:
            logger.error(f'需求提炼失败: {str(e)}', exc_info=True)
            return {'success': False, 'error': str(e)}
