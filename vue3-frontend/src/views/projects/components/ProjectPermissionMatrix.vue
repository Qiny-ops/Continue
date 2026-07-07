<template>
  <div class="project-permission-matrix">
    <div class="matrix-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="header-info">
          <h3 class="matrix-title">项目角色权限矩阵</h3>
          <p class="matrix-desc">点击单元格切换权限，管理员可自定义修改</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button v-if="hasChanges" size="small" @click="resetChanges">
          重置
        </el-button>
        <el-button v-if="hasChanges" type="primary" size="small" :loading="saving" @click="saveChanges">
          保存修改
        </el-button>
      </div>
    </div>

    <div class="matrix-body" v-loading="loading">
      <div class="matrix-table-wrapper">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="col-role">角色</th>
              <th v-for="perm in projectPermissions" :key="perm.code" class="col-perm">
                {{ perm.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in roleData" :key="row.key">
              <td class="col-role">
                <div class="role-cell">
                  <div class="role-icon" :style="{ background: getRoleColor(row.key) }">
                    <el-icon><UserFilled /></el-icon>
                  </div>
                  <div class="role-info">
                    <span class="role-name">{{ row.name }}</span>
                    <span class="role-count">{{ row.memberCount }} 人</span>
                  </div>
                </div>
              </td>
              <td
                v-for="perm in projectPermissions"
                :key="perm.code"
                class="col-perm"
                :class="{ clickable: canManage && row.key !== 'admin' }"
                @click="canManage && row.key !== 'admin' && togglePermission(row.key, perm.code)"
              >
                <div class="perm-cell">
                  <el-checkbox
                    v-if="canManage && row.key !== 'admin'"
                    :model-value="row.permissions.includes(perm.code)"
                    :disabled="row.key === 'admin'"
                    @click.stop
                    @change="togglePermission(row.key, perm.code)"
                  />
                  <template v-else>
                    <el-icon v-if="row.permissions.includes(perm.code)" class="status-icon success">
                      <CircleCheckFilled />
                    </el-icon>
                    <span v-else class="status-dot disabled"></span>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="matrix-footer">
      <div class="footer-tip" v-if="canManage">
        <el-icon><InfoFilled /></el-icon>
        <span>管理员角色默认拥有所有权限，不可修改</span>
      </div>
      <div class="legend">
        <span class="legend-item">
          <el-icon class="status-icon success"><CircleCheckFilled /></el-icon>
          拥有权限
        </span>
        <span class="legend-item">
          <span class="status-dot disabled"></span>
          无权限
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, Grid, UserFilled, InfoFilled } from '@element-plus/icons-vue'
import { usePermissionStore } from '@/stores/modules/permission'
import { useMemberStore } from '@/stores/modules/member'
import { usePermission } from '@/composables/permission/usePermission'
import { PERMISSION_NAMES, DEFAULT_ROLE_PERMISSIONS, ROLE_NAMES, ROLE_COLORS } from '@/constants/permissions'
import memberApi from '@/api/modules/member.js'

const props = defineProps({
  projectId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['updated'])

const permissionStore = usePermissionStore()
const memberStore = useMemberStore()
const { isProjectAdminUser } = usePermission()

const loading = ref(false)
const saving = ref(false)
const allPermissions = ref([])
const originalRoleData = ref({})
const roleData = ref([])

const canManage = computed(() => isProjectAdminUser.value)

// 项目权限列表（列）- 从后端获取
const projectPermissions = computed(() => {
  if (allPermissions.value.length > 0) {
    return allPermissions.value.map(code => ({
      code,
      name: PERMISSION_NAMES[code] || code
    }))
  }
  return Object.entries(PERMISSION_NAMES).map(([code, name]) => ({ code, name }))
})

// 检测是否有修改
const hasChanges = computed(() => {
  if (!roleData.value.length) return false

  for (const role of roleData.value) {
    const original = originalRoleData.value[role.key] || []
    if (JSON.stringify([...role.permissions].sort()) !== JSON.stringify([...original].sort())) {
      return true
    }
  }
  return false
})

// 获取角色颜色
const getRoleColor = (roleKey) => {
  return ROLE_COLORS[roleKey] || 'var(--color-text-tertiary)'
}

// 切换权限
const togglePermission = (roleKey, permCode) => {
  const role = roleData.value.find(r => r.key === roleKey)
  if (!role || roleKey === 'admin') return

  const index = role.permissions.indexOf(permCode)
  if (index > -1) {
    role.permissions.splice(index, 1)
  } else {
    role.permissions.push(permCode)
  }
}

// 重置修改
const resetChanges = () => {
  roleData.value.forEach(role => {
    role.permissions = [...(originalRoleData.value[role.key] || [])]
  })
}

// 保存修改
const saveChanges = async () => {
  saving.value = true
  try {
    // 保存每个角色的权限
    for (const role of roleData.value) {
      if (role.key === 'admin') continue

      await memberApi.updateRole(props.projectId, role.key, {
        permissions: role.permissions
      })

      // 更新原始数据
      originalRoleData.value[role.key] = [...role.permissions]
    }

    ElMessage.success('权限配置已保存')
    emit('updated')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const loadData = async () => {
  if (!props.projectId) return

  loading.value = true
  try {
    // 获取项目角色和所有可用权限
    const rolesResponse = await memberApi.getRoles(props.projectId)
    const rolesData = rolesResponse?.data || {}

    // 存储所有可用权限
    allPermissions.value = rolesData.all_permissions || []

    // 获取成员数量
    const memberCounts = {}
    if (memberStore.members && memberStore.members.length > 0) {
      memberStore.members.forEach(m => {
        const role = m.role || 'viewer'
        memberCounts[role] = (memberCounts[role] || 0) + 1
      })
    } else {
      await memberStore.fetchMembers(props.projectId)
      if (memberStore.members && memberStore.members.length > 0) {
        memberStore.members.forEach(m => {
          const role = m.role || 'viewer'
          memberCounts[role] = (memberCounts[role] || 0) + 1
        })
      }
    }

    // 构建角色数据
    const roleKeys = ['admin', 'developer', 'tester', 'viewer']
    const roles = rolesData.roles || []

    roleData.value = roleKeys.map(key => {
      const roleConfig = roles.find(r => r.key === key)
      let permissions = roleConfig?.permissions || DEFAULT_ROLE_PERMISSIONS[key] || []

      // admin 角色默认拥有所有权限
      if (key === 'admin' && permissions.length === 0) {
        permissions = allPermissions.value.length > 0 ? [...allPermissions.value] : [...DEFAULT_ROLE_PERMISSIONS[key]]
      }

      // 存储原始数据
      originalRoleData.value[key] = [...permissions]

      return {
        key,
        name: ROLE_NAMES[key] || key,
        memberCount: memberCounts[key] || 0,
        permissions: [...permissions]
      }
    })

    // 更新 permissionStore
    permissionStore.setProjectRoles(roles)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

watch(() => props.projectId, () => {
  loadData()
})
</script>

<style scoped>
.project-permission-matrix {
  background: #fff;
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-primary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  border-radius: 2px;
  color: var(--color-primary);
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.matrix-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.matrix-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.matrix-body {
  padding: 0;
}

.matrix-table-wrapper {
  overflow-x: auto;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.matrix-table thead th {
  background: var(--color-bg-secondary);
  padding: 12px 16px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-primary);
  white-space: nowrap;
}

.matrix-table thead th.col-role {
  text-align: left;
  width: 140px;
  font-weight: 600;
}

.matrix-table thead th.col-perm {
  min-width: 90px;
}

.matrix-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-primary);
  text-align: center;
}

.matrix-table tbody tr:last-child td {
  border-bottom: none;
}

.matrix-table tbody tr:hover {
  background: var(--color-bg-secondary);
}

.matrix-table tbody td.clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.matrix-table tbody td.clickable:hover {
  background: var(--color-bg-tertiary);
}

.role-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  color: #fff;
  flex-shrink: 0;
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.role-count {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.perm-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon {
  font-size: 16px;
}

.status-icon.success {
  color: var(--color-success);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border-primary);
}

.matrix-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.footer-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.legend {
  display: flex;
  align-items: center;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .matrix-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .matrix-table thead th.col-role {
    width: 100px;
  }
}
</style>
