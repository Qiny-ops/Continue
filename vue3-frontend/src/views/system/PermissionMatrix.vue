<template>
  <div class="matrix-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">权限矩阵</h1>
        </div>
      </div>
    </header>

    <main class="page-content" v-loading="loading">
      <div class="matrix-section">
        <div class="section-header">
          <div class="section-title">系统角色权限矩阵</div>
          <div class="section-desc">系统角色控制用户在平台全局的权限，由系统管理员配置</div>
        </div>

        <el-table :data="systemRoleTableData" style="width: 100%" :show-header="true">
          <el-table-column prop="name" label="角色" width="160" fixed>
            <template #default="{ row }">
              <div class="role-cell">
                <el-tag :type="row.code === 'admin' ? 'danger' : 'info'" size="default">
                  {{ row.name }}
                </el-tag>
                <span class="role-code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column v-for="perm in systemPermissions" :key="perm.code" :label="perm.name" min-width="100" align="center">
            <template #header>
              <div class="perm-header">
                <span class="perm-title">{{ perm.name }}</span>
              </div>
            </template>
            <template #default="{ row }">
              <el-icon v-if="row.permissions.includes(perm.code)" class="status-icon success">
                <CircleCheckFilled />
              </el-icon>
              <el-icon v-else class="status-icon disabled">
                <CircleCloseFilled />
              </el-icon>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 图例 -->
      <div class="legend-bar">
        <div class="legend-item">
          <el-icon class="status-icon success"><CircleCheckFilled /></el-icon>
          <span>拥有权限</span>
        </div>
        <div class="legend-item">
          <el-icon class="status-icon disabled"><CircleCloseFilled /></el-icon>
          <span>无权限</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import authApi from '@/api/modules/auth'

const loading = ref(false)
const systemPermissions = ref([])
const systemRoles = ref([])

// 系统角色表格数据（行）
const systemRoleTableData = computed(() => {
  return systemRoles.value.map(role => ({
    code: role.code,
    name: role.name,
    permissions: role.permissions || []
  }))
})

const loadPermissionData = async () => {
  loading.value = true
  try {
    // 获取权限信息
    const infoResponse = await authApi.getPermissionInfo()
    const systemPerms = infoResponse?.data?.system_permissions || []

    // 转换为统一格式
    systemPermissions.value = systemPerms.map(p => ({
      code: p.code,
      name: p.name
    }))

    // 获取角色列表及权限
    const rolesResponse = await authApi.getRoles()
    const roles = rolesResponse?.data?.roles || []

    // 只显示系统角色
    systemRoles.value = roles.filter(r => r.is_system).map(role => ({
      code: role.code,
      name: role.name,
      permissions: role.permissions || []
    }))
  } catch (error) {
    ElMessage.error(error.message || '获取权限信息失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPermissionData()
})
</script>

<style scoped>
.matrix-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.page-header {
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.matrix-section {
  background: #fff;
  border-radius: 4px;
  border: 1px solid var(--color-border-primary);
}

.section-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px 0;
}

.section-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
}

.role-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.role-code {
  font-size: 11px;
  color: var(--color-text-tertiary);
  font-family: monospace;
}

.perm-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.perm-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  text-align: center;
}

.status-icon {
  font-size: 16px;
}

.status-icon.success {
  color: var(--color-success);
}

.status-icon.disabled {
  color: var(--color-text-placeholder);
}

.legend-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 20px;
  margin-top: 16px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid var(--color-border-primary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 表格样式 */
.matrix-section :deep(.el-table) {
  border-radius: 0 0 4px 4px;
}

.matrix-section :deep(.el-table__header th) {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 500;
  font-size: 12px;
  padding: 12px 0;
}

.matrix-section :deep(.el-table__header th:first-child) {
  font-size: 13px;
  font-weight: 600;
}

.matrix-section :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.matrix-section :deep(.el-table__row:hover > td) {
  background: var(--color-bg-secondary) !important;
}

.matrix-section :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

@media (max-width: 768px) {
  .page-content {
    padding: 12px 16px;
  }

  .header-content {
    padding: 0 16px;
  }
}
</style>
