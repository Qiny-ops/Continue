import axios from '@/api/axios.js'
import { handleApiError } from '@/api/errorHandler.js'
import { getCache, setCache, clearCache, CACHE_KEYS } from '@/utils/request-cache.js'

const BASE_URL = '/projects'

const USER_LIST_TTL = 10 * 60 * 1000
const ROLES_TTL = 5 * 60 * 1000

const validateParams = (params) => {
  return typeof params === 'object' && params !== null ? params : {}
}

const validateId = (id, name = 'ID') => {
  if (!id) {
    throw new Error(`${name}不能为空`)
  }
  return id
}

const memberApi = {
  async getMembers(projectId) {
    try {
      const validatedId = validateId(projectId, '项目ID')
      const response = await axios.get(`${BASE_URL}/${validatedId}/members/`)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async addMember(projectId, data) {
    try {
      const validatedId = validateId(projectId, '项目ID')
      const validatedData = validateParams(data)
      const response = await axios.post(`${BASE_URL}/${validatedId}/members/add/`, validatedData)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async updateMember(projectId, memberId, data) {
    try {
      const validatedProjectId = validateId(projectId, '项目ID')
      const validatedMemberId = validateId(memberId, '成员ID')
      const validatedData = validateParams(data)
      const response = await axios.put(`${BASE_URL}/${validatedProjectId}/members/${validatedMemberId}/`, validatedData)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async removeMember(projectId, memberId) {
    try {
      const validatedProjectId = validateId(projectId, '项目ID')
      const validatedMemberId = validateId(memberId, '成员ID')
      const response = await axios.delete(`${BASE_URL}/${validatedProjectId}/members/${validatedMemberId}/delete/`)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async batchUpdateMembers(projectId, memberIds, data) {
    try {
      const validatedId = validateId(projectId, '项目ID')
      if (!Array.isArray(memberIds) || memberIds.length === 0) {
        throw new Error('成员ID数组不能为空')
      }
      const validatedData = validateParams(data)
      const response = await axios.put(`${BASE_URL}/${validatedId}/members/batch/`, {
        member_ids: memberIds,
        ...validatedData
      })
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async getRoles(projectId) {
    try {
      const validatedId = validateId(projectId, '项目ID')
      const cacheKey = CACHE_KEYS.PROJECT_ROLES(validatedId)
      const cached = getCache(cacheKey)
      if (cached) return cached

      const response = await axios.get(`${BASE_URL}/${validatedId}/roles/`)
      setCache(cacheKey, response, ROLES_TTL)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async updateRole(projectId, roleKey, data) {
    try {
      const validatedProjectId = validateId(projectId, '项目ID')
      const validatedData = validateParams(data)
      const response = await axios.put(`${BASE_URL}/${validatedProjectId}/roles/${roleKey}/`, validatedData)
      clearCache(CACHE_KEYS.PROJECT_ROLES(validatedProjectId))
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async createRole(projectId, data) {
    try {
      const validatedProjectId = validateId(projectId, '项目ID')
      const validatedData = validateParams(data)
      const response = await axios.post(`${BASE_URL}/${validatedProjectId}/roles/create/`, validatedData)
      clearCache(CACHE_KEYS.PROJECT_ROLES(validatedProjectId))
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async fetchUsers() {
    try {
      const cached = getCache(CACHE_KEYS.USER_LIST)
      if (cached) return cached

      const response = await axios.get('/users/search/')
      setCache(CACHE_KEYS.USER_LIST, response, USER_LIST_TTL)
      return response
    } catch (error) {
      handleApiError(error, 'Member')
      throw error
    }
  },

  async getPermissions() {
    try {
      const response = await axios.get(`${BASE_URL}/permissions/`)
      return response
    } catch (error) {
      handleApiError(error, 'Permission')
      throw error
    }
  }
}

export default memberApi
