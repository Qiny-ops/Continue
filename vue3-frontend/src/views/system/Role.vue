<template>
  <div class="role-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">角色管理</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
        </div>
      </div>
      <div class="filter-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索角色名称或代码"
          clearable
          style="width: 240px;"
          @input="handleFilter"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </header>

    <main class="page-content">
      <el-table :data="filteredRoles" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="角色名称" min-width="120">
          <template #default="{ row }">
            <div class="role-name">
              <el-tag :type="getRoleTagType(row.code)" size="default">
                {{ row.name }}
              </el-tag>
              <span v-if="row.is_system" class="system-badge">系统</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="角色代码" min-width="120">
          <template #default="{ row }">
            <code class="code-text">{{ row.code }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="user_count" label="用户数" width="100" align="center">
          <template #default="{ row }">
            <span class="user-count">{{ row.user_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="info" size="small" @click="handlePermissions(row)">权限</el-button>
            <el-button
              v-if="!row.is_system"
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </main>

    <!-- 编辑角色对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑角色' : '新增角色'"
      width="500px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色代码" prop="code">
          <el-input v-model="form.code" placeholder="请输入角色代码（英文）" :disabled="isEditing" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入角色描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限配置"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="permission-header">
        <span class="role-label">角色：</span>
        <el-tag :type="getRoleTagType(currentRole?.code)" size="default">
          {{ currentRole?.name }}
        </el-tag>
      </div>
      <div class="permission-groups">
        <div v-for="group in permissionGroups" :key="group.key" class="permission-group">
          <div class="group-header">
            <el-checkbox
              v-model="group.checked"
              :indeterminate="group.indeterminate"
              @change="handleGroupChange(group)"
            >
              {{ group.name }}
            </el-checkbox>
          </div>
          <div class="group-items">
            <el-checkbox
              v-for="perm in group.permissions"
              :key="perm.code"
              v-model="perm.checked"
              @change="handlePermissionChange(group)"
            >
              {{ perm.name }}
            </el-checkbox>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSavePermissions" :loading="savingPermissions">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import authApi from '@/api/modules/auth'

const loading = ref(false)
const submitting = ref(false)
const savingPermissions = ref(false)
const dialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const roles = ref([])
const searchKeyword = ref('')
const currentRole = ref(null)
const permissionGroups = ref([])

const form = reactive({
  name: '',
  code: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入角色代码', trigger: 'blur' },
    { pattern: /^[a-z_]+$/, message: '角色代码只能包含小写字母和下划线', trigger: 'blur' }
  ]
}

const filteredRoles = computed(() => {
  if (!searchKeyword.value) return roles.value

  const keyword = searchKeyword.value.toLowerCase()
  return roles.value.filter(r =>
    r.name?.toLowerCase().includes(keyword) ||
    r.code?.toLowerCase().includes(keyword)
  )
})

const getRoleTagType = (code) => {
  const types = {
    admin: 'danger',
    user: 'info'
  }
  return types[code] || 'primary'
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const loadRoles = async () => {
  loading.value = true
  try {
    const response = await authApi.getRoles()
    roles.value = response?.data?.roles || []
  } catch (error) {
    ElMessage.error(error.message || '获取角色列表失败')
    roles.value = []
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {}

const handleAdd = () => {
  isEditing.value = false
  editingId.value = null
  form.name = ''
  form.code = ''
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEditing.value = true
  editingId.value = row.id
  form.name = row.name
  form.code = row.code
  form.description = row.description || ''
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色"${row.name}"吗？`, '删除确认', {
      type: 'warning'
    })

    await authApi.deleteRole(row.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEditing.value) {
      await authApi.updateRole(editingId.value, {
        name: form.name,
        description: form.description
      })
      ElMessage.success('更新成功')
    } else {
      await authApi.createRole({
        name: form.name,
        code: form.code,
        description: form.description
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadRoles()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handlePermissions = async (row) => {
  currentRole.value = row
  await loadRolePermissions(row.id)
  permissionDialogVisible.value = true
}

const loadRolePermissions = async (roleId) => {
  // 从后端 API 获取权限列表
  try {
    // 获取权限体系信息
    const infoResponse = await authApi.getPermissionInfo()
    const systemPerms = infoResponse?.data?.system_permissions || []
    const projectPerms = infoResponse?.data?.project_permissions || []

    // 构建权限分组
    permissionGroups.value = []

    // 系统权限分组
    if (systemPerms.length > 0) {
      permissionGroups.value.push({
        key: 'system',
        name: '系统权限',
        checked: false,
        indeterminate: false,
        permissions: systemPerms.map(p => ({
          code: p.code,
          name: p.name,
          checked: false
        }))
      })
    }

    // 项目权限分组（按功能模块分组）
    if (projectPerms.length > 0) {
      // 定义分组映射
      const groupMapping = {
        'project': '项目管理',
        'member': '成员管理',
        'testcase': '测试用例',
        'apitest': '接口测试',
        'knowledge': '知识库',
        'bug': '缺陷管理',
        'report': '报告中心',
        'settings': '设置管理',
        'test': '测试执行',
      }

      // 按分组整理权限
      const groupedPerms = {}
      projectPerms.forEach(p => {
        let groupKey = 'other'
        for (const key of Object.keys(groupMapping)) {
          if (p.code.includes(key)) {
            groupKey = key
            break
          }
        }
        if (!groupedPerms[groupKey]) {
          groupedPerms[groupKey] = {
            key: groupKey,
            name: groupMapping[groupKey] || '其他',
            checked: false,
            indeterminate: false,
            permissions: []
          }
        }
        groupedPerms[groupKey].permissions.push({
          code: p.code,
          name: p.name,
          checked: false
        })
      })

      // 添加到权限分组列表
      Object.values(groupedPerms).forEach(group => {
        if (group.permissions.length > 0) {
          permissionGroups.value.push(group)
        }
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '获取权限信息失败')
    permissionGroups.value = []
  }

  // 加载角色当前权限
  try {
    const response = await authApi.getRolePermissions(roleId)
    const rolePermissions = response?.data?.permissions || []

    permissionGroups.value.forEach(group => {
      group.permissions.forEach(perm => {
        perm.checked = rolePermissions.includes(perm.code)
      })
      updateGroupStatus(group)
    })
  } catch (error) {
    ElMessage.error(error.message || '获取角色权限失败')
  }
}

const updateGroupStatus = (group) => {
  const checkedCount = group.permissions.filter(p => p.checked).length
  group.checked = checkedCount === group.permissions.length
  group.indeterminate = checkedCount > 0 && checkedCount < group.permissions.length
}

const handleGroupChange = (group) => {
  group.permissions.forEach(perm => {
    perm.checked = group.checked
  })
  group.indeterminate = false
}

const handlePermissionChange = (group) => {
  updateGroupStatus(group)
}

const handleSavePermissions = async () => {
  savingPermissions.value = true

  const permissions = []
  permissionGroups.value.forEach(group => {
    group.permissions.forEach(perm => {
      if (perm.checked) {
        permissions.push(perm.code)
      }
    })
  })

  try {
    await authApi.updateRolePermissions(currentRole.value.id, { permissions })
    ElMessage.success('权限配置成功')
    permissionDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '权限配置失败')
  } finally {
    savingPermissions.value = false
  }
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.role-page {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border-secondary);
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.role-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.system-badge {
  font-size: 11px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 1px 6px;
  border-radius: 2px;
}

.code-text {
  font-family: monospace;
  font-size: 12px;
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 2px;
  color: var(--color-text-secondary);
}

.user-count {
  font-weight: 500;
  color: var(--color-primary);
}

.permission-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-primary);
}

.role-label {
  font-weight: 500;
  color: var(--color-text-secondary);
}

.permission-groups {
  max-height: 400px;
  overflow-y: auto;
}

.permission-group {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.group-header {
  margin-bottom: 10px;
  font-weight: 500;
}

.group-items {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-left: 24px;
}
</style>
