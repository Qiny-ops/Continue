import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'

const BASE_URL = '/requirements'

const validateParams = (params) => {
  return typeof params === 'object' && params !== null ? params : {}
}

const validateId = (id) => {
  if (!id) {
    throw new Error('ID不能为空')
  }
  return id
}

const requirementApi = {
  async getRequirements(params = {}) {
    try {
      const response = await axios.get(`${BASE_URL}/`, { params: validateParams(params) })
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async getRequirement(id) {
    try {
      const response = await axios.get(`${BASE_URL}/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async createRequirement(data) {
    try {
      const response = await axios.post(`${BASE_URL}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async updateRequirement(id, data) {
    try {
      const response = await axios.put(`${BASE_URL}/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async patchRequirement(id, data) {
    try {
      const response = await axios.patch(`${BASE_URL}/${validateId(id)}/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async deleteRequirement(id) {
    try {
      const response = await axios.delete(`${BASE_URL}/${validateId(id)}/`)
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async batchDeleteRequirements(ids) {
    try {
      const response = await axios.post(`${BASE_URL}/batch_delete/`, { ids })
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async generateTestcases(id, data) {
    try {
      const response = await axios.post(`${BASE_URL}/${validateId(id)}/generate-testcases/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async batchGenerateTestcases(data) {
    try {
      const response = await axios.post(`${BASE_URL}/batch-generate-testcases/`, validateParams(data))
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  },

  async getModuleStatistics(projectId) {
    try {
      const response = await axios.get(`${BASE_URL}/module_statistics/`, { params: { project: projectId } })
      return response
    } catch (error) {
      handleApiError(error, 'Requirement')
      throw error
    }
  }
}

export { requirementApi }
export default requirementApi
