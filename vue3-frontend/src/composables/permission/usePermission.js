import { computed } from 'vue'
import { usePermissionStore } from '@/stores/modules/permission'
import { useUserStore } from '@/stores/modules/user'
import { useProjectStore } from '@/stores/modules/project'
import { PERMISSIONS } from '@/constants/permissions'
import {
  isSystemAdmin,
  isProjectOwner,
  canManageProject as checkCanManageProject,
  canManageMembers as checkCanManageMembers,
  canManageTestCases as checkCanManageTestCases,
  canViewTestCases as checkCanViewTestCases,
  canExecuteTests as checkCanExecuteTests,
  canViewReports as checkCanViewReports,
  canManageSettings as checkCanManageSettings
} from '@/utils/permission'

export function usePermission() {
  const permissionStore = usePermissionStore()
  const userStore = useUserStore()
  const projectStore = useProjectStore()

  const isSystemAdminUser = computed(() =>
    isSystemAdmin(userStore.user)
  )

  const isProjectOwnerUser = computed(() =>
    isProjectOwner(projectStore.currentProject, userStore.user)
  )

  const isProjectAdminUser = computed(() =>
    permissionStore.isCurrentProjectAdmin
  )

  const canManageProject = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanManageProject(project, user, member)
  })

  const canManageMembers = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanManageMembers(project, user, member)
  })

  const canManageTestCases = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanManageTestCases(project, user, member)
  })

  const canViewTestCases = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanViewTestCases(project, user, member)
  })

  const canExecuteTests = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanExecuteTests(project, user, member)
  })

  const canViewReports = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanViewReports(project, user, member)
  })

  const canManageSettings = computed(() => {
    const project = projectStore.currentProject
    const user = userStore.user
    const member = permissionStore.currentMember
    return checkCanManageSettings(project, user, member)
  })

  const hasPermission = (permission) => {
    return permissionStore.hasProjectPermission(permission)
  }

  const hasAnyPermission = (permissions) => {
    return permissionStore.hasAnyProjectPermission(permissions)
  }

  const hasAllPermissions = (permissions) => {
    return permissionStore.hasAllProjectPermissions(permissions)
  }

  const checkPermission = (permission) => {
    if (isSystemAdminUser.value) return true
    if (isProjectOwnerUser.value) return true
    return hasPermission(permission)
  }

  const checkPermissions = (permissions, mode = 'any') => {
    if (isSystemAdminUser.value) return true
    if (isProjectOwnerUser.value) return true

    if (mode === 'all') {
      return hasAllPermissions(permissions)
    }
    return hasAnyPermission(permissions)
  }

  return {
    isSystemAdminUser,
    isProjectOwnerUser,
    isProjectAdminUser,
    canManageProject,
    canManageMembers,
    canManageTestCases,
    canViewTestCases,
    canExecuteTests,
    canViewReports,
    canManageSettings,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    checkPermission,
    checkPermissions,
    PERMISSIONS
  }
}
