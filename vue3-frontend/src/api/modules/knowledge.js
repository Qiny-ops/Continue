/**
 * 知识库管理 API
 * 对接 WeKnora 知识库后端服务
 */

import axios from '@/api/axios.js'

// ==================== 知识库管理 ====================

/**
 * 获取知识库列表
 * @returns {Promise<Object>} 知识库列表
 */
export async function listKnowledgeBases() {
  const response = await axios.get('/knowledge/')
  return response
}

/**
 * 创建知识库
 * @param {Object} data - 知识库配置
 * @param {string} data.name - 知识库名称
 * @param {string} [data.description] - 描述
 * @param {string} [data.type='document'] - 类型 (document/faq)
 * @param {Object} [data.chunking_config] - 分块配置
 * @param {string} [data.embedding_model_id] - 嵌入模型ID
 * @param {string} [data.summary_model_id] - 概要模型ID
 * @returns {Promise<Object>} 创建的知识库信息
 */
export async function createKnowledgeBase(data) {
  const response = await axios.post('/knowledge/create/', data)
  return response
}

/**
 * 获取知识库详情
 * @param {string} kbId - 知识库ID
 * @returns {Promise<Object>} 知识库详情
 */
export async function getKnowledgeBase(kbId) {
  const response = await axios.get(`/knowledge/${kbId}/`)
  return response
}

/**
 * 更新知识库
 * @param {string} kbId - 知识库ID
 * @param {Object} data - 更新数据
 * @returns {Promise<Object>} 更新后的知识库信息
 */
export async function updateKnowledgeBase(kbId, data) {
  const response = await axios.put(`/knowledge/${kbId}/update/`, data)
  return response
}

/**
 * 删除知识库
 * @param {string} kbId - 知识库ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteKnowledgeBase(kbId) {
  const response = await axios.delete(`/knowledge/${kbId}/delete/`)
  return response
}

/**
 * 复制知识库
 * @param {string} sourceId - 源知识库ID
 * @param {string} [name] - 新知识库名称
 * @returns {Promise<Object>} 复制任务信息
 */
export async function copyKnowledgeBase(sourceId, name) {
  const response = await axios.post('/knowledge/copy/', { source_id: sourceId, name })
  return response
}

/**
 * 获取复制进度
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 复制进度信息
 */
export async function getCopyProgress(taskId) {
  const response = await axios.get(`/knowledge/copy/progress/${taskId}/`)
  return response
}

/**
 * 置顶/取消置顶知识库
 * @param {string} kbId - 知识库ID
 * @returns {Promise<Object>} 更新后的知识库信息
 */
export async function pinKnowledgeBase(kbId) {
  const response = await axios.put(`/knowledge/${kbId}/pin/`)
  return response
}

/**
 * 混合搜索（向量+关键词）
 * @param {string} kbId - 知识库ID
 * @param {Object} params - 搜索参数
 * @param {string} params.query_text - 查询文本
 * @param {number} [params.vector_threshold] - 向量相似度阈值
 * @param {number} [params.keyword_threshold] - 关键词匹配阈值
 * @param {number} [params.match_count] - 返回结果数量
 * @returns {Promise<Object>} 搜索结果
 */
export async function hybridSearch(kbId, params) {
  const response = await axios.get(`/knowledge/${kbId}/search/`, { params })
  return response
}

// ==================== 知识文档管理 ====================

/**
 * 获取知识库下的知识列表
 * @param {string} kbId - 知识库ID
 * @param {Object} [params] - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=20] - 每页数量
 * @param {string} [params.tag_id] - 标签ID筛选
 * @returns {Promise<Object>} 知识列表
 */
export async function listKnowledge(kbId, params = {}) {
  const response = await axios.get(`/knowledge/${kbId}/knowledge/`, { params })
  return response
}

/**
 * 上传文件知识
 * @param {string} kbId - 知识库ID
 * @param {File} file - 文件对象
 * @param {Object} [options] - 选项
 * @param {boolean} [options.enable_multimodel=true] - 是否启用多模态处理
 * @param {string} [options.metadata] - 元数据
 * @returns {Promise<Object>} 创建的知识信息
 */
