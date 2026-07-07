<template>
  <div class="all-projects">
    <div class="projects-table-card">
      <div class="section-header">
        <div class="project-header">
          <div class="header-tabs">
            <div class="tab-item active">全部项目</div>
          </div>
          <div class="header-actions">
            <div class="input-container">
              <el-input
                :model-value="searchKeyword"
                placeholder="搜索"
                class="search-input"
                :prefix-icon="Search"
                clearable
                @update:model-value="$emit('search', $event)"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="content-wrapper all-projects-wrapper">
        <!-- 加载状态 -->
        <div v-if="loading" class="skeleton-container">
          <div class="custom-list">
            <div class="table-wrapper">
              <ProjectTableHeader :columns="columns" />
              <LoadingSkeleton
                v-for="i in 5"
                :key="'skeleton-' + i"
                type="table-row"
                :columns="columns.length"
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <ProjectTableEmpty
          v-else-if="projects.length === 0"
          :message="emptyMessage"
          show-action
          action-text="创建项目"
          @action="$emit('create')"
        />

        <!-- 项目列表 -->
        <div v-else class="table-container">
          <div class="custom-list">
            <div class="table-wrapper">
              <ProjectTableHeader :columns="columns" />
              <ProjectTableRow
                v-for="project in projects"
                :key="project.id"
                :project="project"
                :columns="columns"
                @view="$emit('view', $event)"
                @toggle-favorite="$emit('toggleFavorite', $event)"
                @delete="$emit('delete', $event)"
              />
            </div>

            <div class="bottom-create">
              <div class="create-button" @click="$emit('create')">
                <div class="add-icon" />
                创建项目
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * AllProjects - 全部项目组件
 * @property {Array} projects - 项目列表
 * @property {boolean} loading - 加载状态
 * @property {string} searchKeyword - 搜索关键词
 * @property {Array} columns - 列配置
 * @property {string} emptyMessage - 空状态消息
 */
import { Search } from '@element-plus/icons-vue'
import { LoadingSkeleton } from '@/components/common'
import ProjectTableHeader from './ProjectTableHeader.vue'
import ProjectTableRow from './ProjectTableRow.vue'
import ProjectTableEmpty from './ProjectTableEmpty.vue'

defineProps({
  projects: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  searchKeyword: {
    type: String,
    default: ''
  },
  columns: {
    type: Array,
    required: true
  },
  emptyMessage: {
    type: String,
    default: '暂无项目'
  }
})

defineEmits(['search', 'create', 'view', 'toggleFavorite', 'delete'])
</script>

<style scoped>
.all-projects {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.projects-table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #fff;
}

.section-header {
  flex-shrink: 0;
}

.project-header {
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: #fff;
  border-bottom: 1px solid var(--color-border-secondary);
}

.header-tabs {
  display: flex;
  align-items: center;
}

.tab-item {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 600;
  padding: 8px 0;
  cursor: pointer;
}

.tab-item.active {
  color: var(--color-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.input-container {
  display: flex;
  align-items: center;
}

.search-input {
  width: 200px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: none;
  border: 1px solid var(--color-border-primary);
}

.search-input :deep(.el-input__wrapper:focus-within) {
  border-color: var(--color-primary);
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
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

.skeleton-container {
  padding: 16px 0;
}

.custom-list {
  width: 100%;
  background: #fff;
}

.table-wrapper {
  width: 100%;
}

.table-container {
  width: 100%;
}

.bottom-create {
  padding: 4px 8px;
  border-top: 1px solid var(--color-border-primary);
}

.create-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 8px 12px;
  background: transparent;
  color: var(--color-text-secondary);
  border: 2px dashed var(--color-border-primary);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.create-button:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary-hover);
  color: var(--color-primary-hover);
}

.create-button:active {
  background: var(--color-primary-light);
}

.add-icon {
  width: 18px;
  height: 18px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230066cc'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  transition: transform 0.25s ease;
}

.create-button:hover .add-icon {
  transform: rotate(90deg);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230052a3'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3E%3C/svg%3E");
}

@media (max-width: 768px) {
  .project-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-input {
    width: 100%;
    max-width: 200px;
  }
}
</style>
