<template>
  <div class="user-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">用户管理</h1>
        </div>
        <div class="header-right">
          <el-button
            type="danger"
            :disabled="selectedUsers.length === 0"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            批量删除 {{ selectedUsers.length > 0 ? `(${selectedUsers.length})` : '' }}
          </el-button>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </div>
      <div class="filter-bar">
        <el-select v-model="filterRole" placeholder="用户角色" clearable style="width: 140px;" @change="handleFilter">
          <el-option label="全部角色" value="" />
          <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="用户状态" clearable style="width: 120px;" @change="handleFilter">
          <el-option label="全部状态" value="" />
          <el-option label="正常" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名、姓名、邮箱"
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
      <el-table :data="filteredUsers" style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="real_name" label="姓名" min-width="100">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="28" :src="row.avatar">
                {{ (row.real_name || row.name || row.username)?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">{{ row.real_name || row.name || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" min-width="80" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column prop="system_role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.system_role)" size="small">
              {{ getRoleName(row.system_role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </main>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑用户' : '新增用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :disabled="isEditing" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item v-if="!isEditing" label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="system_role">
          <el-select v-model="form.system_role" placeholder="请选择角色" style="width: 100%;">
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.code" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isEditing" label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio value="active">正常</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import authApi from '@/api/modules/auth'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const users = ref([])
const roles = ref([])
const selectedUsers = ref([])
const filterRole = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 保存原始数据，用于判断是否有变化
const originalData = ref({
  status: '',
  system_role: ''
})

const form = reactive({
  username: '',
  real_name: '',
  email: '',
  phone: '',
  password: '',
  system_role: 'user',
  status: 'active'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const filteredUsers = computed(() => {
  let result = users.value

  if (filterStatus.value) {
    result = result.filter(u => u.status === filterStatus.value)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(u =>
      u.username?.toLowerCase().includes(keyword) ||
      u.real_name?.toLowerCase().includes(keyword) ||
      u.name?.toLowerCase().includes(keyword) ||
      u.email?.toLowerCase().includes(keyword)
    )
  }

  return result
})

const roleMap = {
  admin: '系统管理员',
  tester: '测试人员',
  developer: '开发人员',
  viewer: '访客'
}

const getRoleName = (role) => roleMap[role] || role || '未知'

const getRoleTagType = (role) => {
  const types = {
    admin: 'danger',
    tester: 'warning',
    developer: '',
    viewer: 'info'
  }
  return types[role] || 'info'
}

const getStatusName = (status) => {
  const names = {
    active: '正常',
    disabled: '禁用'
  }
  return names[status] || status
}

const getStatusTagType = (status) => {
  const types = {
    active: 'success',
    disabled: 'danger'
  }
  return types[status] || 'info'
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await authApi.getUsers({
      page: currentPage.value,
      page_size: pageSize.value
    })
    users.value = response?.data?.users || response?.data || []
    total.value = response?.data?.total || users.value.length
  } catch {
    users.value = []
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const response = await authApi.getRoles()
    roles.value = response?.data?.roles || [
      { id: 1, code: 'admin', name: '系统管理员' },
      { id: 2, code: 'tester', name: '测试人员' },
      { id: 3, code: 'developer', name: '开发人员' },
      { id: 4, code: 'viewer', name: '访客' }
    ]
  } catch {
    roles.value = [
      { id: 1, code: 'admin', name: '系统管理员' },
      { id: 2, code: 'tester', name: '测试人员' },
      { id: 3, code: 'developer', name: '开发人员' },
      { id: 4, code: 'viewer', name: '访客' }
    ]
  }
}

const handleFilter = () => {}

const handleAdd = () => {
  isEditing.value = false
  editingId.value = null
  form.username = ''
  form.real_name = ''
  form.email = ''
  form.phone = ''
  form.password = ''
  form.system_role = 'user'
  form.status = 'active'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEditing.value = true
  editingId.value = row.id
  form.username = row.username
  form.real_name = row.real_name || row.name || ''
  form.email = row.email
  form.phone = row.phone || ''
  form.system_role = row.system_role || 'user'
  form.status = row.status
  // 保存原始数据
  originalData.value = {
    status: row.status,
    system_role: row.system_role || 'user'
  }
  dialogVisible.value = true
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const actionText = newStatus === 'disabled' ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(`确定要${actionText}用户"${row.username}"吗？`, '确认操作', {
      type: 'warning'
    })

    await authApi.updateUserStatus(row.id, newStatus)
    ElMessage.success(`${actionText}成功`)
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户"${row.username}"吗？`, '删除确认', {
      type: 'warning'
    })

    await authApi.deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const handleBatchDelete = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请选择要删除的用户')
    return
  }

  const userIds = selectedUsers.value.map(u => u.id)
  const usernames = selectedUsers.value.map(u => u.username).join('、')

  try {
    await ElMessageBox.confirm(
      `确定要删除以下 ${selectedUsers.value.length} 个用户吗？\n${usernames}`,
      '批量删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const response = await authApi.batchDeleteUsers(userIds)
    const { deleted_count, failed_users } = response.data || {}

    if (failed_users && failed_users.length > 0) {
      const failedMsg = failed_users.map(f => `${f.username || f.id}: ${f.reason}`).join('\n')
      ElMessage.warning(`成功删除 ${deleted_count} 个用户，${failed_users.length} 个失败\n${failedMsg}`)
    } else {
      ElMessage.success(`成功删除 ${deleted_count} 个用户`)
    }

    selectedUsers.value = []
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量删除失败')
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
      // 更新基本信息（name, phone）
      await authApi.updateUser(editingId.value, {
        name: form.real_name,
        phone: form.phone
      })
      // 只有状态变化时才更新
      if (form.status !== originalData.value.status) {
        await authApi.updateUserStatus(editingId.value, form.status)
      }
      // 只有角色变化时才更新
      if (form.system_role !== originalData.value.system_role) {
        await authApi.updateUserRole(editingId.value, form.system_role)
      }
      ElMessage.success('更新成功')
    } else {
      await authApi.register({
        username: form.username,
        name: form.real_name,
        email: form.email,
        phone: form.phone,
        password: form.password,
        system_role: form.system_role
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped>
.user-page {
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

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-info .el-avatar {
  flex-shrink: 0;
}

.username {
  font-weight: 500;
}

.pagination-wrapper {
  padding: 16px 0;
  display: flex;
  justify-content: flex-end;
}
</style>
