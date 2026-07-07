<template>
  <div class="project-card-item" @click="onCardClick">
    <div class="card-top">
      <div
        class="card-avatar"
        :style="{ backgroundColor: project.iconColor || 'var(--color-primary)' }"
      >
        <el-icon :size="20">
          <component :is="currentIconComponent" />
        </el-icon>
      </div>
      <div class="card-top-right">
        <div class="card-name">{{ project.name }}</div>
        <div class="card-desc" :class="{ 'desc-none': !project.description }">
          {{ project.description || '未填写项目描述' }}
        </div>
      </div>
      <div
        class="star-icon"
        :class="{ active: project.isFavorite }"
        :title="project.isFavorite ? '取消常用项目' : '添加常用项目'"
        @click.stop="onToggleFavorite"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
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

    <div class="card-bottom">
      <div class="card-links">
        <div class="link-list">
          <a
            v-if="hasFeature('testcase')"
            href="#"
            class="link-item"
            :title="`测试用例: ${project.testCases || 0}`"
            @click.stop.prevent="onNavigate('testcase')"
          >
            <span class="link-icon">📝</span>
          </a>
          <a
            v-if="hasFeature('testplan')"
            href="#"
            class="link-item"
            :title="`测试计划: ${project.testPlans || 0}`"
            @click.stop.prevent="onNavigate('testplan')"
          >
            <span class="link-icon">📋</span>
          </a>
          <a
            v-if="hasFeature('bug')"
            href="#"
            class="link-item"
            :title="`缺陷: ${project.bugs || 0}`"
            @click.stop.prevent="onNavigate('bug')"
          >
            <span class="link-icon">🐛</span>
          </a>
          <a
            href="#"
            class="link-item"
            title="项目设置"
            @click.stop.prevent="onNavigate('settings')"
          >
            <span class="link-icon">⚙️</span>
          </a>
        </div>
      </div>

      <div class="card-actions">
        <div
          class="action-trigger"
          title="更多操作"
          @click.stop="onMoreAction"
        >
          <svg
            fill="currentColor"
            preserveAspectRatio="xMidYMid meet"
            height="16"
            width="16"
            viewBox="0 0 16 16"
          >
            <g>
              <path
                d="M8 6.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm5.5 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm-11 0a1.5 1.5 0 110 3 1.5 1.5 0 010-3z"
              />
            </g>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getIconComponent } from '@/utils/icons'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cardClick', 'toggleFavorite', 'moreAction', 'navigate'])

const currentIconComponent = computed(() => {
  const iconName = props.project.icon || 'Folder'
  return getIconComponent(iconName)
})

const FEATURE_CONFIG = {
  testcase: { minCount: 0, field: 'testCases' },
  testplan: { minCount: 0, field: 'testPlans' },
  bug: { minCount: 0, field: 'bugs' }
}

const hasFeature = (featureType) => {
  const config = FEATURE_CONFIG[featureType]
  if (!config) return true
  const count = props.project[config.field] || 0
  return count >= config.minCount
}

const onCardClick = () => {
  emit('cardClick', props.project)
}

const onToggleFavorite = () => {
  emit('toggleFavorite', props.project)
}

const onMoreAction = () => {
  emit('moreAction', props.project)
}

const onNavigate = (moduleType) => {
  emit('navigate', moduleType, props.project)
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
  color: white;
  text-transform: uppercase;
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

.card-desc.desc-none {
  color: var(--color-text-tertiary);
  font-style: italic;
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
  flex-shrink: 0;
}

.star-icon:hover {
  opacity: 1;
  background: var(--color-bg-tertiary);
}

.star-icon.active {
  opacity: 1;
  color: var(--color-warning);
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
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
}

.link-item:hover {
  background: var(--color-primary);
  color: white;
  transform: translateY(-1px);
}

.link-icon {
  font-size: 14px;
}

.card-actions {
  margin-left: 8px;
}

.action-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 2px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-trigger:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-card-item {
    width: 100%;
    margin-right: 0;
  }
}
</style>
