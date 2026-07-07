<template>
  <el-dialog
    v-model="visible"
    :title="isEditing ? '编辑角色权限' : '新建角色'"
    width="680px"
    class="role-dialog"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="dialog-body">
      <div class="form-section">
        <div class="form-row">
          <div class="color-picker-wrapper">
            <div 
              class="color-block" 
              :style="{ background: form.color }"
              @click="showColorPicker = !showColorPicker"
            >
              <el-icon class="color-icon"><UserFilled /></el-icon>
            </div>
            <div v-if="showColorPicker" class="color-palette">
              <div 
                v-for="color in colorOptions" 
                :key="color"
                class="color-dot"
                :style="{ background: color }"
                :class="{ active: form.color === color }"
                @click="selectColor(color)"
              />
            </div>
          </div>
          <div class="form-fields">
            <el-input 
              v-model="form.name" 
              placeholder="角色名称"
              :disabled="isSystemRole"
            />
            <el-input 
              v-model="form.key" 
              placeholder="角色标识（英文）"
              :disabled="isEditing"
              style="margin-top: 8px;"
            />
          </div>
        </div>
      </div>

      <div class="permissions-section">
        <div class="section-bar">
          <span class="section-label">权限配置</span>
          <div class="section-actions">
            <el-button size="small" link type="primary" @click="selectAllPermissions">全选</el-button>
            <span class="divider">|</span>
            <el-button size="small" link @click="clearAllPermissions">清空</el-button>
            <span class="selected-badge">{{ selectedCount }} 项</span>
          </div>
        </div>
        
        <div class="permissions-table">
          <div class="table-header">
            <span class="col-name">功能模块</span>
            <span class="col-perms">权限项</span>
          </div>
          <div v-if="loading" class="loading-wrapper">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else class="table-body">
            <div 
              v-for="group in permissionGroups" 
              :key="group.key" 
              class="table-row"
            >
              <div class="col-name">
                <el-checkbox
                  v-model="group.checked"
                  :indeterminate="group.indeterminate"
                  @change="handleGroupChange(group)"
                >
                  {{ group.name }}
                </el-checkbox>
              </div>
              <div class="col-perms">
                <div class="perm-items">
                  <div 
                    v-for="perm in group.permissions" 
                    :key="perm.key"
                    class="perm-chip"
                    :class="{ active: perm.checked }"
                    @click="togglePermission(group, perm)"
                  >
                    <span class="perm-text">{{ perm.name }}</span>
                    <el-icon v-if="perm.checked" class="check-icon"><Check /></el-icon>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存修改' : '创建角色' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Check, Loading } from '@element-plus/icons-vue'
import { ROLE_COLORS } from '@/constants/permissions'
import memberApi from '@/api/modules/member.js'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  role: {
    type: Object,
    default: null
  },
  projectId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEditing = computed(() => !!props.role)
const isSystemRole = computed(() => {
  return ['admin', 'developer', 'tester', 'viewer'].includes(props.role?.key)
})

const submitting = ref(false)
const showColorPicker = ref(false)
const loading = ref(false)

const colorOptions = [...new Set(Object.values(ROLE_COLORS))]

const form = reactive({
  name: '',
  key: '',
  color: 'var(--color-text-secondary)',
  permissions: []
})

const permissionGroups = ref([])

const loadPermissions = async () => {
  loading.value = true
  try {
    const response = await memberApi.getPermissions()
    const data = response?.data || response || {}
    const permissions = data.permissions || []
    const groups = data.groups || []
    
    const groupedPermissions = groups.map(group => {
      const groupPerms = permissions.filter(p => p.group === group.key)
      return {
        key: group.key,
        name: group.name,
        permissions: groupPerms.map(p => ({
          key: p.key,
          name: p.name,
          checked: false
        })),
        checked: false,
        indeterminate: false
      }
    }).filter(g => g.permissions.length > 0)
    
    permissionGroups.value = groupedPermissions
  } catch {
    permissionGroups.value = []
  } finally {
    loading.value = false
  }
}

const selectedCount = computed(() => {
  let count = 0
  permissionGroups.value.forEach(group => {
    count += group.permissions.filter(p => p.checked).length
  })
  return count
})

const togglePermission = (group, perm) => {
  perm.checked = !perm.checked
  updateGroupStatus(group)
}

const updateGroupStatus = (group) => {
  const checkedCount = group.permissions.filter(p => p.checked).length
  group.checked = checkedCount === group.permissions.length
  group.indeterminate = checkedCount > 0 && checkedCount < group.permissions.length
}

const handleGroupChange = (group) => {
  group.permissions.forEach(p => {
    p.checked = group.checked
  })
  group.indeterminate = false
}

