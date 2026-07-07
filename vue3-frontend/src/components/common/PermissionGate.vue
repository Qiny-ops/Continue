<template>
  <slot v-if="hasPermission" />
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '@/stores/modules/user'
import { usePermission } from '@/composables/permission/usePermission'

const props = defineProps({
  // 单个权限代码
  permission: { type: String, default: null },
  // 多个权限代码数组
  permissions: { type: Array, default: null },
  // 权限检查模式：'any' (任意一个) 或 'all' (全部)
  mode: { type: String, default: 'any' },
  // 系统权限检查
  systemPermission: { type: String, default: null },
  // 要求系统管理员
  requireSystemAdmin: { type: Boolean, default: false },
  // 要求项目管理员
  requireProjectAdmin: { type: Boolean, default: false },
  // 要求项目所有者
  requireProjectOwner: { type: Boolean, default: false }
})

const { checkPermission, checkPermissions, isSystemAdminUser, isProjectOwnerUser, isProjectAdminUser } = usePermission()
const userStore = useUserStore()

const hasPermission = computed(() => {
  // 系统管理员直接通过所有检查
  if (userStore.user?.system_role?.code === 'admin') {
    return true
  }

  // 系统管理员检查
  if (props.requireSystemAdmin) {
    return isSystemAdminUser.value
  }

  // 系统权限检查 - 真正匹配权限代码
  if (props.systemPermission) {
    const systemPermissions = userStore.systemPermissions || []
    return systemPermissions.includes(props.systemPermission)
  }

  // 项目所有者检查
  if (props.requireProjectOwner) {
    return isProjectOwnerUser.value
  }

  // 项目管理员检查
  if (props.requireProjectAdmin) {
    return isProjectAdminUser.value || isProjectOwnerUser.value
  }

  // 单个权限检查
  if (props.permission) {
    return checkPermission(props.permission)
  }

  // 多个权限检查
  if (props.permissions && props.permissions.length > 0) {
    return checkPermissions(props.permissions, props.mode)
  }

  // 默认允许显示
  return true
})
</script>
