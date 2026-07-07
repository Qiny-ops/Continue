import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'
import { createSSEStream } from '@/utils/sse.js'

const BASE_URL = '/testcase'

const validateParams = (params) => {
  return typeof params === 'object' && params !== null ? params : {}
}

const validateId = (id) => {
  if (!id) {
    throw new Error('ID不能为空')
  }
  return id
}

const repositoryApi = {
  async getRepositories(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/repositories/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getRepository(id) {
    try {
      const response = await axios.get(`${BASE_URL}/repositories/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createRepository(data) {
    try {
      const response = await axios.post(`${BASE_URL}/repositories/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async updateRepository(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/repositories/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteRepository(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/repositories/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const versionApi = {
  async getVersions(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/versions/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getVersion(id) {
    try {
      const response = await axios.get(`${BASE_URL}/versions/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createVersion(data) {
    try {
      const response = await axios.post(`${BASE_URL}/versions/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async updateVersion(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/versions/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteVersion(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/versions/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async setDefaultVersion(id) {
    try {
      const response = await axios.post(`${BASE_URL}/versions/${validateId(id)}/set_default/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const moduleApi = {
  async getModules(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/modules/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getModuleTree(versionId) {
    try {
      const response = await axios.get(`${BASE_URL}/modules/tree/`, { params: { version: versionId } })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getModuleStatistics(versionId) {
    try {
      const response = await axios.get(`${BASE_URL}/modules/statistics/`, { params: { version: versionId } })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getModule(id) {
    try {
      const response = await axios.get(`${BASE_URL}/modules/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createModule(data) {
    try {
      const response = await axios.post(`${BASE_URL}/modules/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async updateModule(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/modules/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteModule(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/modules/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async batchDeleteModules(ids, versionId, deleteCases = false) {
    try {
      const response = await axios.post(`${BASE_URL}/modules/batch_delete/`, {
        ids,
        version: validateId(versionId),
        delete_cases: deleteCases
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const testCaseApi = {
  async getTestCases(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getTestCasesByVersion(versionId, params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/by_version/`, {
        params: { version: validateId(versionId), ...validateParams(params) }
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getTestCasesByModule(moduleId, params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/by_module/`, {
        params: { module: validateId(moduleId), ...validateParams(params) }
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getTestCasesByModuleTree(moduleId, params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/by_module_tree/`, {
        params: { module: validateId(moduleId), ...validateParams(params) }
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getTestCasesByProject(projectIdentifier, params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/by_project/`, {
        params: { project: projectIdentifier, ...validateParams(params) }
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getTestCase(id) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createTestCase(data) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async updateTestCase(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/cases/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async patchTestCase(id, data) {
    try {
      const response = await axios.patch(`${BASE_URL}/cases/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteTestCase(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/cases/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async copyTestCase(id) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/${validateId(id)}/copy/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async batchCopyTestCases(ids) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/batch_copy/`, { ids })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async batchDeleteTestCases(ids) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/batch_delete/`, { ids })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async batchMoveTestCases(ids, targetModuleId) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/batch_move/`, {
        ids,
        target_module: targetModuleId
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async batchUpdateTestCases(data) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/batch_update/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async exportTestCases(params) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/export/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const reviewApi = {
  async getReviews(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/reviews/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createReview(data) {
    try {
      const response = await axios.post(`${BASE_URL}/reviews/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async updateReview(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/reviews/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteReview(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/reviews/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 通过评审
  async approveReview(testCaseId, comment = '') {
    try {
      const response = await axios.post(`${BASE_URL}/cases/${validateId(testCaseId)}/approve/`, { comment })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 驳回评审
  async rejectReview(testCaseId, comment) {
    try {
      const response = await axios.post(`${BASE_URL}/cases/${validateId(testCaseId)}/reject/`, { comment })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 修改后重新提交评审
  async resubmitReview(testCaseId, revisionNote = '') {
    try {
      const response = await axios.post(`${BASE_URL}/cases/${validateId(testCaseId)}/resubmit/`, { revision_note: revisionNote })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 获取评审历史
  async getReviewHistory(testCaseId) {
    try {
      const response = await axios.get(`${BASE_URL}/cases/${validateId(testCaseId)}/review_history/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const executionApi = {
  async getExecutions(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/executions/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async getExecutionsByTestCase(testCaseId) {
    try {
      const response = await axios.get(`${BASE_URL}/executions/by_test_case/`, {
        params: { test_case: validateId(testCaseId) }
      })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async createExecution(data) {
    try {
      const response = await axios.post(`${BASE_URL}/executions/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  async deleteExecution(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/executions/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 获取用例执行统计
  async getExecutionStatistics(testCaseId) {
    try {
      const response = await axios.get(`${BASE_URL}/executions/${validateId(testCaseId)}/statistics/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  // 获取评审通过后的执行记录
  async getExecutionsSinceApproval(testCaseId) {
    try {
      const response = await axios.get(`${BASE_URL}/executions/${validateId(testCaseId)}/since_approval/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  }
}

const aiApi = {
  async getAIStatus() {
    try {
      const response = await axios.get(`${BASE_URL}/ai/status/`)
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  /**
   * 取消AI生成任务
   * @param {string} taskId - 任务ID（从SSE started事件获取）
   */
  async cancelGeneration(taskId) {
    try {
      const response = await axios.post(`${BASE_URL}/ai/cancel/`, { task_id: taskId })
      return response
    } catch (error) {
      handleApiError(error, 'TestCase')
      throw error
    }
  },

  /**
   * 流式生成测试用例（SSE）
   * @param {Object} data - 请求参数
   * @param {Object} callbacks - 回调函数
   *   - onProgress: 进度回调 (step, status, message)
   *   - onRequest: AI请求实时回调（发送/成功/失败）
   *   - onChunk: AI微服务流式chunk回调（实时生成内容）
   *   - onComplete: 完成回调
   *   - onError: 错误回调
   * @returns {Object} 包含 abort 方法的控制器对象
   */
  generateTestCasesStream(data, callbacks) {
    const { onProgress, onRequest, onChunk, onComplete, onError } = callbacks
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    const url = `${baseUrl}/testcase/ai/generate-stream/`

    return createSSEStream({
      url,
      data,
      callbacks: {
        onEvent(eventName, parsed) {
          if (eventName === 'started' && callbacks.onStarted) {
            callbacks.onStarted(parsed)
          } else if (eventName === 'progress' && onProgress) {
            onProgress(parsed)
          } else if (eventName === 'request' && onRequest) {
            onRequest(parsed)
          } else if (eventName === 'thinking_chunk' && callbacks.onThinkingChunk) {
            callbacks.onThinkingChunk(parsed)
          } else if (eventName === 'chunk' && onChunk) {
            onChunk(parsed)
          } else if (eventName === 'complete' && onComplete) {
            onComplete(parsed)
          } else if (eventName === 'error' && onError) {
            onError(parsed)
          } else if (eventName === 'cancelled' && callbacks.onCancelled) {
            callbacks.onCancelled(parsed)
          }
        },
        onError,
        onComplete: () => {}
      }
    })
  }
}

export {
  repositoryApi,
  versionApi,
  moduleApi,
  testCaseApi,
  reviewApi,
  executionApi,
  aiApi
}

export default {
  repository: repositoryApi,
  version: versionApi,
  module: moduleApi,
  testCase: testCaseApi,
  review: reviewApi,
  execution: executionApi,
  ai: aiApi
}