const selectAllPermissions = () => {
  permissionGroups.value.forEach(group => {
    group.checked = true
    group.indeterminate = false
    group.permissions.forEach(p => {
      p.checked = true
    })
  })
}

const clearAllPermissions = () => {
  permissionGroups.value.forEach(group => {
    group.checked = false
    group.indeterminate = false
    group.permissions.forEach(p => {
      p.checked = false
    })
  })
}

const selectColor = (color) => {
  form.color = color
  showColorPicker.value = false
}

const getSelectedPermissions = () => {
  const permissions = []
  permissionGroups.value.forEach(group => {
    group.permissions.forEach(p => {
      if (p.checked) {
        permissions.push(p.key)
      }
    })
  })
  return permissions
}

const setPermissions = (permissions) => {
  const permSet = new Set(permissions || [])
  permissionGroups.value.forEach(group => {
    group.permissions.forEach(p => {
      p.checked = permSet.has(p.key)
    })
    updateGroupStatus(group)
  })
}

const handleSubmit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入角色名称')
    return
  }

  if (!isEditing.value && !form.key.trim()) {
    ElMessage.warning('请输入角色标识')
    return
  }

  const permissions = getSelectedPermissions()
  if (permissions.length === 0) {
    ElMessage.warning('请至少选择一个权限')
    return
  }

  submitting.value = true
  try {
    if (isEditing.value) {
      await memberApi.updateRole(props.projectId, props.role.key, {
        permissions
      })
      ElMessage.success('角色权限更新成功')
    } else {
      await memberApi.createRole(props.projectId, {
        key: form.key.trim(),
        name: form.name.trim(),
        color: form.color,
        permissions
      })
      ElMessage.success('角色创建成功')
    }
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
  showColorPicker.value = false
}

watch(() => props.modelValue, async (val) => {
  if (val) {
    await loadPermissions()
    
    if (props.role) {
      form.name = props.role.name || ''
      form.key = props.role.key || ''
      form.color = ROLE_COLORS[props.role.key] || props.role.color || 'var(--color-text-secondary)'
      setPermissions(props.role.permissions || [])
    } else {
      form.name = ''
      form.key = ''
      form.color = 'var(--color-text-secondary)'
      setPermissions([])
    }
  }
})
</script>

<style scoped>
.role-dialog :deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-primary);
  margin: 0;
}

.role-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.role-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.dialog-body {
  display: flex;
  flex-direction: column;
}

.form-section {
  padding: 20px;
  border-bottom: 1px solid var(--color-border-primary);
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.color-picker-wrapper {
  position: relative;
  flex-shrink: 0;
}

.color-block {
  width: 48px;
  height: 48px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s;
}

.color-block:hover {
  transform: scale(1.05);
}

.color-icon {
  color: white;
  font-size: 20px;
}

.color-palette {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  display: flex;
  gap: 6px;
  padding: 10px;
  background: white;
  border-radius: 2px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 100;
}

.color-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.15s;
  border: 2px solid transparent;
}

.color-dot:hover {
  transform: scale(1.15);
}

.color-dot.active {
  border-color: var(--color-text-primary);
}

.form-fields {
  flex: 1;
  min-width: 0;
}

.permissions-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.divider {
  color: var(--color-text-placeholder);
  font-size: 12px;
}

.selected-badge {
  margin-left: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-border-primary);
  padding: 2px 8px;
  border-radius: 2px;
}

.permissions-table {
  flex: 1;
  overflow: auto;
}

.table-header {
  display: flex;
  padding: 10px 20px;
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-primary);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.table-body {
  max-height: 320px;
  overflow-y: auto;
}

.loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--color-text-secondary);
  gap: 8px;
}

.loading-wrapper .is-loading {
  font-size: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.table-row {
  display: flex;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-bg-tertiary);
  transition: background 0.15s;
}

.table-row:hover {
  background: var(--color-bg-secondary);
}

.table-row:last-child {
  border-bottom: none;
}

.col-name {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.col-name :deep(.el-checkbox__label) {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.col-perms {
  flex: 1;
  min-width: 0;
}

.perm-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.perm-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.perm-chip:hover {
  background: var(--color-border-primary);
}

.perm-chip.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.perm-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.perm-chip.active .perm-text {
  color: var(--color-primary);
}

.check-icon {
  font-size: 12px;
  color: var(--color-primary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-primary);
  background: var(--color-bg-secondary);
}

@media (max-width: 640px) {
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .color-picker-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .color-palette {
    position: static;
    margin-top: 0;
  }
  
  .table-header {
    display: none;
  }
  
  .table-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .col-name {
    width: auto;
  }
}
</style>
