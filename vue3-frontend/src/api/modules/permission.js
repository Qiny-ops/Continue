import axios from '../axios'
import { handleApiError } from '../errorHandler'

const BASE_URL = '/users'

export default {
  async getPermissions() {
    try {
      const response = await axios.get(`${BASE_URL}/permissions/`)
      return response
    } catch (error) {
      handleApiError(error, 'Permission')
      throw error
    }
  },

  // 获取当前用户权限
  async getMyPermissions(projectId = null) {
    try {
      const params = projectId ? { project: projectId } : {}
      const response = await axios.get(`${BASE_URL}/my-permissions/`, { params })
      return response
    } catch (error) {
      handleApiError(error, 'Permission')
      throw error
    }
  },

  // 获取权限体系信息
  async getPermissionInfo() {
    try {
      const response = await axios.get(`${BASE_URL}/permission-info/`)
      return response
    } catch (error) {
      handleApiError(error, 'Permission')
      throw error
    }
  }
}