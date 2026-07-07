import { PERMISSIONS, DEFAULT_ROLE_PERMISSIONS, SYSTEM_ROLES, ROLE_KEYS } from '@/constants/permissions'

export function hasPermission(userPermissions, requiredPermission) {
  if (!userPermissions || !Array.isArray(userPermissions)) {
    return false
  }
  
  if (Array.isArray(requiredPermission)) {
    return requiredPermission.some(perm => userPermissions.includes(perm))
  }
  
  return userPermissions.includes(requiredPermission)
}

export function hasAllPermissions(userPermissions, requiredPermissions) {
  if (!userPermissions || !Array.isArray(userPermissions)) {
    return false
  }
  
  if (!Array.isArray(requiredPermissions)) {
    return false
  }
  
  return requiredPermissions.every(perm => userPermissions.includes(perm))
}

export function isSystemAdmin(user) {
  if (!user) return false
  return user.system_role === SYSTEM_ROLES.ADMIN
}

export function isProjectOwner(project, user) {
  if (!project || !user) return false
  return project.owner === user.username || 
         project.owner_id === user.id ||
         project.owner?.id === user.id
}

export function isProjectAdmin(member) {
  if (!member) return false
  return member.role === ROLE_KEYS.ADMIN
}

export function canManageProject(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  if (member && isProjectAdmin(member)) return true
  return false
}

export function canManageMembers(project, user, member) {
  return canManageProject(project, user, member)
}

export function canManageTestCases(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  
  if (member) {
    const permissions = member.permissions || DEFAULT_ROLE_PERMISSIONS[member.role] || []
    return hasPermission(permissions, PERMISSIONS.TESTCASE_MANAGE)
  }
  
  return false
}

export function canViewTestCases(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  
  if (member) {
    const permissions = member.permissions || DEFAULT_ROLE_PERMISSIONS[member.role] || []
    return hasPermission(permissions, [PERMISSIONS.TESTCASE_VIEW, PERMISSIONS.TESTCASE_MANAGE])
  }
  
  return false
}

export function canExecuteTests(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  
  if (member) {
    const permissions = member.permissions || DEFAULT_ROLE_PERMISSIONS[member.role] || []
    return hasPermission(permissions, PERMISSIONS.TEST_EXECUTE)
  }
  
  return false
}

export function canViewReports(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  
  if (member) {
    const permissions = member.permissions || DEFAULT_ROLE_PERMISSIONS[member.role] || []
    return hasPermission(permissions, PERMISSIONS.REPORT_VIEW)
  }
  
  return false
}

export function canManageSettings(project, user, member) {
  if (isSystemAdmin(user)) return true
  if (isProjectOwner(project, user)) return true
  
  if (member) {
    const permissions = member.permissions || DEFAULT_ROLE_PERMISSIONS[member.role] || []
    return hasPermission(permissions, PERMISSIONS.SETTINGS_MANAGE)
  }
  
  return false
}

export function getPermissionsByRole(roleKey) {
  return DEFAULT_ROLE_PERMISSIONS[roleKey] || []
}

export function getMemberPermissions(member, projectRoles = []) {
  if (!member) return []
  
  if (member.permissions && Array.isArray(member.permissions)) {
    return member.permissions
  }
  
  const roleConfig = projectRoles.find(r => r.key === member.role)
  if (roleConfig && roleConfig.permissions) {
    return roleConfig.permissions
  }
  
  return getPermissionsByRole(member.role)
}
