"""
WeKnora 知识库服务数据访问层

封装与 WeKnora 外部服务的所有 API 通信。
"""

import logging
import json
import requests
from typing import Optional, Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class WeKnoraRepository:
    """
    WeKnora 知识库 API 数据访问层

    负责与 WeKnora 后端服务进行通信，不包含业务逻辑。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url or getattr(settings, 'WEKNORA_BASE_URL', 'http://localhost:3000/api/v1')
        self.api_key = api_key or getattr(settings, 'WEKNORA_API_KEY', '')
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        raw_response: bool = False
    ) -> Dict[str, Any]:
        """发送请求到 WeKnora 服务"""
        url = f"{self.base_url}{endpoint}"

        headers = {}
        if not files:
            headers['Content-Type'] = 'application/json'
        headers['X-API-Key'] = self.api_key

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data and not files else None,
                data=data if files else None,
                files=files,
                headers=headers,
                timeout=self.timeout
            )

            if raw_response:
                return response

            # ---- 解析响应（兼容非 JSON / 异常结构）----
            try:
                result = response.json()
            except (ValueError, json.JSONDecodeError):
                # 上游返回了非 JSON 内容（网关错误页、HTML 等）
                body = (response.text or '')[:200]
                if response.status_code in (401, 403):
                    return {
                        'success': False,
                        'error': 'WeKnora 认证失败：API Key 无效或未配置',
                        'code': 'AUTH_ERROR',
                        'http_status': 502,
                    }
                if response.status_code >= 500:
                    return {
                        'success': False,
                        'error': f'WeKnora 服务异常（HTTP {response.status_code}）',
                        'code': 'UPSTREAM_ERROR',
                        'http_status': 502,
                    }
                return {
                    'success': False,
                    'error': body or f'未知错误（HTTP {response.status_code}）',
                    'code': 'UNKNOWN_ERROR',
                    'http_status': 500,
                }

            # 防御：个别实现可能返回非 dict（如字符串/列表）
            if not isinstance(result, dict):
                return {
                    'success': False,
                    'error': (str(result) or f'未知错误（HTTP {response.status_code}）')[:200],
                    'code': 'UNKNOWN_ERROR',
                    'http_status': 500,
                }

            if not result.get('success', False):
                error = result.get('error', {})
                # error 可能是字符串，也可能是 {message, code} 字典
                if isinstance(error, dict):
                    message = error.get('message') or error.get('detail') or '未知错误'
                    code = error.get('code', 'UNKNOWN_ERROR')
                else:
                    message = str(error)
                    code = 'UPSTREAM_ERROR'
                # 结合 HTTP 状态码给出更精准的归类，便于前端/运维定位
                if response.status_code in (401, 403):
                    message = f'WeKnora 认证失败：{message}'
                    code = 'AUTH_ERROR'
                    http_status = 502
                elif response.status_code >= 500:
                    http_status = 502
                else:
                    http_status = 500
                logger.error(f"WeKnora API 错误: {message}")
                return {
                    'success': False,
                    'error': message,
                    'code': code,
                    'http_status': http_status,
                }

            return {
                'success': True,
                'data': result.get('data', {})
            }

        except requests.exceptions.Timeout:
            logger.error(f"WeKnora API 请求超时: {url}")
            return {'success': False, 'error': '请求超时', 'code': 'TIMEOUT', 'http_status': 504}
        except requests.exceptions.ConnectionError:
            logger.error(f"WeKnora API 连接错误: {url}")
            return {'success': False, 'error': '无法连接到 WeKnora 服务', 'code': 'CONNECTION_ERROR', 'http_status': 503}
        except requests.exceptions.RequestException as e:
            logger.error(f"WeKnora API 请求异常: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 'REQUEST_ERROR', 'http_status': 502}
        except Exception as e:
            logger.error(f"WeKnora API 未知错误: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 'UNKNOWN_ERROR', 'http_status': 500}

    # ==================== 知识库管理 ====================

    def create_knowledge_base(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建知识库"""
        return self._request('POST', '/knowledge-bases', data=data)

    def list_knowledge_bases(self) -> Dict[str, Any]:
        """获取知识库列表"""
        return self._request('GET', '/knowledge-bases')

    def get_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库详情"""
        return self._request('GET', f'/knowledge-bases/{kb_id}')

    def update_knowledge_base(self, kb_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识库"""
        return self._request('PUT', f'/knowledge-bases/{kb_id}', data=data)

    def delete_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """删除知识库"""
        return self._request('DELETE', f'/knowledge-bases/{kb_id}')

    def copy_knowledge_base(self, source_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """复制知识库"""
        data = {'source_id': source_id}
        if name:
            data['name'] = name
        return self._request('POST', '/knowledge-bases/copy', data=data)

    def get_copy_progress(self, task_id: str) -> Dict[str, Any]:
        """获取复制进度"""
        return self._request('GET', f'/knowledge-bases/copy/progress/{task_id}')

    def pin_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """置顶/取消置顶知识库"""
        return self._request('PUT', f'/knowledge-bases/{kb_id}/pin')

    def hybrid_search(self, query_text: str, knowledge_ids: List[str] = None, knowledge_base_ids: List[str] = None, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """
        向量检索 - 使用 knowledge-search API 进行向量相似度搜索

        Args:
            query_text: 搜索查询文本
            knowledge_ids: 指定搜索的知识文档ID列表
            knowledge_base_ids: 指定搜索的知识库ID列表
            top_k: 返回结果数量
        """
        data = {
            'query': query_text,
            'top_k': top_k,
        }
        if knowledge_ids:
            data['knowledge_ids'] = knowledge_ids
        elif knowledge_base_ids:
            data['knowledge_base_ids'] = knowledge_base_ids
        data.update(kwargs)
        return self._request('POST', '/knowledge-search', data=data)

    def search_chunks(
        self,
        query_text: str,
        knowledge_ids: List[str] = None,
        knowledge_base_ids: List[str] = None,
        top_k: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        搜索文档片段（chunks）

        与 hybrid_search 不同，此方法返回的是分块后的片段内容，
        而不是聚合后的完整文档。

        Args:
            query_text: 搜索查询文本
            knowledge_ids: 指定搜索的知识文档ID列表
            knowledge_base_ids: 指定搜索的知识库ID列表
            top_k: 返回结果数量
        """
        data = {
            'query': query_text,
            'top_k': top_k,
        }
        if knowledge_ids:
            data['knowledge_ids'] = knowledge_ids
        elif knowledge_base_ids:
            data['knowledge_base_ids'] = knowledge_base_ids
        data.update(kwargs)

        # 尝试使用 chunk-search API，如果不存在则回退到 knowledge-search
        result = self._request('POST', '/chunk-search', data=data)

        # 如果 chunk-search 不存在，尝试 knowledge-search 并检查返回格式
        if not result.get('success') and 'not found' in str(result.get('error', '')).lower():
            logger.info("chunk-search API not found, falling back to knowledge-search")
            result = self._request('POST', '/knowledge-search', data=data)

        return result

    def list_chunks(
        self,
        knowledge_id: str,
        page: int = 1,
        page_size: int = 25
    ) -> Dict[str, Any]:
        """
        获取知识文档的所有片段

        Args:
            knowledge_id: 知识文档ID
            page: 页码
            page_size: 每页数量
        """
        params = {'page': page, 'page_size': page_size}
        return self._request('GET', f'/chunks/{knowledge_id}', params=params)

    # ==================== 知识文档管理 ====================

    def upload_file_knowledge_raw(
        self,
        kb_id: str,
        file_content: bytes,
        file_name: str,
        metadata: Optional[Dict] = None,
        enable_multimodel: bool = True
    ) -> Dict[str, Any]:
        """上传文件知识"""
        files = {'file': (file_name, file_content)}
        data = {'enable_multimodel': str(enable_multimodel).lower()}
        if file_name:
            data['fileName'] = file_name
        if metadata:
            data['metadata'] = json.dumps(metadata)

        return self._request(
            'POST',
            f'/knowledge-bases/{kb_id}/knowledge/file',
            data=data,
            files=files
        )

    def create_url_knowledge(self, kb_id: str, url: str, enable_multimodel: bool = True) -> Dict[str, Any]:
        """从 URL 创建知识"""
        data = {'url': url, 'enable_multimodel': enable_multimodel}
        return self._request('POST', f'/knowledge-bases/{kb_id}/knowledge/url', data=data)

    def create_manual_knowledge(self, kb_id: str, title: str, content: str, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """创建手动 Markdown 知识"""
        data = {'title': title, 'content': content}
        if tag_id:
            data['tag_id'] = tag_id
        return self._request('POST', f'/knowledge-bases/{kb_id}/knowledge/manual', data=data)

    def list_knowledge(self, kb_id: str, page: int = 1, page_size: int = 20, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """获取知识列表"""
        params = {'page': page, 'page_size': page_size}
        if tag_id:
            params['tag_id'] = tag_id
        return self._request('GET', f'/knowledge-bases/{kb_id}/knowledge', params=params)

    def get_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        """获取知识详情"""
        return self._request('GET', f'/knowledge/{knowledge_id}')

    def update_knowledge(self, knowledge_id: str, title: Optional[str] = None, description: Optional[str] = None, tag_id: Optional[str] = None) -> Dict[str, Any]:
        """更新知识"""
        data = {}
        if title:
            data['title'] = title
        if description:
            data['description'] = description
        if tag_id:
            data['tag_id'] = tag_id
        return self._request('PUT', f'/knowledge/{knowledge_id}', data=data)

    def update_manual_knowledge(self, knowledge_id: str, title: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """更新手动 Markdown 知识"""
        data = {}
        if title:
            data['title'] = title
        if content:
            data['content'] = content
        return self._request('PUT', f'/knowledge/manual/{knowledge_id}', data=data)

    def delete_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        """删除知识"""
        return self._request('DELETE', f'/knowledge/{knowledge_id}')

    def download_knowledge(self, knowledge_id: str) -> requests.Response:
        """下载知识文件"""
        return self._request('GET', f'/knowledge/{knowledge_id}/download', raw_response=True)

    def reparse_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        """重新解析知识"""
        return self._request('POST', f'/knowledge/{knowledge_id}/reparse')

    def search_knowledge(self, keyword: Optional[str] = None, offset: int = 0, limit: int = 20, file_types: Optional[List[str]] = None, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """搜索知识"""
        params = {'offset': offset, 'limit': limit}
        if keyword:
            params['keyword'] = keyword
        if file_types:
            params['file_types'] = ','.join(file_types)
        if agent_id:
            params['agent_id'] = agent_id
        return self._request('GET', '/knowledge/search', params=params)

    def move_knowledge(self, knowledge_ids: List[str], source_kb_id: str, target_kb_id: str, mode: str = 'reuse_vectors') -> Dict[str, Any]:
        """迁移知识"""
        data = {
            'knowledge_ids': knowledge_ids,
            'source_kb_id': source_kb_id,
            'target_kb_id': target_kb_id,
            'mode': mode
        }
        return self._request('POST', '/knowledge/move', data=data)

    def get_move_progress(self, task_id: str) -> Dict[str, Any]:
        """获取迁移进度"""
        return self._request('GET', f'/knowledge/move/progress/{task_id}')

    def preview_knowledge(self, knowledge_id: str) -> requests.Response:
        """预览知识文件"""
        return self._request('GET', f'/knowledge/{knowledge_id}/preview', raw_response=True)

    # ==================== Agent 会话管理 ====================

    def create_session(self, knowledge_base_id: str) -> Dict[str, Any]:
        """创建 Agent 会话"""
        data = {'knowledge_base_id': knowledge_base_id}
        return self._request('POST', '/sessions', data=data)

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """删除 Agent 会话"""
        return self._request('DELETE', f'/sessions/{session_id}')

    def agent_chat(
        self,
        session_id: str,
        query: str,
        knowledge_base_ids: List[str],
        knowledge_ids: List[str],
        mentioned_items: List[Dict[str, Any]],
        agent_id: str = 'builtin-smart-reasoning',
        web_search_enabled: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Agent 对话接口

        后端解析 SSE 流式响应，返回完整结果。
        """
        url = f"{self.base_url}/agent-chat/{session_id}"
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'query': query,
            'agent_enabled': True,
            'web_search_enabled': web_search_enabled,
            'knowledge_base_ids': knowledge_base_ids,
            'knowledge_ids': knowledge_ids,
            'agent_id': agent_id,
            'mentioned_items': mentioned_items,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        # Agent 对话可能耗时较长，使用更长的超时时间
        agent_timeout = getattr(settings, 'WEKNORA_AGENT_TIMEOUT', 120)

        try:
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=agent_timeout
            )
            response.raise_for_status()

            # 解析 SSE 流
            full_answer = self._parse_sse_response(response)
            return {'success': True, 'data': {'content': full_answer}}

        except requests.exceptions.Timeout:
            logger.error(f"Agent chat 请求超时: session_id={session_id}")
            return {'success': False, 'error': '请求超时', 'code': 'TIMEOUT'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Agent chat 请求异常: {str(e)}")
            return {'success': False, 'error': str(e), 'code': 'REQUEST_ERROR'}

    def _parse_sse_response(self, response: requests.Response) -> str:
        """解析 Server-Sent Events 流，拼接完整答案"""
        full_answer = ''
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data:'):
                    try:
                        data = json.loads(decoded[5:].strip())
                        if data.get('response_type') == 'answer':
                            full_answer += data.get('content', '')
                    except json.JSONDecodeError:
                        pass
        return full_answer


# 默认实例
weknora_repository = WeKnoraRepository()
