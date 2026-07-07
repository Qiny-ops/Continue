import { usePermissionStore } from '@/stores/modules/permission'
import { useUserStore } from '@/stores/modules/user'

function checkPermission(el, binding) {
  const permissionStore = usePermissionStore()
  const userStore = useUserStore()
  const { value } = binding

  if (!value) return

  // 系统管理员直接显示
  if (userStore.user?.system_role?.code === 'admin') {
    return
  }

  let hasPermission = false

  if (Array.isArray(value)) {
    hasPermission = permissionStore.hasAnyProjectPermission(value)
  } else {
    hasPermission = permissionStore.hasProjectPermission(value)
  }

  if (!hasPermission) {
    el.parentNode?.removeChild(el)
  }
}

function checkRole(el, binding) {
  const permissionStore = usePermissionStore()
  const userStore = useUserStore()
  const { value } = binding

  if (!value) return

  // 系统管理员直接显示
  if (userStore.user?.system_role?.code === 'admin') {
    return
  }

  let hasRole = false

  if (permissionStore.isCurrentProjectOwner) {
    hasRole = true
  } else if (Array.isArray(value)) {
    hasRole = value.includes(permissionStore.currentMember?.role)
  } else {
    hasRole = permissionStore.currentMember?.role === value
  }

  if (!hasRole) {
    el.parentNode?.removeChild(el)
  }
}

function checkAdmin(el) {
  const permissionStore = usePermissionStore()
  const userStore = useUserStore()

  // 系统管理员直接显示
  if (userStore.user?.system_role?.code === 'admin') {
    return
  }

  if (!permissionStore.isCurrentProjectAdmin) {
    el.parentNode?.removeChild(el)
  }
}

function checkSystemPermission(el, binding) {
  const userStore = useUserStore()
  const { value } = binding

  if (!value) return

  // 只有系统管理员才有系统权限
  if (userStore.user?.system_role?.code !== 'admin') {
    el.parentNode?.removeChild(el)
  }
}

function checkAllPermissions(el, binding) {
  const permissionStore = usePermissionStore()
  const userStore = useUserStore()
  const { value } = binding

  if (!value || !Array.isArray(value)) return

  // 系统管理员直接显示
  if (userStore.user?.system_role?.code === 'admin') {
    return
  }

  const hasAll = permissionStore.hasAllProjectPermissions(value)
  if (!hasAll) {
    el.parentNode?.removeChild(el)
  }
}

export const permissionDirective = {
  mounted(el, binding) {
    checkPermission(el, binding)
  },
  updated(el, binding) {
    checkPermission(el, binding)
  }
}

export const roleDirective = {
  mounted(el, binding) {
    checkRole(el, binding)
  },
  updated(el, binding) {
    checkRole(el, binding)
  }
}

export const adminDirective = {
  mounted(el) {
    checkAdmin(el)
  },
  updated(el) {
    checkAdmin(el)
  }
}

/**
 * 系统权限指令
 * 用法：v-system-permission="'user_manage'"
 */
export const systemPermissionDirective = {
  mounted(el, binding) {
    checkSystemPermission(el, binding)
  },
  updated(el, binding) {
    checkSystemPermission(el, binding)
  }
}

/**
 * 全部权限指令
 * 用法：v-permission-all="['testcase_manage', 'test_execute']"
 */
export const permissionAllDirective = {
  mounted(el, binding) {
    checkAllPermissions(el, binding)
  },
  updated(el, binding) {
    checkAllPermissions(el, binding)
  }
}

export function setupPermissionDirectives(app) {
  app.directive('permission', permissionDirective)
  app.directive('role', roleDirective)
  app.directive('admin', adminDirective)
  app.directive('system-permission', systemPermissionDirective)
  app.directive('permission-all', permissionAllDirective)
}
