<template>
  <div class="project-table-row" @click="$emit('click', project)">
    <div class="row-content">
      <!-- 项目名称列 -->
      <div class="column-header" :style="getColumnStyle(columns[0])">
        <div class="column-title">
          <a class="project-link" @click.stop="$emit('view', project)">
            <div
              class="project-icon"
              :style="{ backgroundColor: project.iconColor || 'var(--color-primary)' }"
            >
              <el-icon :size="16">
                <component :is="getIconComponent(project)" />
              </el-icon>
            </div>
            <div class="project-info">
              <div class="project-identifier">
                <div class="project-title">{{ project.name }}</div>
                <div class="project-code">{{ project.code }}</div>
              </div>
            </div>
          </a>
        </div>
      </div>

      <!-- 类型列 -->
      <div class="column-header" :style="getColumnStyle(columns[1])">
        <el-tag :type="getProjectTypeType(project.type)" size="small">
          {{ getProjectTypeLabel(project.type) }}
        </el-tag>
      </div>

      <!-- 状态列 -->
      <div class="column-header" :style="getColumnStyle(columns[2])">
        <el-tag :type="getStatusType(project.status)" size="small">
          {{ getStatusLabel(project.status) }}
        </el-tag>
      </div>

      <!-- 统计列 -->
      <div class="column-header" :style="getColumnStyle(columns[3])">
        <div class="project-stats">
          <div class="stat-item" title="测试用例">
            <span class="stat-icon">📝</span>
            <span class="stat-value">{{ project.testCases || 0 }}</span>
          </div>
          <div class="stat-item" title="测试计划">
            <span class="stat-icon">📋</span>
            <span class="stat-value">{{ project.testPlans || 0 }}</span>
          </div>
          <div class="stat-item" title="缺陷">
            <span class="stat-icon">🐛</span>
            <span class="stat-value">{{ project.bugs || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 负责人列 -->
      <div class="column-header" :style="getColumnStyle(columns[4])">
        <div class="project-owner">
          <div class="owner-wrapper">
            <div class="avatar-container">
              <el-avatar
                v-if="project.owner"
                :size="24"
                :src="getAvatarUrl(project.ownerAvatar) || undefined"
                class="owner-avatar"
                :title="project.owner"
              >
                {{ project.owner.charAt(0) }}
              </el-avatar>
              <span v-else class="no-owner">未分配</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 收藏列 -->
      <div class="column-header" :style="getColumnStyle(columns[5])">
        <div
          class="star-icon"
          :class="{ active: project.isFavorite }"
          :title="project.isFavorite ? '取消常用项目' : '添加收藏项目'"
          @click.stop="$emit('toggleFavorite', project)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path
              v-if="project.isFavorite"
              d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"
            />
            <path
              v-else
              d="M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4z"
            />
          </svg>
        </div>
      </div>

      <!-- 操作列 -->
      <div class="column-header" :style="getColumnStyle(columns[6])">
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="action-trigger" @click.stop>
            <svg
              fill="currentColor"
              preserveAspectRatio="xMidYMid meet"
              height="1em"
              width="1em"
              viewBox="0 0 16 16"
              class="cuk2-icon cuk2-icon-ellipsis-h null"
              style="vertical-align: middle"
            >
              <g>
                <path
                  d="M8 6.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm5.5 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm-11 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3z"
                />
              </g>
            </svg>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="view">
                <el-icon><View /></el-icon>
                查看项目
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided class="delete-item">
                <el-icon><Delete /></el-icon>
                删除项目
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ProjectTableRow - 项目表格行组件
 * @property {Object} project - 项目数据
 * @property {Array} columns - 列配置数组
 */
import { View, Delete } from '@element-plus/icons-vue'
import { getIconComponent as resolveIcon } from '@/utils/icons'
import { getAvatarUrl } from '@/utils/avatar.js'
import {
  getProjectTypeLabel,
  getProjectTypeType,
  getStatusLabel,
  getStatusType
} from '@/constants/project.js'

const props = defineProps({
  project: {
    type: Object,
    required: true
  },
  columns: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['click', 'view', 'toggleFavorite', 'delete'])

const handleCommand = (command) => {
  if (command === 'view') {
    emit('view', props.project)
  } else if (command === 'delete') {
    emit('delete', props.project)
  }
}

const getColumnStyle = (col) => {
  if (col.flexGrow) {
    return { flexGrow: col.flexGrow, minWidth: `${col.minWidth}px` }
  }
  return { width: `${col.width}px`, flexShrink: 0 }
}

const getIconComponent = (project) => {
  const iconName = project.icon || 'Folder'
  return resolveIcon(iconName)
}
</script>

<style scoped>
.project-table-row {
  width: 100%;
  height: 56px;
  padding: 0 24px;
  box-sizing: border-box;
  cursor: pointer;
}

.project-table-row:hover {
  background: var(--color-bg-secondary);
}

.row-content {
  box-shadow: 0 1px 0 0 var(--color-bg-tertiary);
  width: 100%;
  height: 100%;
  display: flex;
  align-items: stretch;
}

.column-header {
  color: rgba(32, 45, 64, 0.6);
  font-size: 12px;
  box-sizing: border-box;
  padding-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.column-header:first-child {
  justify-content: flex-start;
}

.column-title {
  display: flex;
  align-items: center;
  width: 100%;
}

.project-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  width: 100%;
}

.project-link:hover {
  color: var(--color-primary);
}

.project-icon {
  margin-right: 12px;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-identifier {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.project-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-title:hover {
  color: var(--color-primary);
  text-decoration: underline;
}

.project-code {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
}

.project-stats {
  display: flex;
  gap: 16px;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.stat-icon {
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  color: var(--color-text-primary);
}

.project-owner {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.avatar-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
}

.owner-avatar {
  font-size: 12px;
  flex-shrink: 0;
}

.no-owner {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.star-icon {
  cursor: pointer;
  padding: 4px;
  border-radius: 2px;
  transition: all 0.2s ease;
  font-size: 16px;
  opacity: 0.6;
  display: flex;
  align-items: center;
}

.star-icon:hover {
  opacity: 1;
  background: var(--color-bg-tertiary);
}

.star-icon.active {
  opacity: 1;
  color: var(--color-warning);
}

.action-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 2px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-trigger:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

:deep(.delete-item) {
  color: var(--color-danger);
}

:deep(.delete-item:hover) {
  background: var(--color-danger-light);
}
</style>
