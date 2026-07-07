<template>
  <div class="favorite-projects">
    <div class="section-card favorite-projects-card">
      <div class="section-title">常用项目</div>

      <div class="content-wrapper favorite-wrapper">
        <LoadingSkeleton v-if="loading" type="multiple" :count="3" />

        <ProjectEmpty
          v-else-if="projects.length === 0"
          icon=""
          title="暂无常用项目"
          description="点击项目右侧的星标图标添加常用项目"
          :show-action="false"
        />

        <div v-else class="project-cards-grid">
          <ProjectCard
            v-for="project in projects"
            :key="project.id"
            :project="project"
            @card-click="$emit('view', $event)"
            @toggle-favorite="$emit('toggleFavorite', $event)"
            @more-action="$emit('view', $event)"
            @navigate="$emit('navigate', $event)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * FavoriteProjects - 常用项目组件
 * @property {Array} projects - 项目列表
 * @property {boolean} loading - 加载状态
 */
import { LoadingSkeleton } from '@/components/common'
import ProjectCard from './ProjectCard.vue'
import ProjectEmpty from './ProjectEmpty.vue'

defineProps({
  projects: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['view', 'toggleFavorite', 'navigate'])
</script>

<style scoped>
.section-card {
  background: #fff;
  padding: 20px 24px;
}

.section-title {
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 22px;
  font-weight: 600;
  margin-bottom: 16px;
}

.content-wrapper {
  max-height: 180px;
  overflow-y: auto;
  overflow-x: hidden;
}

.content-wrapper::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: var(--color-text-placeholder);
  border-radius: 2px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

.project-cards-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
</style>
