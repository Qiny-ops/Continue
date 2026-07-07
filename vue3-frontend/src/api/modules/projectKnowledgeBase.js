/**
 * 项目知识库关联 API
 */

import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'

/**
 * 获取项目关联的知识库
 * @param {string|number} projectId - 项目ID或code
 * @returns {Promise<Object>} 知识库信息
 */
export async function getProjectKnowledgeBase(projectId) {
  try {
    const response = await axios.get(`/projects/${projectId}/knowledge-base/`)
    return response
  } catch (error) {
    handleApiError(error, '获取项目知识库失败')
    throw error
  }
}

/**
 * 关联知识库到项目
 * @param {string|number} projectId - 项目ID或code
 * @param {Object} data - 知识库数据
 * @param {string} data.knowledgeBaseId - 知识库ID
 * @param {string} data.knowledgeBaseName - 知识库名称
 * @returns {Promise<Object>} 关联结果
 */
export async function linkKnowledgeBase(projectId, data) {
  try {
    const response = await axios.post(`/projects/${projectId}/knowledge-base/link/`, data)
    return response
  } catch (error) {
    handleApiError(error, '关联知识库失败')
    throw error
  }
}

/**
 * 解除知识库关联
 * @param {string|number} projectId - 项目ID或code
 * @returns {Promise<Object>} 操作结果
 */
export async function unlinkKnowledgeBase(projectId) {
  try {
    const response = await axios.delete(`/projects/${projectId}/knowledge-base/unlink/`)
    return response
  } catch (error) {
    handleApiError(error, '解除知识库关联失败')
    throw error
  }
}

/**
 * 为项目创建知识库
 * @param {string|number} projectId - 项目ID或code
 * @param {Object} [data] - 知识库配置
 * @param {string} [data.name] - 知识库名称
 * @param {string} [data.description] - 描述
 * @returns {Promise<Object>} 创建结果
 */
export async function createProjectKnowledgeBase(projectId, data = {}) {
  try {
    const response = await axios.post(`/projects/${projectId}/knowledge-base/create/`, data)
    return response
  } catch (error) {
    handleApiError(error, '创建项目知识库失败')
    throw error
  }
}

export default {
  getProjectKnowledgeBase,
  linkKnowledgeBase,
  unlinkKnowledgeBase,
  createProjectKnowledgeBase
}
