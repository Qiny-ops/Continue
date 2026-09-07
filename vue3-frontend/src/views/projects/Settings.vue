<template>
  <div class="project-settings">
    <!-- 顶部标签导航 -->
    <div class="settings-tabs">
      <div
        v-for="item in menuItems"
        :key="item.key"
        :class="['tab-item', { active: activeMenu === item.key }]"
        @click="activeMenu = item.key"
      >
        {{ item.label }}
      </div>
    </div>

    <!-- 基本设置 -->
    <div v-if="activeMenu === 'basic'" class="settings-section">
      <div class="section-title">基本信息</div>
      <div class="form-list">
        <!-- 项目图标 -->
        <div class="form-item">
          <label class="form-label">项目图标</label>
          <div class="form-value">
            <div class="icon-preview" :style="{ background: form.iconColor }">
              <el-icon :size="24"><component :is="getIcon(form.icon)" /></el-icon>
            </div>
            <el-button size="small" @click="showIconPicker = true">更换</el-button>
            <div class="color-list">
              <span
                v-for="c in colorPresets"
                :key="c"
                :class="['color-dot', { active: form.iconColor === c }]"
                :style="{ background: c }"
                @click="form.iconColor = c"
              />
            </div>
          </div>
        </div>

        <!-- 项目名称 -->
        <div class="form-item">
          <label class="form-label required">项目名称</label>
          <div class="form-value">
            <el-input v-model="form.name" placeholder="请输入项目名称" maxlength="50" />
          </div>
        </div>

        <!-- 项目标识 -->
        <div class="form-item">
          <label class="form-label">项目标识</label>
          <div class="form-value">
            <el-input v-model="form.identifier" placeholder="项目唯一标识" @input="formatIdentifier" />
            <span class="form-hint">用于项目 URL 和 API 调用</span>
          </div>
        </div>

        <!-- 项目描述 -->
        <div class="form-item">
          <label class="form-label">项目描述</label>
          <div class="form-value">
            <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述项目的目标和范围" maxlength="200" show-word-limit />
          </div>
        </div>

        <!-- 项目类型 -->
        <div class="form-item">
          <label class="form-label">项目类型</label>
          <div class="form-value">
            <el-select v-model="form.type" placeholder="选择类型">
              <el-option label="Web 应用" value="web" />
              <el-option label="移动应用" value="mobile" />
              <el-option label="API 服务" value="api" />
              <el-option label="桌面应用" value="desktop" />
              <el-option label="其他" value="other" />
            </el-select>
          </div>
        </div>

        <!-- 可见性 -->
        <div class="form-item">
          <label class="form-label">可见性</label>
          <div class="form-value">
            <el-select v-model="form.visibility" placeholder="选择可见性">
              <el-option label="公开" value="public" />
              <el-option label="私有" value="private" />
            </el-select>
          </div>
        </div>

        <!-- 时间设置 -->
        <div class="form-item">
          <label class="form-label">开始时间</label>
          <div class="form-value">
            <el-date-picker v-model="form.startTime" type="date" placeholder="选择开始时间" value-format="YYYY-MM-DD" />
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">结束时间</label>
          <div class="form-value">
            <el-date-picker v-model="form.endTime" type="date" placeholder="选择结束时间" value-format="YYYY-MM-DD" :disabled-date="disableEndDate" />
          </div>
        </div>

        <!-- 项目状态 -->
        <div class="form-item">
          <label class="form-label">项目状态</label>
          <div class="form-value">
            <div class="status-list">
              <div
                v-for="s in statusOptions"
                :key="s.value"
                :class="['status-item', { active: form.status === s.value }]"
                @click="form.status = s.value"
              >
                <span :class="['status-dot', s.value]" />
                <span>{{ s.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <el-button @click="resetForm">重置</el-button>
        <el-button v-if="canManageSettings" type="primary" :loading="saving" @click="saveSettings">保存设置</el-button>
      </div>
    </div>

    <!-- 成员管理 -->
    <div v-else-if="activeMenu === 'members'" class="settings-section">
      <div class="section-header">
        <div class="section-title">成员管理</div>
        <el-button v-if="canManageMembers" type="primary" @click="openAddMember">
          <el-icon><Plus /></el-icon>
          添加成员
        </el-button>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input v-model="memberSearch" placeholder="搜索成员姓名或邮箱" :prefix-icon="Search" clearable style="width: 240px" />
        <el-select v-model="memberRoleFilter" placeholder="全部角色" clearable style="width: 120px">
          <el-option label="管理员" value="admin" />
          <el-option label="开发人员" value="developer" />
          <el-option label="测试人员" value="tester" />
          <el-option label="观察者" value="viewer" />
        </el-select>
        <el-select v-model="memberStatusFilter" placeholder="全部状态" clearable style="width: 120px">
          <el-option label="活跃" value="active" />
          <el-option label="已禁用" value="disabled" />
        </el-select>
      </div>

      <!-- 批量操作 -->
      <div v-if="selectedMembers.length > 0 && canManageMembers" class="batch-bar">
        <span>已选择 {{ selectedMembers.length }} 个成员</span>
        <el-button size="small" @click="showBatchRole = true">批量修改角色</el-button>
        <el-button type="danger" size="small" @click="batchRemoveMembers">批量移除</el-button>
        <el-button size="small" @click="selectedMembers = []">取消</el-button>
      </div>

      <!-- 成员列表 -->
      <el-table
        ref="memberTableRef"
        :data="paginatedMembers"
        style="width: 100%"
        empty-text="暂无成员数据"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" :selectable="canSelectRow" />
        <el-table-column label="成员" min-width="200">
          <template #default="{ row }">
            <div class="member-cell">
              <el-avatar :size="32" :src="row.avatar" class="member-avatar">
                {{ row.name?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div class="member-info">
                <span class="member-name">
                  {{ row.name }}
                  <el-tag v-if="row.isOwner" type="warning" size="small">创建者</el-tag>
                </span>
                <span class="member-email">{{ row.email }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small" effect="light">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <div class="status-cell">
              <span :class="['status-dot', row.status]" />
              <span>{{ getStatusText(row.status) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="joinDate" label="加入时间" width="100" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div v-if="!row.isOwner && canManageMembers" class="action-cell">
              <el-button link type="primary" size="small" @click="openEditMember(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removeMember(row)">移除</el-button>
            </div>
            <span v-else-if="!row.isOwner" class="no-permission-text">无权限</span>
            <span v-else class="owner-text">创建者</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="memberPage"
          v-model:page-size="memberPageSize"
          :page-sizes="[10, 20, 50]"
          :total="filteredMembers.length"
          layout="total, sizes, prev, pager, next"
          size="small"
        />
      </div>
    </div>

    <!-- 角色列表 -->
    <div v-else-if="activeMenu === 'permissions'" class="settings-section permission-section">
      <div class="section-header">
        <div class="section-title">角色列表</div>
        <div class="section-actions">
          <el-button v-if="isProjectAdminUser && !hasRoleChanges" type="primary" @click="openAddRole">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
          <el-button v-if="hasRoleChanges" @click="resetRoleChanges">重置</el-button>
          <el-button v-if="hasRoleChanges" type="primary" :loading="savingRoles" @click="saveRoleChanges">保存修改</el-button>
        </div>
      </div>

      <div class="permission-table-wrapper">
        <table class="permission-table">
          <thead>
            <tr>
              <th class="col-role">角色</th>
              <th class="col-count">成员</th>
              <th v-for="perm in allPermissions" :key="perm.code" class="col-perm">
                {{ perm.name }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="role in roleList" :key="role.key">
              <td class="col-role">
                <div class="role-cell">
                  <div class="role-icon" :style="{ background: role.color }">
                    <el-icon><UserFilled /></el-icon>
                  </div>
                  <span class="role-name">{{ role.name }}</span>
                </div>
              </td>
              <td class="col-count">{{ role.memberCount }} 人</td>
              <td
                v-for="perm in allPermissions"
                :key="perm.code"
                class="col-perm"
                :class="{ clickable: isProjectAdminUser && role.key !== 'admin' }"
                @click="isProjectAdminUser && role.key !== 'admin' && toggleRolePermission(role.key, perm.code)"
              >
                <el-checkbox
                  v-if="isProjectAdminUser && role.key !== 'admin'"
                  :model-value="role.permissions.includes(perm.code)"
                  @click.stop
                  @change="toggleRolePermission(role.key, perm.code)"
                />
                <el-icon v-else-if="role.permissions.includes(perm.code)" class="status-icon success">
                  <CircleCheckFilled />
                </el-icon>
                <span v-else class="status-dot disabled"></span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="section-footer">
        <span class="footer-tip" v-if="isProjectAdminUser">
          <el-icon><InfoFilled /></el-icon>
          管理员角色默认拥有所有权限，不可修改
        </span>
      </div>
    </div>

    <!-- 危险操作 -->
    <div v-else-if="activeMenu === 'danger'" class="settings-section danger-section">
      <div class="section-title danger-title">危险操作</div>
      <div class="danger-card">
        <div class="danger-item">
          <div class="danger-info">
            <h4>删除项目</h4>
            <p>删除项目后，项目下的所有测试用例、测试计划、缺陷等数据都将被永久删除，无法恢复。</p>
          </div>
          <el-button type="danger" @click="handleDeleteProject">
            删除项目
          </el-button>
        </div>
      </div>
    </div>

    <!-- 图标选择器 -->
    <el-dialog v-model="showIconPicker" title="选择图标" width="480px">
      <div class="icon-grid">
        <div
          v-for="icon in availableIcons"
          :key="icon.name"
          :class="['icon-item', { selected: form.icon === icon.name }]"
          @click="form.icon = icon.name; showIconPicker = false"
        >
          <div class="icon-preview-small" :style="{ background: form.iconColor }">
            <el-icon :size="20"><component :is="icon.component" /></el-icon>
          </div>
          <span>{{ icon.label }}</span>
        </div>
      </div>
    </el-dialog>

    <!-- 成员编辑对话框 -->
    <el-dialog
      v-model="memberDialogVisible"
      :title="editingMember ? '编辑成员' : '添加成员'"
      width="460px"
      :close-on-click-modal="false"
    >
      <div class="dialog-form">
        <div v-if="!editingMember" class="mode-tabs">
          <div :class="['tab-item', { active: addMode === 'select' }]" @click="addMode = 'select'">从用户列表选择</div>
          <div :class="['tab-item', { active: addMode === 'manual' }]" @click="addMode = 'manual'">手动输入</div>
        </div>

        <template v-if="editingMember">
          <div class="member-preview">
            <el-avatar :size="36" class="preview-avatar">{{ memberForm.name?.charAt(0)?.toUpperCase() }}</el-avatar>
            <div class="preview-info">
              <span class="preview-name">{{ memberForm.name }}</span>
              <span class="preview-email">{{ memberForm.email }}</span>
            </div>
          </div>
        </template>

        <template v-else-if="addMode === 'select'">
          <div class="form-field">
            <label>选择用户</label>
            <el-select v-model="memberForm.userId" placeholder="搜索并选择用户" filterable :loading="usersLoading" style="width: 100%" @change="handleUserSelect">
              <el-option v-for="u in allUsers" :key="u.id" :label="u.name" :value="u.id">
                <div class="user-option">
                  <el-avatar :size="24" class="user-option-avatar">{{ u.name?.charAt(0)?.toUpperCase() }}</el-avatar>
                  <span>{{ u.name }}</span>
                  <span class="user-option-email">{{ u.email }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
        </template>

        <template v-else>
          <div class="form-field">
            <label>姓名</label>
            <el-input v-model="memberForm.name" placeholder="请输入成员姓名" />
          </div>
          <div class="form-field">
            <label>邮箱</label>
            <el-input v-model="memberForm.email" placeholder="请输入成员邮箱" />
          </div>
        </template>

        <div class="form-field">
          <label>角色</label>
          <el-select v-model="memberForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="开发人员" value="developer" />
            <el-option label="测试人员" value="tester" />
            <el-option label="观察者" value="viewer" />
          </el-select>
        </div>

        <div class="form-field">
          <label>状态</label>
          <el-select v-model="memberForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="活跃" value="active" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <el-button @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="memberSubmitting" @click="submitMember">
          {{ editingMember ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量修改角色 -->
    <el-dialog v-model="showBatchRole" title="批量修改角色" width="360px">
      <div class="batch-info">将修改 <strong>{{ selectedMembers.length }}</strong> 个成员的角色</div>
      <div class="form-field">
        <label>新角色</label>
        <el-select v-model="batchRoleValue" placeholder="请选择角色" style="width: 100%">
          <el-option label="管理员" value="admin" />
          <el-option label="开发人员" value="developer" />
          <el-option label="测试人员" value="tester" />
          <el-option label="观察者" value="viewer" />
        </el-select>
      </div>
      <template #footer>
        <el-button @click="showBatchRole = false">取消</el-button>
        <el-button type="primary" :disabled="!batchRoleValue" @click="confirmBatchRole">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑角色对话框 -->
    <RolePermissionDialog
      v-model="roleDialogVisible"
      :role="editingRole"
      :project-id="props.project.id"
      @success="handleRoleSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, UserFilled, CircleCheckFilled, InfoFilled } from '@element-plus/icons-vue'
import { getIconComponent, roleIcons } from '@/utils/icons'
import { useProjectStore } from '@/stores/modules/project'
import { useMemberStore } from '@/stores/modules/member'
import { usePermissionStore } from '@/stores/modules/permission'
import { usePermission } from '@/composables/permission/usePermission'
import { PERMISSION_NAMES, ROLE_COLORS } from '@/constants/permissions'
import { getAvatarUrl } from '@/utils/avatar'
import RolePermissionDialog from './components/RolePermissionDialog.vue'

const router = useRouter()

const props = defineProps({ project: { type: Object, required: true } })

const projectStore = useProjectStore()
const memberStore = useMemberStore()
const permissionStore = usePermissionStore()
const { canManageMembers, canManageSettings, isProjectAdminUser, isProjectOwnerUser } = usePermission()

const activeMenu = ref('basic')
const menuItems = computed(() => {
  const items = [{ key: 'basic', label: '基本信息' }]
  if (canManageMembers.value) {
    items.push({ key: 'members', label: '成员管理' })
    items.push({ key: 'permissions', label: '角色列表' })
  }
  if (isProjectOwnerUser.value) {
    items.push({ key: 'danger', label: '危险操作' })
  }
  return items
})

const colorPresets = ['#18181B', '#3F3F46', '#52525B', '#71717A', '#EF4444', '#22C55E', '#EAB308', '#0EA5E9']
const statusOptions = [
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'archived', label: '已归档' }
]

const form = reactive({
  name: props.project.name || '',
  description: props.project.description || '',
  identifier: props.project.code || props.project.identifier || '',
  type: props.project.type || 'web',
  visibility: props.project.visibility || 'private',
  startTime: props.project.startTime || null,
  endTime: props.project.endTime || null,
  status: props.project.status || 'in_progress',
  icon: props.project.icon || 'Folder',
  iconColor: props.project.iconColor || '#18181B'
})

const originalForm = JSON.parse(JSON.stringify(form))
const saving = ref(false)
const showIconPicker = ref(false)

const availableIcons = roleIcons

const getIcon = (name) => getIconComponent(name)

const disableEndDate = (time) => form.startTime && time.getTime() < new Date(form.startTime).getTime()
const formatIdentifier = () => { form.identifier = form.identifier.toLowerCase().replace(/[^a-z0-9_-]/g, '') }

const resetForm = async () => {
  try {
    await ElMessageBox.confirm('确定重置？未保存的更改将丢失', '确认', { type: 'warning' })
    Object.assign(form, originalForm)
    ElMessage.success('已重置')
  } catch {}
}

const saveSettings = async () => {
  if (!form.name.trim()) return ElMessage.warning('请输入项目名称')
  saving.value = true
  try {
    await projectStore.updateProject(props.project.id, {
      name: form.name.trim(),
      description: form.description.trim(),
      identifier: form.identifier,
      type: form.type,
      visibility: form.visibility,
      startTime: form.startTime,
      endTime: form.endTime,
      status: form.status,
      icon: form.icon,
      iconColor: form.iconColor
    })
    Object.assign(originalForm, form)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || '网络错误'))
  } finally {
    saving.value = false
  }
}

// 成员管理
const memberSearch = ref('')
const memberRoleFilter = ref('')
const memberStatusFilter = ref('')
const memberPage = ref(1)
const memberPageSize = ref(10)
const memberTableRef = ref(null)
const selectedMembers = ref([])

const memberDialogVisible = ref(false)
const editingMember = ref(null)
const addMode = ref('select')
const memberSubmitting = ref(false)
const memberForm = reactive({ userId: '', name: '', email: '', role: '', status: 'active' })
const usersLoading = ref(false)
const allUsers = ref([])

const showBatchRole = ref(false)
const batchRoleValue = ref('')

const members = computed(() => memberStore.members.filter(m => m).map(m => ({
  ...m,
  id: m.id || m.user_id || m.userId,
  name: m.name || m.nickname || '',
  avatar: getAvatarUrl(m.avatar),
  joinDate: (m.joined_at || m.joinedAt) ? (m.joined_at || m.joinedAt).split('T')[0] : '-',
  isOwner: Boolean(m.isOwner || m.is_owner)
})))

const filteredMembers = computed(() => members.value.filter(m => {
  const matchSearch = !memberSearch.value || m.name.toLowerCase().includes(memberSearch.value.toLowerCase()) || m.email.toLowerCase().includes(memberSearch.value.toLowerCase())
  const matchRole = !memberRoleFilter.value || m.role === memberRoleFilter.value
  const matchStatus = !memberStatusFilter.value || m.status === memberStatusFilter.value
  return matchSearch && matchRole && matchStatus
}))

const paginatedMembers = computed(() => {
  const start = (memberPage.value - 1) * memberPageSize.value
  return filteredMembers.value.slice(start, start + memberPageSize.value)
})

const getRoleText = (role) => ({ admin: '管理员', developer: '开发人员', tester: '测试人员', viewer: '观察者' }[role] || role)
const getRoleType = (role) => ({ admin: 'danger', developer: 'primary', tester: 'success', viewer: 'info' }[role] || '')
const getStatusText = (status) => ({ active: '活跃', disabled: '已禁用' }[status] || status)

const canSelectRow = (row) => !row.isOwner
const handleSelectionChange = (selection) => { selectedMembers.value = selection }

const openAddMember = async () => {
  editingMember.value = null
  addMode.value = 'select'
  Object.assign(memberForm, { userId: '', name: '', email: '', role: '', status: 'active' })
  memberDialogVisible.value = true
  if (!allUsers.value.length) {
    usersLoading.value = true
    try {
      const users = await memberStore.fetchUsers()
      allUsers.value = users || []
    } finally {
      usersLoading.value = false
    }
  }
}

const handleUserSelect = (userId) => {
  const user = allUsers.value.find(u => u.id === userId)
  if (user) { memberForm.name = user.name; memberForm.email = user.email }
}

const openEditMember = (m) => {
  editingMember.value = m
  Object.assign(memberForm, { userId: m.id, name: m.name, email: m.email, role: m.role, status: m.status })
  memberDialogVisible.value = true
}

const removeMember = async (m) => {
  try {
    await ElMessageBox.confirm(`确定移除成员「${m.name}」？`, '确认', { type: 'warning' })
    await memberStore.removeMember(props.project.id, m.id)
    ElMessage.success('已移除')
  } catch (e) { if (e !== 'cancel') ElMessage.error('移除失败') }
}

const submitMember = async () => {
  if (!editingMember.value && addMode.value === 'select') {
    if (!memberForm.userId) return ElMessage.warning('请选择用户')
  } else if (!editingMember.value) {
    if (!memberForm.name?.trim()) return ElMessage.warning('请输入姓名')
    if (!memberForm.email?.trim()) return ElMessage.warning('请输入邮箱')
  }
  if (!memberForm.role) return ElMessage.warning('请选择角色')
  memberSubmitting.value = true
  try {
    if (editingMember.value) {
      await memberStore.updateMember(props.project.id, editingMember.value.id, { role: memberForm.role, status: memberForm.status })
      ElMessage.success('已更新')
    } else {
      await memberStore.addMember(props.project.id, { userId: memberForm.userId, nickname: memberForm.name, email: memberForm.email, role: memberForm.role, status: memberForm.status })
      ElMessage.success('已添加')
    }
    memberDialogVisible.value = false
  } catch { ElMessage.error('操作失败') }
  finally { memberSubmitting.value = false }
}

const batchRemoveMembers = async () => {
  try {
    await ElMessageBox.confirm(`确定移除 ${selectedMembers.value.length} 人？`, '确认', { type: 'warning' })
    for (const m of selectedMembers.value) await memberStore.removeMember(props.project.id, m.id)
    ElMessage.success('已移除')
    selectedMembers.value = []
  } catch (e) { if (e !== 'cancel') ElMessage.error('移除失败') }
}

const confirmBatchRole = async () => {
  try {
    await memberStore.batchUpdateMembers(props.project.id, selectedMembers.value, { role: batchRoleValue.value })
    ElMessage.success(`已修改 ${selectedMembers.value.length} 人`)
    showBatchRole.value = false
    selectedMembers.value = []
  } catch { ElMessage.error('修改失败') }
}

// 角色列表
// 所有可用权限
const allPermissions = computed(() => {
  return Object.entries(PERMISSION_NAMES).map(([code, name]) => ({ code, name }))
})

// 角色列表数据
const roleList = ref([])
const originalRoleData = ref({})
const savingRoles = ref(false)

// 初始化角色列表
const initRoleList = () => {
  const projectRoles = Array.isArray(permissionStore.projectRoles) ? permissionStore.projectRoles : []
  roleList.value = projectRoles.map(r => ({
    key: r.key,
    name: r.name || ({ admin: '管理员', developer: '开发人员', tester: '测试人员', viewer: '观察者' }[r.key] || r.key),
    color: r.color || ROLE_COLORS[r.key] || 'var(--color-text-tertiary)',
    memberCount: r.memberCount || 0,
    permissions: [...(r.permissions || [])]
  }))

  // 保存原始数据用于比较
  roleList.value.forEach(role => {
    originalRoleData.value[role.key] = [...role.permissions]
  })
}

// 监听 projectRoles 变化
watch(() => permissionStore.projectRoles, () => {
  initRoleList()
}, { immediate: true })

// 检测是否有修改
const hasRoleChanges = computed(() => {
  if (!roleList.value.length) return false
  for (const role of roleList.value) {
    const original = originalRoleData.value[role.key] || []
    if (JSON.stringify([...role.permissions].sort()) !== JSON.stringify([...original].sort())) {
      return true
    }
  }
  return false
})

// 切换权限
const toggleRolePermission = (roleKey, permCode) => {
  const role = roleList.value.find(r => r.key === roleKey)
  if (!role || roleKey === 'admin') return

  const index = role.permissions.indexOf(permCode)
  if (index > -1) {
    role.permissions.splice(index, 1)
  } else {
    role.permissions.push(permCode)
  }
}

// 重置修改
const resetRoleChanges = () => {
  roleList.value.forEach(role => {
    role.permissions = [...(originalRoleData.value[role.key] || [])]
  })
}

// 保存修改
const saveRoleChanges = async () => {
  savingRoles.value = true
  try {
    const memberApi = (await import('@/api/modules/member.js')).default

    for (const role of roleList.value) {
      if (role.key === 'admin') continue
      await memberApi.updateRole(props.project.id, role.key, {
        permissions: role.permissions
      })
      originalRoleData.value[role.key] = [...role.permissions]
    }

    ElMessage.success('权限配置已保存')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    savingRoles.value = false
  }
}

const getPermName = (p) => PERMISSION_NAMES[p] || p

// 角色新增/编辑
const roleDialogVisible = ref(false)
const editingRole = ref(null)

const openAddRole = () => {
  editingRole.value = null
  roleDialogVisible.value = true
}

const handleRoleSuccess = () => {
  permissionStore.initProjectPermissions(props.project.id)
}

const handleDeleteProject = async () => {
  try {
    await ElMessageBox.confirm(
      `确定删除项目「${props.project.name}」？删除后将无法恢复，项目下的所有测试用例、测试计划等数据都将被删除。`,
      '删除项目',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    await projectStore.deleteProject(props.project.id)
    ElMessage.success('项目已删除')
    router.push('/projects')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.message || '删除失败，请重试')
    }
  }
}

onMounted(async () => {
  await memberStore.fetchMembers(props.project.id)
  await permissionStore.initProjectPermissions(props.project.id)
})

watch(() => props.project, (p) => {
  Object.assign(form, {
    name: p.name || '',
    description: p.description || '',
    identifier: p.code || p.identifier || '',
    type: p.type || 'web',
    visibility: p.visibility || 'private',
    startTime: p.startTime || null,
    endTime: p.endTime || null,
    status: p.status || 'in_progress',
    icon: p.icon || 'Folder',
    iconColor: p.iconColor || 'var(--color-primary)'
  })
  Object.assign(originalForm, form)
}, { deep: true })
</script>

<style scoped>
.project-settings {
  height: 100%;
  overflow: auto;
  background: #fff;
}

/* 顶部标签导航 */
.settings-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

.settings-tabs .tab-item {
  padding: 12px 24px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.settings-tabs .tab-item:hover {
  color: var(--color-primary);
}

.settings-tabs .tab-item.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 500;
  background: #fff;
}

/* 设置区块 */
.settings-section {
  padding: 16px 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.section-header .section-title {
  margin-bottom: 0;
}

/* 表单列表 */
.form-list {
  display: flex;
  flex-direction: column;
}

.form-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  width: 100px;
  flex-shrink: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
  padding-top: 6px;
}

.form-label.required::after {
  content: '*';
  color: var(--color-danger);
  margin-left: 4px;
}

.form-value {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-value .el-input,
.form-value .el-select,
.form-value .el-date-picker {
  max-width: 320px;
}

.form-value .el-textarea {
  max-width: 480px;
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 图标选择 */
.icon-preview {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.color-list {
  display: flex;
  gap: 6px;
}

.color-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
}

.color-dot.active {
  border-color: var(--color-text-primary);
}

/* 状态选择 */
.status-list {
  display: flex;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.status-item.active {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  color: var(--color-text-primary);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.in_progress { background: var(--color-primary); }
.status-dot.completed { background: var(--color-success); }
.status-dot.archived { background: var(--color-warning); }
.status-dot.active { background: var(--color-success); }
.status-dot.disabled { background: var(--color-text-tertiary); }

/* 表单操作 */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  margin-top: 8px;
  border-top: 1px solid var(--color-border-primary);
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

/* 批量操作 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-primary-light);
  border: 1px solid var(--color-primary);
  border-radius: 2px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-primary);
}

/* 成员列表 */
.member-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-avatar {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  flex-shrink: 0;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.member-email {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.action-cell {
  display: flex;
  gap: 4px;
}

.owner-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.no-permission-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

/* 角色列表 */
.permission-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.permission-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.permission-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.permission-table thead th {
  background: var(--color-bg-secondary);
  padding: 12px 16px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-primary);
  white-space: nowrap;
}

.permission-table thead th.col-role {
  text-align: left;
  width: 140px;
  font-weight: 600;
}

.permission-table thead th.col-count {
  width: 80px;
}

.permission-table thead th.col-perm {
  min-width: 80px;
}

.permission-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-primary);
  text-align: center;
}

.permission-table tbody tr:last-child td {
  border-bottom: none;
}

.permission-table tbody td.col-role {
  text-align: left;
}

.permission-table tbody td.col-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.permission-table tbody td.clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.permission-table tbody td.clickable:hover {
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
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.section-footer {
  padding: 12px 16px;
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

/* 危险操作区域 */
.danger-section {
  background: #fff;
}

.danger-title {
  color: var(--color-danger);
}

.danger-card {
  border: 1px solid var(--color-danger-light);
  border-radius: 2px;
  background: var(--color-danger-light);
  overflow: hidden;
}

.danger-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.danger-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-danger);
}

.danger-info p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  max-width: 480px;
}

/* 对话框 */
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-tabs {
  display: flex;
  gap: 0;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.mode-tabs .tab-item {
  flex: 1;
  text-align: center;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: none;
  background: transparent;
}

.mode-tabs .tab-item.active {
  background: #fff;
  color: var(--color-primary);
}

.member-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.preview-avatar {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.preview-email {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-option-avatar {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.user-option-email {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.batch-info {
  font-size: 14px;
  color: var(--color-text-secondary);
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  margin-bottom: 12px;
}

.batch-info strong {
  color: var(--color-primary);
}

/* 图标网格 */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-item:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.icon-item.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.icon-preview-small {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.icon-item span {
  font-size: 11px;
  color: var(--color-text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .settings-tabs .tab-item {
    padding: 10px 16px;
    font-size: 13px;
  }

  .form-item {
    flex-direction: column;
    gap: 6px;
  }

  .form-label {
    width: auto;
    padding-top: 0;
  }

  .form-value .el-input,
  .form-value .el-select,
  .form-value .el-date-picker {
    max-width: none;
  }

  .filter-bar {
    flex-direction: column;
  }

  .filter-bar .el-input {
    width: 100% !important;
  }
}
</style>
