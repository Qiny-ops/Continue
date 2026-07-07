import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'

const BASE_URL = '/projects'

const validateParams = (params) => {
  return typeof params === 'object' && params !== null ? params : {}
}

const validateId = (id) => {
  if (!id) {
    throw new Error('项目ID或标识不能为空')
  }
  return id
}

const projectApi = {
  async getProjects(params = {}) {
    try {
      const validatedParams = validateParams(params)
      const response = await axios.get(BASE_URL, { params: validatedParams })
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async getProject(id) {
    try {
      const validatedId = validateId(id)
      const response = await axios.get(`${BASE_URL}/${validatedId}`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async createProject(projectData) {
    try {
      const validatedData = validateParams(projectData)
      const response = await axios.post(`${BASE_URL}/create/`, validatedData)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async updateProject(id, projectData) {
    try {
      const validatedId = validateId(id)
      const validatedData = validateParams(projectData)
      const response = await axios.put(`${BASE_URL}/${validatedId}/update/`, validatedData)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async deleteProject(id) {
    try {
      const validatedId = validateId(id)
      const response = await axios.delete(`${BASE_URL}/${validatedId}/delete/`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async searchProjects(keyword, params = {}) {
    try {
      const validatedParams = validateParams(params)
      const response = await axios.get(`${BASE_URL}/search/`, {
        params: { q: keyword, ...validatedParams }
      })
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async getProjectStats() {
    try {
      const response = await axios.get(`${BASE_URL}/stats/`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async getFavoriteProjects() {
    try {
      const response = await axios.get(`${BASE_URL}/favorites/`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async toggleFavorite(id) {
    try {
      const validatedId = validateId(id)
      const response = await axios.post(`${BASE_URL}/${validatedId}/favorite/`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async setFavorite(id, isFavorite) {
    try {
      const validatedId = validateId(id)
      const response = await axios.post(`${BASE_URL}/${validatedId}/favorite/set/`, { isFavorite })
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async updateVisitTime(id) {
    try {
      const validatedId = validateId(id)
      const response = await axios.post(`${BASE_URL}/${validatedId}/visit/`)
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  },

  async getProjectActivities(id, limit = 10) {
    try {
      const validatedId = validateId(id)
      const response = await axios.get(`${BASE_URL}/${validatedId}/activities/`, {
        params: { limit }
      })
      return response
    } catch (error) {
      handleApiError(error, 'Project')
      throw error
    }
  }
}

export default projectApi
