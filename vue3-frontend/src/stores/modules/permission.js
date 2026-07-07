import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/modules/user'
import { useMemberStore } from '@/stores/modules/member'
import { useProjectStore } from '@/stores/modules/project'
import memberApi from '@/api/modules/member.js'
import {
  hasPermission,
  isSystemAdmin,
  isProjectOwner,
  getMemberPermissions
} from '@/utils/permission'
import { PERMISSIONS } from '@/constants/permissions'

export const usePermissionStore = defineStore('permission', () => {
  const currentMember = ref(null)
  const projectRoles = ref([])
  const loading = ref(false)
  const error = ref(null)

  const userStore = useUserStore()

  const isCurrentProjectOwner = computed(() => {
    const projectStore = useProjectStore()
    return isProjectOwner(projectStore.currentProject, userStore.user)
  })

  const isCurrentProjectAdmin = computed(() => {
    if (isSystemAdmin(userStore.user)) return true
    if (isCurrentProjectOwner.value) return true
    return currentMember.value?.role === 'admin'
  })

  const canManageProject = computed(() => {
    if (isSystemAdmin(userStore.user)) return true
    if (isCurrentProjectOwner.value) return true
    if (isCurrentProjectAdmin.value) return true
    return false
  })

  const canManageMembers = computed(() => canManageProject.value)

  const currentPermissions = computed(() => {
    if (isSystemAdmin(userStore.user)) {
      return Object.values(PERMISSIONS)
    }
    if (isCurrentProjectOwner.value) {
      return Object.values(PERMISSIONS)
    }
    if (currentMember.value) {
      return getMemberPermissions(currentMember.value, projectRoles.value)
    }
    return []
  })

  const hasProjectPermission = (permission) => {
    return hasPermission(currentPermissions.value, permission)
  }

  const hasAnyProjectPermission = (permissions) => {
    if (!Array.isArray(permissions)) return false
    return permissions.some(p => hasProjectPermission(p))
  }

  const hasAllProjectPermissions = (permissions) => {
    if (!Array.isArray(permissions)) return false
    return permissions.every(p => hasProjectPermission(p))
  }

  const fetchCurrentMember = async (projectId) => {
    if (!projectId) {
      currentMember.value = null
      return null
    }

    loading.value = true
    error.value = null

    try {
      const memberStore = useMemberStore()

      if (memberStore.members.length === 0) {
        await memberStore.fetchMembers(projectId)
      }

      const userId = userStore.user?.id
      currentMember.value = memberStore.members.find(
        m => m.userId === userId || m.user_id === userId
      ) || null

      return currentMember.value
    } catch (err) {
      error.value = err.message || '获取成员信息失败'
      currentMember.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  const fetchProjectRoles = async (projectId) => {
    if (!projectId) {
      projectRoles.value = []
      return []
    }

    loading.value = true
    error.value = null

    try {
      const response = await memberApi.getRoles(projectId)
      // 后端返回 { roles: [...], all_permissions: [...] }
      projectRoles.value = response?.data?.roles || response?.data || response || []
      return projectRoles.value
    } catch (err) {
      error.value = err.message || '获取角色列表失败'
      projectRoles.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  const initProjectPermissions = async (projectId) => {
    loading.value = true
    error.value = null

    try {
      await Promise.all([
        fetchCurrentMember(projectId),
        fetchProjectRoles(projectId)
      ])
    } catch (err) {
      error.value = err.message || '初始化权限失败'
    } finally {
      loading.value = false
    }
  }

  const clearPermissions = () => {
    currentMember.value = null
    projectRoles.value = []
    error.value = null
  }

  const setProjectRoles = (roles) => {
    projectRoles.value = roles
  }

  return {
    currentMember,
    projectRoles,
    loading,
    error,
    isCurrentProjectOwner,
    isCurrentProjectAdmin,
    canManageProject,
    canManageMembers,
    currentPermissions,
    hasProjectPermission,
    hasAnyProjectPermission,
    hasAllProjectPermissions,
    fetchCurrentMember,
    fetchProjectRoles,
    initProjectPermissions,
    clearPermissions,
    setProjectRoles
  }
})
