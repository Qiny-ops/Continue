<template>
  <Transition name="slide-up">
    <div v-if="selectedCount > 0" class="batch-action-bar">
      <div class="batch-left">
        <div class="batch-info">
          <el-checkbox
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="$emit('selectAll', $event)"
          />
          <span class="selected-count">
            已选择 <strong>{{ selectedCount }}</strong> 项
          </span>
        </div>
        <div class="batch-divider"></div>
        <div class="quick-actions">
          <el-button text size="small" @click="$emit('selectAll', true)">
            <el-icon><Check /></el-icon>
            全选
          </el-button>
          <el-button text size="small" @click="$emit('clearSelection')">
            <el-icon><Close /></el-icon>
            取消
          </el-button>
        </div>
      </div>

      <div class="batch-right">
        <div class="action-group">
          <el-tooltip content="批量执行选中的用例" placement="top">
            <el-button class="action-btn" @click="$emit('batchExecute')">
              <el-icon><VideoPlay /></el-icon>
              <span>执行</span>
            </el-button>
          </el-tooltip>

          <el-dropdown trigger="click" @command="handleEditCommand">
            <el-button class="action-btn">
              <el-icon><Edit /></el-icon>
              <span>修改</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="priority">
                  <el-icon><Flag /></el-icon>
                  修改优先级
                </el-dropdown-item>
                <el-dropdown-item command="module">
                  <el-icon><FolderOpened /></el-icon>
                  移动到模块
                </el-dropdown-item>
                <el-dropdown-item command="tags">
                  <el-icon><PriceTag /></el-icon>
                  修改标签
                </el-dropdown-item>
                <el-dropdown-item command="status">
                  <el-icon><CircleCheck /></el-icon>
                  修改自动化状态
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-tooltip content="复制选中的用例" placement="top">
            <el-button class="action-btn" @click="$emit('batchCopy')">
              <el-icon><CopyDocument /></el-icon>
              <span>复制</span>
            </el-button>
          </el-tooltip>

          <el-tooltip content="移动选中的用例到其他模块" placement="top">
            <el-button class="action-btn" @click="$emit('batchMove')">
              <el-icon><FolderOpened /></el-icon>
              <span>移动</span>
            </el-button>
          </el-tooltip>

          <el-popconfirm
            title="确定要删除选中的用例吗？"
            confirm-button-text="删除"
            cancel-button-text="取消"
            confirm-button-type="danger"
            @confirm="$emit('batchDelete')"
          >
            <template #reference>
              <el-button class="action-btn danger" @click.stop>
                <el-icon><Delete /></el-icon>
                <span>删除</span>
              </el-button>
            </template>
          </el-popconfirm>
        </div>

        <el-button class="exit-btn" @click="$emit('exitBatchMode')">
          退出批量模式
        </el-button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import {
  VideoPlay,
  Edit,
  Delete,
  FolderOpened,
  CopyDocument,
  Check,
  Close,
  ArrowDown,
  Flag,
  PriceTag,
  CircleCheck
} from '@element-plus/icons-vue'

defineProps({
  selectedCount: {
    type: Number,
    default: 0
  },
  totalCount: {
    type: Number,
    default: 0
  },
  isAllSelected: {
    type: Boolean,
    default: false
  },
  isIndeterminate: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'batchExecute',
  'batchMove',
  'batchCopy',
  'batchDelete',
  'batchEdit',
  'clearSelection',
  'selectAll',
  'exitBatchMode'
])

const handleEditCommand = (command) => {
  emit('batchEdit', command)
}
</script>

<style scoped>
.batch-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--color-primary);
  border-radius: 2px;
  box-shadow: var(--shadow-lg);
  margin: 0 16px 16px;
  flex-shrink: 0;
}

.batch-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-info :deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.9);
}

.batch-info :deep(.el-checkbox__inner) {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.batch-info :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #fff;
  border-color: #fff;
}

.batch-info :deep(.el-checkbox__input.is-checked .el-checkbox__inner::after) {
  border-color: var(--color-primary);
}

.batch-info :deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  background-color: rgba(255, 255, 255, 0.6);
  border-color: #fff;
}

.selected-count {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.selected-count strong {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  margin: 0 4px;
}

.batch-divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.3);
}

.quick-actions {
  display: flex;
  gap: 4px;
}

.quick-actions :deep(.el-button) {
  color: rgba(255, 255, 255, 0.85);
  padding: 4px 8px;
}

.quick-actions :deep(.el-button:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
}

.batch-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-group {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: #fff !important;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-1px);
}

.action-btn.danger:hover {
  background: rgba(255, 77, 79, 0.8) !important;
  border-color: var(--color-danger) !important;
}

.action-btn span {
  margin-left: 4px;
}

.exit-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  border: none !important;
  color: var(--color-primary) !important;
  font-weight: 500;
}

.exit-btn:hover {
  background: #fff !important;
  transform: translateY(-1px);
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 1200px) {
  .action-btn span {
    display: none;
  }

  .batch-action-bar {
    padding: 10px 16px;
  }
}
</style>
