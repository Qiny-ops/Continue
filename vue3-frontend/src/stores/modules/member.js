/**
 * 成员管理状态管理
 * 使用Pinia进行项目成员相关的状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import memberApi from '@/api/modules/member.js'

export const useMemberStore = defineStore('member', () => {
  const members = ref([])
  const invitations = ref([])
  const roles = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentProjectId = ref(null)

  const memberCount = computed(() => members.value.length)

  const activeMembers = computed(() =>
    members.value.filter(m => m.status === 'active' || m.is_active === true)
  )

  const adminMembers = computed(() =>
    members.value.filter(m => m.role === 'admin' || m.role_name === '管理员')
  )

  /**
   * 获取项目成员列表
   * @param {string|number} projectId - 项目ID
   * @returns {Promise<Array>} 成员列表
   */
  const fetchMembers = async (projectId) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }

    loading.value = true
    error.value = null
    currentProjectId.value = projectId

    try {
      const response = await memberApi.getMembers(projectId)

      const rawMembers = response.data?.data?.data ||
                         response.data?.data?.results ||
                         response.data?.data?.members ||
                         response.data?.data ||
                         response.data?.results ||
                         response.data?.members ||
                         response.data || []

      const membersArray = Array.isArray(rawMembers) ? rawMembers : []
      members.value = membersArray

      return members.value
    } catch (err) {
      error.value = err.message || '获取成员列表失败'
    } finally {
      loading.value = false
    }
  }

  /**
   * 添加成员
   * @param {string|number} projectId - 项目ID
   * @param {Object} data - 成员数据
   * @returns {Promise<Object>} 新添加的成员
   */
  const addMember = async (projectId, data) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!data || typeof data !== 'object') {
      throw new Error('成员数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.addMember(projectId, data)
      const responseData = response?.data

      if (responseData && responseData.code === 200 && responseData.data) {
        const newMember = responseData.data
        const member = {
          id: newMember.id || newMember.userId,
          user_id: newMember.userId || newMember.user_id || newMember.id,
          userId: newMember.userId || newMember.user_id || newMember.id,
          name: newMember.name || newMember.nickname || newMember.username || '',
          nickname: newMember.nickname || newMember.name || '',
          email: newMember.email || '',
          avatar: newMember.avatar || newMember.avatar_url || '',
          role: newMember.role || 'viewer',
          status: newMember.status || 'active',
          joined_at: newMember.joinedAt || newMember.joined_at || newMember.created_at || new Date().toISOString()
        }
        members.value.push(member)
        return member
      }

      return null
    } catch (err) {
      error.value = err.message || '添加成员失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新成员信息
   * @param {string|number} projectId - 项目ID
   * @param {string|number} memberId - 成员ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的成员信息
   */
  const updateMember = async (projectId, memberId, data) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!memberId) {
      throw new Error('成员ID不能为空')
    }
    if (!data || typeof data !== 'object') {
      throw new Error('更新数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.updateMember(projectId, memberId, data)
      const updatedMember = response.data?.data || response.data

      const index = members.value.findIndex(m => m.id === memberId || m.user_id === memberId)
      if (index !== -1) {
        members.value[index] = { ...members.value[index], ...updatedMember }
      }

      return updatedMember
    } catch (err) {
      error.value = err.message || '更新成员失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 移除成员
   * @param {string|number} projectId - 项目ID
   * @param {string|number} memberId - 成员ID
   * @returns {Promise<void>}
   */
  const removeMember = async (projectId, memberId) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!memberId) {
      throw new Error('成员ID不能为空')
    }

    loading.value = true
    error.value = null

    try {
      await memberApi.removeMember(projectId, memberId)
      members.value = members.value.filter(m => m.id !== memberId && m.user_id !== memberId)
    } catch (err) {
      error.value = err.message || '移除成员失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 邀请成员
   * @param {string|number} projectId - 项目ID
   * @param {Object} data - 邀请数据
   * @returns {Promise<Object>} 邀请信息
   */
  const inviteMember = async (projectId, data) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!data || typeof data !== 'object') {
      throw new Error('邀请数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.inviteMember(projectId, data)
      const invitation = response.data?.data || response.data

      if (invitation) {
        invitations.value.push(invitation)
      }

      return invitation
    } catch (err) {
      error.value = err.message || '邀请成员失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取邀请列表
   * @param {string|number} projectId - 项目ID
   * @returns {Promise<Array>} 邀请列表
   */
  const fetchInvitations = async (projectId) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.getInvitations(projectId)

      const rawInvitations = response.data?.data?.data ||
                             response.data?.data?.results ||
                             response.data?.data?.invitations ||
                             response.data?.data ||
                             response.data?.results ||
                             response.data?.invitations ||
                             response.data || []

      const invitationsArray = Array.isArray(rawInvitations) ? rawInvitations : []
      invitations.value = invitationsArray

      return invitations.value
    } catch (err) {
      error.value = err.message || '获取邀请列表失败'
    } finally {
      loading.value = false
    }
  }

  /**
   * 批量更新成员
   * @param {string|number} projectId - 项目ID
   * @param {Array} memberIds - 成员ID数组
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新结果
   */
  const batchUpdateMembers = async (projectId, memberIds, data) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!Array.isArray(memberIds) || memberIds.length === 0) {
      throw new Error('成员ID数组不能为空')
    }
    if (!data || typeof data !== 'object') {
      throw new Error('更新数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.batchUpdateMembers(projectId, memberIds, data)
      const result = response.data?.data || response.data

      memberIds.forEach(memberId => {
        const index = members.value.findIndex(m => m.id === memberId || m.user_id === memberId)
        if (index !== -1) {
          members.value[index] = { ...members.value[index], ...data }
        }
      })

      return result
    } catch (err) {
      error.value = err.message || '批量更新成员失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取角色列表
   * @param {string|number} projectId - 项目ID
   * @returns {Promise<Array>} 角色列表
   */
  const fetchRoles = async (projectId) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.getRoles(projectId)

      const rawRoles = response.data?.data?.data ||
                       response.data?.data?.results ||
                       response.data?.data?.roles ||
                       response.data?.data ||
                       response.data?.results ||
                       response.data?.roles ||
                       response.data || []

      const rolesArray = Array.isArray(rawRoles) ? rawRoles : []
      roles.value = rolesArray

      return roles.value
    } catch (err) {
      error.value = err.message || '获取角色列表失败'
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新角色权限
   * @param {string|number} projectId - 项目ID
   * @param {string|number} roleId - 角色ID
   * @param {Object} data - 更新数据
   * @returns {Promise<Object>} 更新后的角色信息
   */
  const updateRole = async (projectId, roleId, data) => {
    if (!projectId) {
      throw new Error('项目ID不能为空')
    }
    if (!roleId) {
      throw new Error('角色ID不能为空')
    }
    if (!data || typeof data !== 'object') {
      throw new Error('更新数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.updateRole(projectId, roleId, data)
      const updatedRole = response.data?.data || response.data

      const index = roles.value.findIndex(r => r.id === roleId)
      if (index !== -1) {
        roles.value[index] = { ...roles.value[index], ...updatedRole }
      }

      return updatedRole
    } catch (err) {
      error.value = err.message || '更新角色权限失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 设置当前项目ID
   * @param {string|number} projectId - 项目ID
   */
  const setCurrentProject = (projectId) => {
    currentProjectId.value = projectId
  }

  /**
   * 清除错误信息
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * 重置状态
   */
  const resetState = () => {
    members.value = []
    invitations.value = []
    roles.value = []
    loading.value = false
    error.value = null
    currentProjectId.value = null
  }

  /**
   * 获取用户列表
   * @returns {Promise<Array>} 用户列表
   */
  const fetchUsers = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await memberApi.fetchUsers()

      const rawUsers = response.data?.data?.data ||
                       response.data?.data?.results ||
                       response.data?.data?.users ||
                       response.data?.data ||
                       response.data?.results ||
                       response.data?.users ||
                       response.data || []

      const usersArray = Array.isArray(rawUsers) ? rawUsers : []
      return usersArray.map(user => {
        return {
          id: user.id || user.user_id,
          name: user.name || user.nickname || user.username,
          username: user.username || user.user_name || '',
          nickname: user.nickname,
          email: user.email,
          avatar: user.avatar || user.avatar_url || ''
        }
      })
    } catch (err) {
      error.value = err.message || '获取用户列表失败'
      return []
    } finally {
      loading.value = false
    }
  }

  return {
    members,
    invitations,
    roles,
    loading,
    error,
    currentProjectId,

    memberCount,
    activeMembers,
    adminMembers,

    fetchMembers,
    addMember,
    updateMember,
    removeMember,
    inviteMember,
    fetchInvitations,
    batchUpdateMembers,
    fetchRoles,
    updateRole,
    fetchUsers,
    setCurrentProject,
    clearError,
    resetState
  }
})
