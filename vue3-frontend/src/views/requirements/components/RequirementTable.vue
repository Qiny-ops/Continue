<template>
  <div class="requirement-table">
    <el-table
      ref="tableRef"
      :data="data"
      style="width: 100%; height: 100%"
      empty-text="暂无需求数据"
      row-key="id"
      v-loading="loading"
      @selection-change="$emit('selectionChange', $event)"
    >
      <el-table-column v-if="showSelection" type="selection" width="50" reserve-selection />

      <el-table-column prop="id" label="ID" width="80" align="center">
        <template #default="{ row }">
          <span class="req-id">{{ row.id }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="title" label="需求标题" min-width="220">
        <template #default="{ row }">
          <div class="req-title-cell">
            <span class="req-title">{{ row.title }}</span>
            <el-tag v-if="row.source === 'ai_extracted'" size="small" type="success">AI提取</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="module" label="所属模块" width="140">
        <template #default="{ row }">
          <div class="module-cell">
            <el-icon class="module-icon"><Folder /></el-icon>
            <span class="module-name">{{ row.module || '-' }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="func_point" label="功能点" min-width="200">
        <template #default="{ row }">
          <span class="func-point">{{ row.func_point || '-' }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="priority" label="优先级" width="90" align="center">
        <template #default="{ row }">
          <span class="priority-badge" :class="getPriorityClass(row.priority)">
            {{ getPriorityLabel(row.priority) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="testcase_count" label="关联用例" width="100" align="center">
        <template #default="{ row }">
          <span class="testcase-count">{{ row.testcase_count || 0 }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="created_by_name" label="创建人" width="110">
        <template #default="{ row }">
          <span>{{ row.created_by_name || '-' }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">
          <span class="date-text">{{ formatDate(row.created_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="140" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-cell">
            <el-tooltip content="生成测试用例" placement="top">
              <span class="action-btn generate" @click="$emit('generate', row)">
                <el-icon><MagicStick /></el-icon>
              </span>
            </el-tooltip>
            <el-tooltip content="编辑" placement="top">
              <span class="action-btn edit" @click="handleCommand('edit', row)">
                <el-icon><Edit /></el-icon>
              </span>
            </el-tooltip>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
              <span class="action-btn more">
                <el-icon><MoreFilled /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除需求</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Edit, Delete, Folder, MoreFilled, MagicStick } from '@element-plus/icons-vue'

const tableRef = ref(null)

defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  showSelection: { type: Boolean, default: false },
})

const emit = defineEmits(['selectionChange', 'command', 'generate'])

const PRIORITY_MAP = { p0: 'critical', p1: 'high', p2: 'medium', p3: 'low' }
const PRIORITY_LABEL = { p0: 'P0', p1: 'P1', p2: 'P2', p3: 'P3' }
const STATUS_MAP = { draft: '草稿', active: '活跃', completed: '已完成', archived: '已归档' }
const STATUS_TYPE = { draft: 'info', active: 'success', completed: 'primary', archived: 'warning' }

const getPriorityClass = (p) => PRIORITY_MAP[p] || 'medium'
const getPriorityLabel = (p) => PRIORITY_LABEL[p] || 'P2'
const getStatusText = (s) => STATUS_MAP[s] || '草稿'
const getStatusType = (s) => STATUS_TYPE[s] || 'info'

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const handleCommand = (command, row) => {
  emit('command', { command, row })
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
}

defineExpose({ clearSelection })
</script>

<style scoped>
.requirement-table {
  height: 100%;
  overflow: hidden;
}

.requirement-table :deep(.el-table) {
  --el-table-border-color: var(--color-border-secondary);
  --el-table-header-bg-color: var(--color-bg-secondary);
}

.requirement-table :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.requirement-table :deep(.el-table__row) {
  font-size: 13px;
}

.requirement-table :deep(.el-table .cell) {
  padding: 0 12px;
}

.requirement-table :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-border-secondary);
  padding: 10px 0;
}

.requirement-table :deep(.el-table__row:hover td) {
  background-color: var(--color-bg-secondary);
}

.req-id {
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: 12px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
}

.req-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.req-title {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.module-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.module-icon {
  color: var(--color-warning);
  font-size: 14px;
}

.module-name {
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.func-point {
  color: var(--color-text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.priority-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 500;
}

.priority-badge.critical {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.priority-badge.high {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.priority-badge.medium {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.priority-badge.low {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
}

.testcase-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
}

.date-text {
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
}

.action-btn.generate:hover {
  background: var(--color-success-light);
  color: var(--color-success);
}

.action-btn.edit:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.action-btn.more:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.delete-text {
  color: var(--color-danger);
}
</style>