export async function uploadFileKnowledge(kbId, file, options = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (options.enable_multimodel !== undefined) {
    formData.append('enable_multimodel', String(options.enable_multimodel))
  }
  if (options.metadata) {
    formData.append('metadata', options.metadata)
  }

  const response = await axios.post(`/knowledge/${kbId}/knowledge/file/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response
}

/**
 * 从 URL 创建知识
 * @param {string} kbId - 知识库ID
 * @param {string} url - 网页URL
 * @param {boolean} [enableMultimodel=true] - 是否启用多模态处理
 * @returns {Promise<Object>} 创建的知识信息
 */
export async function createUrlKnowledge(kbId, url, enableMultimodel = true) {
  const response = await axios.post(`/knowledge/${kbId}/knowledge/url/`, {
    url,
    enable_multimodel: enableMultimodel
  })
  return response
}

/**
 * 创建手动 Markdown 知识
 * @param {string} kbId - 知识库ID
 * @param {Object} data - 知识数据
 * @param {string} data.title - 标题
 * @param {string} data.content - Markdown 内容
 * @param {string} [data.tag_id] - 标签ID
 * @returns {Promise<Object>} 创建的知识信息
 */
export async function createManualKnowledge(kbId, data) {
  const response = await axios.post(`/knowledge/${kbId}/knowledge/manual/`, data)
  return response
}

/**
 * 获取知识详情
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Object>} 知识详情
 */
export async function getKnowledge(knowledgeId) {
  const response = await axios.get(`/knowledge/knowledge/${knowledgeId}/`)
  return response
}

/**
 * 更新知识
 * @param {string} knowledgeId - 知识ID
 * @param {Object} data - 更新数据
 * @param {string} [data.title] - 标题
 * @param {string} [data.description] - 描述
 * @param {string} [data.tag_id] - 标签ID
 * @returns {Promise<Object>} 更新结果
 */
export async function updateKnowledge(knowledgeId, data) {
  const response = await axios.put(`/knowledge/knowledge/${knowledgeId}/update/`, data)
  return response
}

/**
 * 更新手动 Markdown 知识
 * @param {string} knowledgeId - 知识ID
 * @param {Object} data - 更新数据
 * @param {string} [data.title] - 标题
 * @param {string} [data.content] - Markdown 内容
 * @returns {Promise<Object>} 更新结果
 */
export async function updateManualKnowledge(knowledgeId, data) {
  const response = await axios.put(`/knowledge/knowledge/manual/${knowledgeId}/update/`, data)
  return response
}

/**
 * 删除知识
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteKnowledge(knowledgeId) {
  const response = await axios.delete(`/knowledge/knowledge/${knowledgeId}/delete/`)
  return response
}

/**
 * 下载知识文件
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Blob>} 文件内容
 */
export async function downloadKnowledge(knowledgeId) {
  const response = await axios.get(`/knowledge/knowledge/${knowledgeId}/download/`, {
    responseType: 'blob'
  })
  return response
}

/**
 * 重新解析知识
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Object>} 重解析结果
 */
export async function reparseKnowledge(knowledgeId) {
  const response = await axios.post(`/knowledge/knowledge/${knowledgeId}/reparse/`)
  return response
}

/**
 * 预览知识文件
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Blob>} 文件内容 Blob
 */
export async function previewKnowledge(knowledgeId) {
  const response = await axios.get(`/knowledge/knowledge/${knowledgeId}/preview/`, {
    responseType: 'blob'
  })
  return response
}

/**
 * 获取知识内容
 * @param {string} knowledgeId - 知识ID
 * @returns {Promise<Object>} 知识内容
 */
export async function getKnowledgeContent(knowledgeId) {
  const response = await axios.get(`/knowledge/knowledge/${knowledgeId}/content/`)
  return response
}

/**
 * 搜索知识
 * @param {Object} params - 搜索参数
 * @param {string} [params.keyword] - 搜索关键词
 * @param {number} [params.offset=0] - 偏移量
 * @param {number} [params.limit=20] - 返回数量
 * @param {string} [params.file_types] - 文件类型过滤（逗号分隔）
 * @returns {Promise<Object>} 搜索结果
 */
export async function searchKnowledge(params = {}) {
  const response = await axios.get('/knowledge/search/', { params })
  return response
}

/**
 * 迁移知识到另一个知识库
 * @param {Object} data - 迁移数据
 * @param {string[]} data.knowledge_ids - 知识ID列表
 * @param {string} data.source_kb_id - 源知识库ID
 * @param {string} data.target_kb_id - 目标知识库ID
 * @param {string} [data.mode='reuse_vectors'] - 迁移模式
 * @returns {Promise<Object>} 迁移任务信息
 */
export async function moveKnowledge(data) {
  const response = await axios.post('/knowledge/knowledge/move/', data)
  return response
}

/**
 * 获取知识迁移进度
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 迁移进度信息
 */
export async function getMoveProgress(taskId) {
  const response = await axios.get(`/knowledge/knowledge/move/progress/${taskId}/`)
  return response
}

export default {
  // 知识库管理
  listKnowledgeBases,
  createKnowledgeBase,
  getKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  copyKnowledgeBase,
  getCopyProgress,
  pinKnowledgeBase,
  hybridSearch,

  // 知识文档管理
  listKnowledge,
  uploadFileKnowledge,
  createUrlKnowledge,
  createManualKnowledge,
  getKnowledge,
  updateKnowledge,
  updateManualKnowledge,
  deleteKnowledge,
  downloadKnowledge,
  reparseKnowledge,
  previewKnowledge,
  getKnowledgeContent,
  searchKnowledge,
  moveKnowledge,
  getMoveProgress
}
