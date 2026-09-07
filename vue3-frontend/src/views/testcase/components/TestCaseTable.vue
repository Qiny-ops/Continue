<template>
  <div class="test-case-table">
    <el-table
      ref="tableRef"
      :data="data"
      style="width: 100%; height: 100%"
      empty-text="暂无测试用例数据"
      row-key="id"
      v-loading="loading"
      @selection-change="$emit('selectionChange', $event)"
    >
      <el-table-column v-if="showSelection" type="selection" width="50" reserve-selection />

      <el-table-column prop="id" label="ID" width="80" align="center">
        <template #default="{ row }">
          <span class="case-id">{{ row.id }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="title" label="用例名称" min-width="220">
        <template #default="{ row }">
          <div class="case-title-cell">
            <span class="case-title">{{ row.title }}</span>
            <div v-if="row.tags && row.tags.length" class="case-tags">
              <el-tag
                v-for="tag in row.tags.slice(0, 2)"
                :key="tag"
                size="small"
                type="info"
                class="case-tag"
              >
                {{ tag }}
              </el-tag>
              <span v-if="row.tags.length > 2" class="more-tags">+{{ row.tags.length - 2 }}</span>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="priority" label="优先级" width="90" align="center">
        <template #default="{ row }">
          <span class="priority-badge" :class="getPriorityClass(row.priority)">
            {{ getPriorityLabel(row.priority) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="review_status" label="评审状态" width="100" align="center">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="row.review_status === 'pending' ? 'warning' : (row.review_status === 'approved' ? 'success' : (row.review_status === 'rejected' ? 'danger' : 'primary'))"
            :class="{ 'revision-btn': row.review_status === 'revision_pending' }"
            plain
            @click="$emit('review', row)"
          >
            {{ getReviewStatusText(row.review_status) }}
          </el-button>
        </template>
      </el-table-column>

      <el-table-column prop="module_name" label="所属模块" width="140">
        <template #default="{ row }">
          <div class="module-cell">
            <el-icon class="module-icon"><Folder /></el-icon>
            <span class="module-name">{{ row.module_name || '-' }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="steps" label="步骤" width="100" align="center">
        <template #default="{ row }">
          <el-tooltip
            v-if="row.steps"
            placement="top"
            :show-after="100"
          >
            <template #content>
              <div class="steps-tooltip">
                <div class="tooltip-header">测试步骤</div>
                <div class="step-text">{{ row.steps }}</div>
                <div v-if="row.expected_result" class="tooltip-header" style="margin-top: 8px;">预期结果</div>
                <div v-if="row.expected_result" class="step-text expected">{{ row.expected_result }}</div>
              </div>
            </template>
            <div class="steps-cell">
              <el-icon class="steps-icon"><List /></el-icon>
              <span class="steps-count">有</span>
            </div>
          </el-tooltip>
          <div v-else class="steps-cell empty">
            <el-icon class="steps-icon"><List /></el-icon>
            <span class="steps-count">0</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="created_by_name" label="创建人" width="110">
        <template #default="{ row }">
          <div class="user-cell">
            <img
              v-if="row.created_by_avatar && !avatarErrors[row.id]"
              :src="getAvatarUrl(row.created_by_avatar)"
              class="user-avatar-img"
              alt=""
              @error="handleAvatarError(row.id)"
            />
            <span v-else class="user-avatar">{{ getAvatarText(row.created_by_name) }}</span>
            <span class="user-name">{{ row.created_by_name || '-' }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">
          <span class="date-text">{{ formatDate(row.created_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-cell">
            <el-tooltip content="执行" placement="top">
              <span class="action-btn execute" @click="handleCommand('execute', row)">
                <el-icon><VideoPlay /></el-icon>
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
                  <el-dropdown-item command="copy">
                    <el-icon><CopyDocument /></el-icon>
                    复制用例
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除用例</span>
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
import { VideoPlay, Edit, Delete, Folder, MoreFilled, CopyDocument, List } from '@element-plus/icons-vue'
import { useTestCaseFormatters } from '@/composables/testcase/useTestCaseFormatters'
import { getAvatarUrl } from '@/utils/avatar.js'

const tableRef = ref(null)
const avatarErrors = ref({})

defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  showSelection: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['selectionChange', 'command', 'review'])

const {
  getPriorityLabel,
  getRelativeTime
} = useTestCaseFormatters()

const PRIORITY_CLASS_MAP = {
  p0: 'critical',
  p1: 'high',
  p2: 'medium',
  p3: 'low'
}

const REVIEW_STATUS_TEXT = {
  pending: '待评审',
  revision_pending: '待重审',
  approved: '已通过',
  rejected: '已驳回'
}

const getPriorityClass = (priority) => PRIORITY_CLASS_MAP[priority] || 'medium'
const getReviewStatusText = (status) => REVIEW_STATUS_TEXT[status] || '已通过'

const getAvatarText = (name) => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

const handleAvatarError = (caseId) => {
  avatarErrors.value[caseId] = true
}

const formatDate = (dateStr) => getRelativeTime(dateStr)

const handleCommand = (command, row) => {
  emit('command', { command, row })
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
}

defineExpose({
  clearSelection
})
</script>

<style scoped>
.test-case-table {
  height: 100%;
  overflow: hidden;
}

.test-case-table :deep(.el-table) {
  --el-table-border-color: var(--color-border-secondary);
  --el-table-header-bg-color: var(--color-bg-secondary);
}

.test-case-table :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.test-case-table :deep(.el-table__row) {
  font-size: 13px;
}

.test-case-table :deep(.el-table .cell) {
  padding: 0 12px;
}

.test-case-table :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-border-secondary);
  padding: 10px 0;
}

.test-case-table :deep(.el-table__row:hover td) {
  background-color: var(--color-bg-secondary);
}

.test-case-table :deep(.el-table__empty-block) {
  min-height: 300px;
}

.case-id {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 12px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
}

.case-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.case-title {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-tags {
  display: flex;
  align-items: center;
  gap: 4px;
}

.case-tag {
  font-size: 11px;
  padding: 0 4px;
  height: 18px;
  line-height: 16px;
}

.more-tags {
  font-size: 11px;
  color: var(--color-text-tertiary);
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

.review-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 500;
}

.review-badge.pending {
  background: #fef3cd;
  color: #856404;
}

.review-badge.revision_pending {
  background: #e9d5ff;
  color: #7c3aed;
}

.review-badge.approved {
  background: #d4edda;
  color: #155724;
}

.review-badge.rejected {
  background: #f8d7da;
  color: #721c24;
}

/* 待重审按钮紫色样式 */
.revision-btn {
  background: #f3e8ff !important;
  border-color: #c4b5fd !important;
  color: #7c3aed !important;
}

.revision-btn:hover,
.revision-btn:focus {
  background: #e9d5ff !important;
  border-color: #a78bfa !important;
  color: #6d28d9 !important;
}

.revision-btn:deep(span) {
  color: #7c3aed !important;
}

.revision-btn:hover:deep(span),
.revision-btn:focus:deep(span) {
  color: #6d28d9 !important;
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

.steps-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-bg-tertiary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.steps-cell:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.steps-cell:hover .steps-icon,
.steps-cell:hover .steps-count {
  color: var(--color-primary);
}

.steps-cell.empty {
  background: var(--color-bg-secondary);
  border-color: var(--color-bg-tertiary);
  cursor: default;
}

.steps-cell.empty:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-bg-tertiary);
}

.steps-cell.empty:hover .steps-icon,
.steps-cell.empty:hover .steps-count {
  color: var(--color-text-placeholder);
}

.steps-icon {
  font-size: 14px;
  color: var(--color-text-tertiary);
  transition: color 0.2s ease;
}

.steps-cell.empty .steps-icon {
  color: var(--color-text-placeholder);
}

.steps-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  transition: color 0.2s ease;
}

.steps-cell.empty .steps-count {
  color: var(--color-text-placeholder);
}

.steps-tooltip {
  max-width: 400px;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px 0;
}

.steps-tooltip::-webkit-scrollbar {
  width: 4px;
}

.steps-tooltip::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.steps-tooltip::-webkit-scrollbar-track {
  background: transparent;
}

.tooltip-header {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  padding: 4px 0 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 8px;
  position: sticky;
  top: 0;
  background: inherit;
}

.step-text {
  font-size: 13px;
  color: #fff;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.step-text.expected {
  color: var(--color-success);
  font-size: 12px;
}

.test-case-table :deep(.user-cell) {
  display: flex !important;
  align-items: center;
  gap: 8px;
}

.test-case-table :deep(.user-avatar) {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-width: 24px;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  border-radius: 50%;
  flex-shrink: 0;
  line-height: 24px;
  text-align: center;
}

.test-case-table :deep(.user-avatar-img) {
  width: 24px;
  height: 24px;
  min-width: 24px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.test-case-table :deep(.user-name) {
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.action-btn.execute:hover {
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
