<template>
  <div class="project-card-item empty-card">
    <div class="card-top">
      <div class="card-avatar">
        <span class="avatar-icon">{{ icon }}</span>
      </div>
      <div class="card-top-right">
        <div class="card-name">{{ title }}</div>
        <div class="card-desc">{{ description }}</div>
      </div>
    </div>
    <div class="card-bottom">
      <div class="card-links">
        <div class="link-list">
          <span class="link-item placeholder">
            <span class="link-icon">📝</span>
          </span>
          <span class="link-item placeholder">
            <span class="link-icon">📋</span>
          </span>
          <span class="link-item placeholder">
            <span class="link-icon">🐛</span>
          </span>
          <span class="link-item placeholder">
            <span class="link-icon">⚙️</span>
          </span>
        </div>
      </div>

      <div class="card-actions">
        <el-button
          v-if="showAction"
          type="primary"
          size="small"
          @click="onAction"
        >
          {{ actionText }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElButton } from 'element-plus'

defineProps({
  title: {
    type: String,
    default: '暂无项目数据'
  },
  description: {
    type: String,
    default: '还没有项目，创建第一个项目开始测试之旅吧！'
  },
  icon: {
    type: String,
    default: '📊'
  },
  showAction: {
    type: Boolean,
    default: true
  },
  actionText: {
    type: String,
    default: '创建第一个项目'
  }
})

const emit = defineEmits(['action'])

const onAction = () => {
  emit('action')
}
</script>

<style scoped>
.project-card-item {
  margin-right: 16px;
  margin-bottom: 16px;
  width: 256px;
  min-width: 256px;
  padding: 0 16px;
  background: #fff;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.project-card-item:hover {
  border-color: var(--color-primary);
}

.empty-card {
  cursor: default;
}

.empty-card:hover {
  border-color: var(--color-border-primary);
}

.card-top {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 0;
}

.card-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  background: var(--color-bg-tertiary);
}

.avatar-icon {
  font-size: 20px;
}

.card-top-right {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 15px;
  color: var(--color-text-primary);
  line-height: 20px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 18px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--color-bg-tertiary);
}

.card-links {
  flex: 1;
}

.link-list {
  display: flex;
  gap: 8px;
}

.link-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 2px;
  background: var(--color-bg-secondary);
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.link-item.placeholder {
  opacity: 0.5;
}

.link-icon {
  font-size: 14px;
}

.card-actions {
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-card-item {
    width: 100%;
    margin-right: 0;
  }
}
</style>
