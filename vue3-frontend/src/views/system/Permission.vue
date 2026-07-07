<template>
  <div class="permission-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">权限管理</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="goToMatrix">
            <el-icon><Grid /></el-icon>
            查看权限矩阵
          </el-button>
        </div>
      </div>
    </header>

    <main class="page-content">
      <div class="info-banner">
        <el-alert
          title="权限说明"
          type="info"
          :closable="false"
          show-icon
        >
          系统权限用于控制系统级功能的访问，项目权限用于项目角色权限分配。admin 角色默认拥有所有权限。
        </el-alert>
      </div>

      <!-- 系统权限 -->
      <div class="permission-section">
        <h2 class="section-title">系统权限</h2>
        <div class="permission-groups">
          <div class="permission-group">
            <div class="group-header">
              <h3 class="group-title">全部系统权限</h3>
              <span class="group-count">{{ systemPermissions.length }} 个权限</span>
            </div>
            <div class="permission-list">
              <div v-for="permission in systemPermissions" :key="permission.code" class="permission-item">
                <div class="permission-info">
                  <span class="permission-name">{{ permission.name }}</span>
                  <code class="permission-code">{{ permission.code }}</code>
                </div>
                <el-tag type="success" size="small">可用</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 项目权限 -->
      <div class="permission-section">
        <h2 class="section-title">项目权限</h2>
        <div class="permission-groups">
          <div v-for="group in projectPermissionGroups" :key="group.key" class="permission-group">
            <div class="group-header">
              <h3 class="group-title">{{ group.name }}</h3>
              <span class="group-count">{{ group.permissions.length }} 个权限</span>
            </div>
            <div class="permission-list">
              <div v-for="permission in group.permissions" :key="permission.code" class="permission-item">
                <div class="permission-info">
                  <span class="permission-name">{{ permission.name }}</span>
                  <code class="permission-code">{{ permission.code }}</code>
                </div>
                <el-tag type="success" size="small">可用</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Grid } from '@element-plus/icons-vue'
import authApi from '@/api/modules/auth'

const router = useRouter()

const loading = ref(false)
const systemPermissions = ref([])
const projectPermissions = ref([])

const goToMatrix = () => {
  router.push('/system/permission-matrix')
}

// 按分组整理项目权限
const projectPermissionGroups = computed(() => {
  const groupNames = {
    'project': '项目管理',
    'member': '成员管理',
    'testcase': '测试用例',
    'api': '接口管理',
    'bug': '缺陷管理',
    'report': '报告中心',
    'settings': '设置管理',
    'test': '测试执行',
  }

  const groups = {}
  projectPermissions.value.forEach(p => {
    let groupKey = 'other'
    for (const key of Object.keys(groupNames)) {
      if (p.code.includes(key)) {
        groupKey = key
        break
      }
    }
    if (!groups[groupKey]) {
      groups[groupKey] = {
        key: groupKey,
        name: groupNames[groupKey] || '其他',
        permissions: []
      }
    }
    groups[groupKey].permissions.push(p)
  })

  return Object.values(groups)
})

const loadPermissions = async () => {
  loading.value = true
  try {
    const response = await authApi.getPermissionInfo()
    const systemPerms = response?.data?.system_permissions || []
    const projectPerms = response?.data?.project_permissions || []

    // 转换为统一格式
    systemPermissions.value = systemPerms.map(p => ({
      code: p.code,
      name: p.name
    }))
    projectPermissions.value = projectPerms.map(p => ({
      code: p.code,
      name: p.name
    }))
  } catch (error) {
    ElMessage.error(error.message || '获取权限信息失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.permission-page {
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
}

.header-right {
  display: flex;
  align-items: center;
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

.info-banner {
  margin-bottom: 16px;
}

.permission-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-primary);
}

.permission-groups {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.permission-group {
  background: #fff;
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
  overflow: hidden;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.group-count {
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-border-primary);
  padding: 2px 8px;
  border-radius: 2px;
}

.permission-list {
  padding: 8px 16px;
}

.permission-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-bg-secondary);
}

.permission-item:last-child {
  border-bottom: none;
}

.permission-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.permission-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.permission-code {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  padding: 1px 6px;
  border-radius: 2px;
}

@media (max-width: 768px) {
  .permission-groups {
    grid-template-columns: 1fr;
  }
}
</style>
