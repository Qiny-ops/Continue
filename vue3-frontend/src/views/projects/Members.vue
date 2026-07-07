<template>
  <div class="project-members">
    <div class="top-nav-bar">
      <div
        v-for="nav in navigationItems"
        :key="nav.key"
        :class="['nav-item', { active: activeNav === nav.key }]"
        @click="activeNav = nav.key"
      >
        <div class="nav-item-content">
          <span class="nav-label">{{ nav.label }}</span>
          <span v-if="nav.count !== undefined" class="nav-count">{{ nav.count }}</span>
        </div>
      </div>
    </div>

    <div class="member-content">
      <div v-if="activeNav === 'all'" class="member-section">
        <div class="section-header">
          <div class="header-left">
            <h2 class="section-title">成员管理</h2>
            <p class="section-description">管理项目成员，设置角色和权限</p>
          </div>
          <div class="header-actions">
            <el-button v-if="canManageMembers" type="primary" @click="handleAddMember">
              <el-icon><Plus /></el-icon>
              添加成员
            </el-button>
          </div>
        </div>

        <div class="filter-section">
          <div class="filter-row">
            <div class="filter-item search-item">
              <el-input
                v-model="searchQuery"
                placeholder="搜索成员姓名或邮箱"
                :prefix-icon="Search"
                clearable
                @clear="handleSearchClear"
              />
            </div>
            <div class="filter-item">
              <el-select v-model="filterRole" placeholder="全部角色" clearable>
                <el-option label="管理员" value="admin" />
                <el-option label="开发人员" value="developer" />
                <el-option label="测试人员" value="tester" />
                <el-option label="观察者" value="viewer" />
              </el-select>
            </div>
            <div class="filter-item">
              <el-select v-model="filterStatus" placeholder="全部状态" clearable>
                <el-option label="活跃" value="active" />
                <el-option label="已禁用" value="disabled" />
              </el-select>
            </div>
          </div>
        </div>

        <div v-if="selectedMembers.length > 0 && canManageMembers" class="batch-actions">
          <span class="batch-info">已选择 {{ selectedMembers.length }} 个成员</span>
          <div class="batch-buttons">
            <el-button type="primary" @click="handleBatchChangeRole">
              批量修改角色
            </el-button>
            <el-button type="danger" @click="handleBatchRemove">
              批量移除
            </el-button>
            <el-button @click="clearSelection">
              取消选择
            </el-button>
          </div>
        </div>

        <div class="members-table-wrapper">
          <el-table
            ref="memberTableRef"
            :data="paginatedMembers"
            style="width: 100%"
            empty-text="暂无成员数据"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" :selectable="canSelectRow" />
            <el-table-column label="成员" min-width="240">
              <template #default="{ row }">
                <div class="member-info">
                  <el-avatar :size="40" :src="row.avatar" class="member-avatar">
                    {{ row.name.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="member-details">
                    <div class="member-name">
                      {{ row.name }}
                      <el-tag v-if="row.isOwner" type="warning" size="small" class="owner-tag">创建者</el-tag>
                    </div>
                    <div class="member-email">{{ row.email }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="role" label="角色" width="140">
              <template #default="{ row }">
                <div class="role-cell">
                  <el-tag :type="getRoleType(row.role)" size="small" effect="light">
                    {{ getRoleText(row.role) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <div class="status-cell">
                  <span :class="['status-dot', row.status]"></span>
                  <span class="status-text">{{ getStatusText(row.status) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="joinDate" label="加入时间" width="140">
              <template #default="{ row }">
                <span class="date-text">{{ row.joinDate }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="lastActive" label="最后活跃" width="140">
              <template #default="{ row }">
                <span class="date-text">{{ row.lastActive || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons" v-if="!row.isOwner && canManageMembers">
                  <el-button link type="primary" size="small" @click="handleEditMember(row)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button link type="danger" size="small" @click="handleRemoveMember(row)">
                    <el-icon><Delete /></el-icon>
                    移除
                  </el-button>
                </div>
                <div class="action-buttons" v-else-if="!row.isOwner">
                  <span class="no-permission-hint">无权限</span>
                </div>
                <div class="action-buttons" v-else>
                  <span class="owner-hint">项目创建者</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="pagination-section">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredMembers.length"
            layout="total, sizes, prev, pager, next, jumper"
          />
        </div>
      </div>

      <div v-else-if="activeNav === 'roles'" class="member-section">
        <div class="section-header">
          <div class="header-left">
            <h2 class="section-title">角色管理</h2>
            <p class="section-description">配置项目角色和对应权限</p>
          </div>
          <div class="header-actions">
            <el-button v-if="isProjectAdminUser" type="primary" @click="handleAddRole">
              <el-icon><Plus /></el-icon>
              新建角色
            </el-button>
          </div>
        </div>

        <div class="roles-grid">
          <div v-for="role in roles" :key="role.key" class="role-card">
            <div class="role-header">
              <div class="role-icon" :style="{ background: role.color }">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="role-info">
                <h4 class="role-name">{{ role.name }}</h4>
                <span class="role-count">{{ role.memberCount }} 名成员</span>
              </div>
            </div>
            <div class="role-permissions">
              <div class="permission-title">权限范围</div>
              <div class="permission-list">
                <span v-for="perm in role.permissions.slice(0, 3)" :key="perm" class="permission-tag">
                  {{ getPermissionName(perm) }}
                </span>
                <span v-if="role.permissions.length > 3" class="permission-more">
                  +{{ role.permissions.length - 3 }} 项
                </span>
              </div>
            </div>
            <div class="role-actions">
              <el-button v-if="isProjectAdminUser" link type="primary" size="small" @click="handleEditRole(role)">
                编辑权限
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑成员' : '添加成员'"
      width="560px"
      class="member-dialog"
      :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <div v-if="!isEditing" class="mode-switch">
          <div
            :class="['mode-item', { active: addMode === 'select' }]"
            @click="switchMode('select')"
          >
            <el-icon><UserFilled /></el-icon>
            <span>从用户列表选择</span>
          </div>
          <div
            :class="['mode-item', { active: addMode === 'manual' }]"
            @click="switchMode('manual')"
          >
            <el-icon><Edit /></el-icon>
            <span>手动输入信息</span>
          </div>
        </div>

        <template v-if="isEditing">
          <div class="form-item">
            <div class="form-label">
              <span>成员信息</span>
            </div>
            <div class="member-display-card">
              <el-avatar :size="40" class="member-avatar-preview">
                {{ form.name.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="member-display-info">
                <span class="member-display-name">{{ form.name }}</span>
                <span class="member-display-email">{{ form.email }}</span>
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="addMode === 'select'">
          <div class="form-item">
            <div class="form-label">
              <span>选择用户</span>
              <span class="required">*</span>
            </div>
            <el-select
              v-model="form.userId"
              placeholder="搜索并选择用户"
              filterable
              :loading="usersLoading"
              size="large"
              style="width: 100%"
              @change="handleUserSelect"
            >
              <el-option
                v-for="user in availableUsers"
                :key="user.id"
                :label="user.name"
                :value="user.id"
              >
                <div class="user-option">
                  <el-avatar :size="28" :src="user.avatar" class="user-option-avatar">
                    {{ user.name.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div class="user-option-info">
                    <span class="user-option-name">{{ user.name }}</span>
                    <span class="user-option-email">{{ user.email }}</span>
                  </div>
                </div>
              </el-option>
            </el-select>
            <div v-if="form.userId" class="selected-user-preview">
              <el-avatar :size="32" class="preview-avatar">
                {{ selectedUser?.name?.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="preview-info">
                <span class="preview-name">{{ selectedUser?.name }}</span>
                <span class="preview-email">{{ selectedUser?.email }}</span>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="form-item">
            <div class="form-label">
              <span>姓名</span>
              <span class="required">*</span>
            </div>
            <el-input v-model="form.name" placeholder="请输入成员姓名" size="large" />
          </div>
          <div class="form-item">
            <div class="form-label">
              <span>邮箱</span>
              <span class="required">*</span>
            </div>
            <el-input v-model="form.email" placeholder="请输入成员邮箱" size="large" />
          </div>
        </template>

        <div class="form-item">
          <div class="form-label">
            <span>角色</span>
            <span class="required">*</span>
          </div>
          <el-select v-model="form.role" placeholder="请选择角色" size="large" style="width: 100%">
            <el-option label="管理员" value="admin">
              <div class="role-option">
                <span class="role-option-name">管理员</span>
                <span class="role-option-desc">拥有项目所有权限</span>
              </div>
            </el-option>
            <el-option label="开发人员" value="developer">
              <div class="role-option">
                <span class="role-option-name">开发人员</span>
                <span class="role-option-desc">可编辑测试用例和接口</span>
              </div>
            </el-option>
            <el-option label="测试人员" value="tester">
              <div class="role-option">
                <span class="role-option-name">测试人员</span>
                <span class="role-option-desc">可执行测试和提交缺陷</span>
              </div>
            </el-option>
            <el-option label="观察者" value="viewer">
              <div class="role-option">
                <span class="role-option-name">观察者</span>
                <span class="role-option-desc">只读权限</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <div class="form-item">
          <div class="form-label">
            <span>状态</span>
            <span class="required">*</span>
          </div>
          <el-select v-model="form.status" placeholder="请选择状态" size="large" style="width: 100%">
            <el-option label="活跃" value="active" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button size="large" @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" size="large" @click="handleSubmit" :loading="submitting">
            {{ isEditing ? '更新' : '添加' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="batchRoleDialogVisible"
      title="批量修改角色"
      width="420px"
      class="member-dialog"
      :close-on-click-modal="false"
    >
      <div class="dialog-content">
        <div class="batch-role-info">
          已选择 <strong>{{ selectedMembers.length }}</strong> 个成员
        </div>
        <div class="form-item">
          <div class="form-label">
            <span>新角色</span>
            <span class="required">*</span>
          </div>
          <el-select v-model="batchRole" placeholder="请选择角色" size="large" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="开发人员" value="developer" />
            <el-option label="测试人员" value="tester" />
            <el-option label="观察者" value="viewer" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button size="large" @click="batchRoleDialogVisible = false">取消</el-button>
          <el-button type="primary" size="large" @click="confirmBatchChangeRole" :disabled="!batchRole">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <RolePermissionDialog
      v-model="roleDialogVisible"
      :role="editingRole"
      :project-id="getProjectId()"
      @success="handleRoleUpdated"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Plus,
  UserFilled,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import { useMemberStore } from '@/stores/modules/member'
import { usePermissionStore } from '@/stores/modules/permission'
import { usePermission } from '@/composables/permission/usePermission'
import { getAvatarUrl } from '@/utils/avatar'
import { PERMISSION_NAMES, ROLE_COLORS, PERMISSIONS } from '@/constants/permissions'
import RolePermissionDialog from './components/RolePermissionDialog.vue'

const route = useRoute()
const memberStore = useMemberStore()
const permissionStore = usePermissionStore()
const { canManageMembers, isProjectAdminUser } = usePermission()

const activeNav = ref('all')
const searchQuery = ref('')
const filterRole = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingMemberId = ref(null)
const addMode = ref('select')
const usersLoading = ref(false)
const submitting = ref(false)
const allUsers = ref([])

const memberTableRef = ref(null)
const selectedMembers = ref([])
const batchRoleDialogVisible = ref(false)
const batchRole = ref('')

const roleDialogVisible = ref(false)
const editingRole = ref(null)

const form = reactive({
  userId: '',
  name: '',
  email: '',
  role: '',
  status: ''
})

const selectedUser = computed(() => {
  if (!form.userId) return null
  return allUsers.value.find(u => u.id === form.userId)
})

const availableUsers = computed(() => {
  const memberEmails = new Set(members.value.map(m => m.email.toLowerCase()))
  return allUsers.value.filter(user => !memberEmails.has(user.email.toLowerCase()))
})

const navigationItems = computed(() => [
  { key: 'all', label: '全部成员', count: memberStore.members.length },
  { key: 'roles', label: '角色管理' }
])

const members = computed(() => memberStore.members.map(m => ({
  id: m.id || m.user_id || m.userId,
  name: m.nickname || m.name || m.username,
  email: m.email,
  avatar: getAvatarUrl(m.avatar),
  role: m.role || 'viewer',
  status: m.status || (m.is_active ? 'active' : 'disabled'),
  joinDate: (m.joined_at || m.joinedAt) ? (m.joined_at || m.joinedAt).split('T')[0] : '-',
  lastActive: (m.last_active || m.lastActive) ? (m.last_active || m.lastActive).split('T')[0] : '-',
  isOwner: Boolean(m.isOwner || m.is_owner)
})))

const roles = computed(() => permissionStore.projectRoles.map(r => ({
  key: r.key,
  name: r.name || getRoleName(r.key),
  color: r.color || ROLE_COLORS[r.key] || 'var(--color-text-secondary)',
  memberCount: r.memberCount || 0,
  permissions: r.permissions || []
})))

const getRoleName = (key) => {
  const names = {
    admin: '管理员',
    developer: '开发人员',
    tester: '测试人员',
    viewer: '观察者'
  }
  return names[key] || key
}

const getPermissionName = (perm) => {
  return PERMISSION_NAMES[perm] || perm
}

const filteredMembers = computed(() => {
  return members.value.filter(member => {
    const matchesSearch = !searchQuery.value ||
      member.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      member.email.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesRole = !filterRole.value || member.role === filterRole.value
    const matchesStatus = !filterStatus.value || member.status === filterStatus.value

    return matchesSearch && matchesRole && matchesStatus
  })
})

const paginatedMembers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredMembers.value.slice(start, end)
})

const getRoleText = (role) => {
  const map = {
    admin: '管理员',
    developer: '开发人员',
    tester: '测试人员',
    viewer: '观察者'
  }
  return map[role] || role
}

const getRoleType = (role) => {
  const map = {
    admin: 'danger',
    developer: 'primary',
    tester: 'success',
    viewer: 'info'
  }
  return map[role] || ''
}

const getStatusText = (status) => {
  const map = {
    active: '活跃',
    disabled: '已禁用'
  }
  return map[status] || status
}

const handleSearchClear = () => {
  searchQuery.value = ''
}

const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const checkDuplicateEmail = (email, excludeId = null) => {
  return members.value.some(m =>
    m.email.toLowerCase() === email.toLowerCase() && m.id !== excludeId
  )
}

const handleAddMember = async () => {
  isEditing.value = false
  editingMemberId.value = null
  addMode.value = 'select'
  Object.assign(form, {
    userId: '',
    name: '',
    email: '',
    role: '',
    status: 'active'
  })
  
  if (allUsers.value.length === 0) {
    usersLoading.value = true
    try {
      allUsers.value = await memberStore.fetchUsers()
    } finally {
      usersLoading.value = false
    }
  }
  
  dialogVisible.value = true
}

const handleUserSelect = (userId) => {
  const user = allUsers.value.find(u => u.id === userId)
  if (user) {
    form.name = user.name
    form.email = user.email
  }
}

const switchMode = (mode) => {
  addMode.value = mode
  form.userId = ''
  form.name = ''
  form.email = ''
}

const handleEditMember = (member) => {
  isEditing.value = true
  editingMemberId.value = member.id
  Object.assign(form, {
    userId: member.id,
    name: member.name,
    email: member.email,
    role: member.role,
    status: member.status
  })
  dialogVisible.value = true
}

const handleRemoveMember = async (member) => {
  await ElMessageBox.confirm(
    `确定要移除成员"${member.name}"吗？此操作不可恢复。`,
    '确认移除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )

  const projectId = getProjectId()
  if (projectId) {
    try {
      await memberStore.removeMember(projectId, member.id)
      ElMessage.success('成员移除成功')
    } catch (error) {
      ElMessage.error(error.message || '移除成员失败')
    }
  }
}

const handleSubmit = async () => {
  if (!isEditing.value && addMode.value === 'select') {
    if (!form.userId) {
      ElMessage.warning('请选择用户')
      return
    }
  } else {
    if (!form.name || !form.name.trim()) {
      ElMessage.warning('请输入成员姓名')
      return
    }

    if (!form.email || !form.email.trim()) {
      ElMessage.warning('请输入成员邮箱')
      return
    }

    if (!validateEmail(form.email)) {
      ElMessage.warning('请输入有效的邮箱地址')
      return
    }

    if (!isEditing.value && checkDuplicateEmail(form.email)) {
      ElMessage.warning('该邮箱已存在于项目中')
      return
    }
  }

  if (!form.role) {
    ElMessage.warning('请选择成员角色')
    return
  }

  if (!form.status) {
    ElMessage.warning('请选择成员状态')
    return
  }

  const projectId = getProjectId()
  if (!projectId) {
    ElMessage.error('项目ID不存在')
    return
  }

  submitting.value = true
  try {
    if (isEditing.value) {
      await memberStore.updateMember(projectId, editingMemberId.value, {
        nickname: form.name,
        email: form.email,
        role: form.role,
        status: form.status
      })
      ElMessage.success('成员信息更新成功')
    } else {
      await memberStore.addMember(projectId, {
        user_id: form.userId,
        nickname: form.name,
        email: form.email,
        role: form.role,
        status: form.status
      })
      ElMessage.success('成员添加成功')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleAddRole = () => {
  editingRole.value = null
  roleDialogVisible.value = true
}

const handleEditRole = (role) => {
  editingRole.value = role
  roleDialogVisible.value = true
}

const handleRoleUpdated = async () => {
  const projectId = getProjectId()
  if (projectId) {
    await permissionStore.fetchProjectRoles(projectId)
  }
}

const canSelectRow = (row) => {
  return !row.isOwner
}

const handleSelectionChange = (selection) => {
  selectedMembers.value = selection
}

const clearSelection = () => {
  memberTableRef.value?.clearSelection()
}

const handleBatchChangeRole = () => {
  batchRole.value = ''
  batchRoleDialogVisible.value = true
}

const confirmBatchChangeRole = async () => {
  const projectId = getProjectId()
  if (!projectId) {
    ElMessage.error('项目ID不存在')
    return
  }

  const memberIds = selectedMembers.value.map(m => m.id)

  try {
    await memberStore.batchUpdateMembers(projectId, memberIds, { role: batchRole.value })
    ElMessage.success(`已成功修改 ${memberIds.length} 个成员的角色`)
    batchRoleDialogVisible.value = false
    clearSelection()
  } catch (error) {
    ElMessage.error(error.message || '批量修改角色失败')
  }
}

const handleBatchRemove = async () => {
  await ElMessageBox.confirm(
    `确定要移除选中的 ${selectedMembers.value.length} 个成员吗？此操作不可恢复。`,
    '批量移除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )

  const projectId = getProjectId()
  if (!projectId) {
    ElMessage.error('项目ID不存在')
    return
  }

  const memberIds = selectedMembers.value.map(m => m.id)
  const selectedCount = selectedMembers.value.length

  try {
    // 逐个调用移除API
    for (const memberId of memberIds) {
      await memberStore.removeMember(projectId, memberId)
    }
    ElMessage.success(`已成功移除 ${selectedCount} 个成员`)
    clearSelection()
  } catch (error) {
    ElMessage.error(error.message || '批量移除失败')
  }
}

const getProjectId = () => {
  return route.params.id || route.params.projectId || route.params.code || null
}

onMounted(async () => {
  const projectId = getProjectId()
  if (projectId) {
    await memberStore.fetchMembers(projectId)
    await permissionStore.initProjectPermissions(projectId)
  }
})
</script>

<style scoped>
.project-members {
  min-height: 100%;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid var(--color-border-primary);
  display: flex;
  flex-direction: column;
}

.top-nav-bar {
  display: flex;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
  padding: 0 24px;
  overflow-x: auto;
  overflow-y: hidden;
  flex-shrink: 0;
}

.top-nav-bar::-webkit-scrollbar {
  display: none;
}

.nav-item {
  position: relative;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-item:hover {
  background: var(--color-bg-tertiary);
}

.nav-item.active {
  background: #fff;
  border-bottom-color: var(--color-primary);
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.nav-item.active .nav-label {
  color: var(--color-primary);
  font-weight: 600;
}

.nav-count {
  background: var(--color-border-primary);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 2px;
  min-width: 20px;
  text-align: center;
}

.nav-item.active .nav-count {
  background: var(--color-primary);
  color: #fff;
}

.member-content {
  flex: 1;
  overflow: auto;
}

.member-section {
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border-primary);
}

.header-left {
  flex: 1;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.section-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-section {
  background: var(--color-bg-secondary);
  padding: 16px 20px;
  border-radius: 2px;
  margin-bottom: 20px;
  border: 1px solid var(--color-border-primary);
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
}

.filter-item.search-item {
  flex: 1;
  min-width: 280px;
  max-width: 400px;
}

.members-table-wrapper {
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  overflow: hidden;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-primary-light);
  border: 1px solid var(--color-primary);
  border-radius: 2px;
  padding: 12px 16px;
  margin-bottom: 16px;
}

.batch-info {
  font-size: 14px;
  color: var(--color-primary);
  font-weight: 500;
}

.batch-buttons {
  display: flex;
  gap: 8px;
}

.members-table-wrapper :deep(.el-table) {
  border: none;
}

.members-table-wrapper :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border-primary);
}

.members-table-wrapper :deep(.el-table__row) {
  font-size: 14px;
}

.members-table-wrapper :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.members-table-wrapper :deep(.el-table__row:hover > td) {
  background-color: var(--color-bg-secondary) !important;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-avatar {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  flex-shrink: 0;
}

.member-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-tag {
  font-size: 10px;
}

.member-email {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.role-cell {
  display: flex;
  align-items: center;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.active {
  background: var(--color-success);
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
}

.status-dot.disabled {
  background: var(--color-text-tertiary);
}

.status-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.date-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.owner-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.no-permission-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.pagination-section {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 0 0;
}

.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.role-card {
  background: #fff;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  padding: 20px;
  transition: all 0.2s ease;
}

.role-card:hover {
  border-color: var(--color-text-placeholder);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.role-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.role-icon {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.role-info {
  flex: 1;
}

.role-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px 0;
}

.role-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.role-permissions {
  margin-bottom: 16px;
}

.permission-title {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.permission-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.permission-tag {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
  padding: 4px 8px;
  border-radius: 2px;
}

.permission-more {
  font-size: 11px;
  color: var(--color-primary);
  padding: 4px 8px;
}

.role-actions {
  padding-top: 12px;
  border-top: 1px solid var(--color-bg-tertiary);
}

.member-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-primary);
  margin: 0;
}

.member-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.member-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mode-switch {
  display: flex;
  gap: 12px;
  padding: 4px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  margin-bottom: 8px;
}

.mode-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 2px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
  background: transparent;
}

.mode-item:hover {
  color: var(--color-text-primary);
}

.mode-item.active {
  background: #fff;
  color: var(--color-primary);
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.mode-item .el-icon {
  font-size: 16px;
}

.member-display-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
}

.member-avatar-preview {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  flex-shrink: 0;
}

.member-display-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-display-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.member-display-email {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.user-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.user-option-avatar {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  flex-shrink: 0;
}

.user-option-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-option-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.user-option-email {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.selected-user-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--color-primary-light);
  border-radius: 2px;
  border: 1px solid var(--color-primary);
}

.preview-avatar {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.preview-email {
  font-size: 12px;
  color: var(--color-primary-hover);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.required {
  color: var(--color-danger);
  margin-left: 4px;
}

.role-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-option-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.role-option-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.batch-role-info {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
}

.batch-role-info strong {
  color: var(--color-primary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border-primary);
  margin-top: 8px;
}

@media (max-width: 768px) {
  .project-members {
    border-radius: 2px;
    margin: 0;
    border: none;
    box-shadow: none;
  }

  .top-nav-bar {
    padding: 0 16px;
  }

  .nav-item {
    padding: 12px 16px;
  }

  .member-section {
    padding: 16px;
  }

  .section-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-item.search-item {
    max-width: none;
  }

  .roles-grid {
    grid-template-columns: 1fr;
  }
}
</style>
