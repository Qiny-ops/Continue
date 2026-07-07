import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'
import { getToken } from '@/api/axios.js'
import { createSSEStream } from '@/utils/sse.js'

const BASE_URL = '/apitest'

/**
 * API 测试环境管理
 */
const environmentApi = {
  async getEnvironments(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/environments/`, { params })
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async getEnvironment(id) {
    try {
      const response = await axios.get(`${BASE_URL}/environments/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async createEnvironment(data) {
    try {
      const response = await axios.post(`${BASE_URL}/environments/`, data)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async updateEnvironment(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/environments/${id}/`, data)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async deleteEnvironment(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/environments/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async setDefault(id) {
    try {
      const response = await axios.post(`${BASE_URL}/environments/${id}/set_default/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  },

  async testConnection(id) {
    try {
      const response = await axios.post(`${BASE_URL}/environments/${id}/test_connection/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiEnvironment')
      throw error
    }
  }
}

/**
 * API 测试用例管理
 */
const apiTestCaseApi = {
  async getCases(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/`, { params })
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestCase')
      throw error
    }
  },

  async getCase(id) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestCase')
      throw error
    }
  },

  async createCase(data) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/`, data)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestCase')
      throw error
    }
  },

  async updateCase(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/cases/${id}/`, data)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestCase')
      throw error
    }
  },

  async deleteCase(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/cases/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestCase')
      throw error
    }
  },

  async getRuns(caseId) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/${caseId}/runs/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestRun')
      throw error
    }
  },

  executeCaseStream(id, environmentId, onMessage, onError, onComplete) {
    const url = `${axios.defaults.baseURL}${BASE_URL}/cases/${id}/execute/`

    return createSSEStream({
      url,
      data: { environment_id: environmentId },
      callbacks: {
        onEvent(eventName, parsed) {
          // executeCaseStream 的 SSE 只有 data 行，无 event 行
          onMessage?.(parsed)
        },
        onError: (err) => onError?.(new Error(err.error || '执行失败')),
        onComplete: () => onComplete?.()
      }
    })
  },

  generateFromKbStream(projectId, knowledgeBaseId, knowledgeId, onMessage, onError, onComplete) {
    const url = `${axios.defaults.baseURL}${BASE_URL}/cases/generate_from_kb/`
    const token = getToken()

    if (!token) {
      onError?.(new Error('未登录或 token 已过期'))
      return null
    }

    let fullContent = ''

    return createSSEStream({
      url,
      data: {
        project_id: projectId,
        knowledge_base_id: knowledgeBaseId,
        knowledge_ids: knowledgeId ? [knowledgeId] : []
      },
      callbacks: {
        onEvent(eventName, parsed) {
          if (parsed.type === 'chunk') {
            fullContent += parsed.data?.content || ''
          }
          onMessage?.(parsed)
        },
        onError: (err) => onError?.(new Error(err.error || '生成失败')),
        onComplete: () => onComplete?.(fullContent)
      }
    })
  },

  validateCaseStream(id, executionResults, onMessage, onError, onComplete) {
    const url = `${axios.defaults.baseURL}${BASE_URL}/cases/${id}/validate/`

    return createSSEStream({
      url,
      data: { execution_results: executionResults },
      callbacks: {
        onEvent(eventName, parsed) {
          onMessage?.(parsed)
        },
        onError: (err) => onError?.(new Error(err.error || '校验失败')),
        onComplete: () => onComplete?.()
      }
    })
  }
}

/**
 * API 测试执行记录
 */
const apiTestRunApi = {
  async getRuns(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/runs/`, { params })
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestRun')
      throw error
    }
  },

  async getRun(id) {
    try {
      const response = await axios.get(`${BASE_URL}/runs/${id}/`)
      return response
    } catch (error) {
      handleApiError(error, 'ApiTestRun')
      throw error
    }
  }
}

export { environmentApi, apiTestCaseApi, apiTestRunApi }
export default {
  environment: environmentApi,
  testCase: apiTestCaseApi,
  run: apiTestRunApi
}