import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'

const BASE_URL = '/codecheck'

/**
 * 代码变更检查 API
 * 触发/查询/同步 通过 Django 代理（端口 8000），Django 内部再调 aicheck-service（8004）
 */
const codeCheckApi = {
  /** 任务列表 */
  async getTasks(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/`, { params })
      return response
    } catch (error) {
      handleApiError(error, 'CodeCheckTask')
      throw error
    }
  },

  /** 任务详情（自动 sync 微服务） */
  async getTaskDetail(id) {
    try {
      const response = await axios.get(`${BASE_URL}/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'CodeCheckTask')
      throw error
    }
  },

  /** 手动触发检查 */
  async triggerCheck(data) {
    try {
      const response = await axios.post(`${BASE_URL}/`, data)
      return response
    } catch (error) {
      handleApiError(error, 'CodeCheckTask')
      throw error
    }
  },

  /** 强制回写（拉微服务最新结果） */
  async syncTask(id) {
    try {
      const response = await axios.post(`${BASE_URL}/${id}/sync/`)
      return response
    } catch (error) {
      handleApiError(error, 'CodeCheckTask')
      throw error
    }
  }
}

export default codeCheckApi
