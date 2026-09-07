"""
需求提取服务

负责从知识库提取需求、JSON解析等。
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from apps.knowledge.repositories.weknora_repository import weknora_repository
from apps.knowledge.services.agent_service import AgentService
from apps.core.utils.json_parser import JSONParser

logger = logging.getLogger(__name__)


class RequirementService:
    """需求提取服务"""

    # 默认的需求提炼 prompt
    DEFAULT_REQUIREMENT_QUERY = """请仔细阅读以下需求文档内容，提取出所有的功能点。

要求:
1. 功能点必须覆盖完整，功能点是对需求功能的总结
2. 要尊重事实不要猜测
3. 必须严格按照以下JSON数组格式返回，不要添加任何其他内容:
[{"模块":"模块名称","功能点":"具体功能描述"}]
4. 功能点必须完整，不能遗漏任何功能
5. 模块名称要简洁明确，必须拆分很细
6. 功能点描述要具体，包含交互逻辑和校验规则
7. 注意：JSON中的字符串必须使用双引号，键名"模块"和"功能点"必须带引号
8. 不要使用markdown代码块格式，直接返回纯JSON数组
9. 不要添加任何解释说明、注释或额外文字，只返回JSON数组本身

示例输出格式:
[{"模块":"用户管理","功能点":"用户登录功能，支持账号密码和手机验证码两种方式"},{"模块":"用户管理","功能点":"用户注册功能，需要填写手机号、密码、昵称"}]
"""

    def __init__(self, repository=None):
        self.repository = repository or weknora_repository

    def extract(
        self,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_id: str = 'builtin-smart-reasoning',
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs
    ) -> Tuple[List[dict], str]:
        """
        提取需求

        Args:
            knowledge_base_ids: 知识库ID列表
            knowledge_ids: 文件ID列表
            query: 自定义查询内容
            session_id: 会话ID（可选）
            agent_id: Agent ID
            temperature: 生成温度
            max_tokens: 最大输出token

        Returns:
            (requirements列表, session_id)
        """
        # 创建或使用已有会话
        if not session_id:
            create_result = self.repository.create_session(knowledge_base_ids[0])
            if not create_result.get('success'):
                logger.error(f"创建会话失败: {create_result.get('error')}")
                return [], None
            session_id = create_result['data']['id']
            logger.info(f"自动创建会话: session_id={session_id}")

        # 构建mentioned_items
        mentioned_items = self._build_mentioned_items(knowledge_base_ids, knowledge_ids)

        # 调用Agent提取需求
        query_text = query or self.DEFAULT_REQUIREMENT_QUERY
        result = self.repository.agent_chat(
            session_id=session_id,
            query=query_text,
            knowledge_base_ids=knowledge_base_ids,
            knowledge_ids=knowledge_ids,
            mentioned_items=mentioned_items,
            agent_id=agent_id,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not result.get('success'):
            logger.error(f"需求提取失败: {result.get('error')}")
            return [], session_id

        content = result['data']['content']

        # 解析JSON
        success, requirements, error = JSONParser.try_parse(content)

        if not success:
            logger.warning(f"JSON解析失败: {error}")
            return [], session_id

        logger.info(f"需求提取成功: {len(requirements)} 个功能点")
        return requirements, session_id

    def _build_mentioned_items(
        self,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """构建mentioned_items数组（委托给 AgentService 避免重复）"""
        return AgentService.build_mentioned_items(
            knowledge_base_ids=knowledge_base_ids,
            knowledge_ids=knowledge_ids,
        )