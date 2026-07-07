<template>
  <div class="project-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <nav class="tab-nav">
            <a
              v-for="tab in tabs"
              :key="tab.key"
              :class="['tab-item', { active: activeTab === tab.key }]"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </a>
          </nav>
        </div>

        <div class="header-right">
          <div class="create-btn" @click="handleCreateProject">
            <div class="plus-icon"></div>
            创建项目
          </div>
        </div>
      </div>
    </header>

    <main class="page-content">
      <div class="content-container">
        <section class="projects-display">
          <!-- 常用项目 - 只在"我参与的"tab显示 -->
          <FavoriteProjects
            v-if="activeTab === 'projects'"
            :projects="favoriteProjects"
            :loading="projectStore.loading"
            @view="handleView"
            @toggle-favorite="toggleFavorite"
            @navigate="handleNavigate"
          />

          <!-- 全部项目 -->
          <AllProjects
            :projects="filteredProjects"
            :loading="projectStore.loading"
            :search-keyword="searchKeyword"
            :columns="tableColumns"
            :empty-message="getEmptyMessage(activeTab)"
            @search="handleSearchChange"
            @create="handleCreateProject"
            @view="handleView"
            @toggle-favorite="toggleFavorite"
            @delete="handleDelete"
          />
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
/**
 * ProjectList - 项目列表页面
 * 使用子组件拆分，保持主组件简洁
 */
import { useProjectStore } from '@/stores/modules/project'
import { useProjectList } from '@/composables/project/useProjectList'
import FavoriteProjects from './components/FavoriteProjects.vue'
import AllProjects from './components/AllProjects.vue'

const projectStore = useProjectStore()

const {
  activeTab,
  searchKeyword,
  favoriteProjects,
  filteredProjects,
  tabs,
  tableColumns,
  handleSearchChange,
  handleCreateProject,
  handleView,
  handleNavigate,
  toggleFavorite,
  handleDelete,
  getEmptyMessage
} = useProjectList()
</script>

<style scoped>
/* ==================== 页面布局 ==================== */
.project-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.page-header {
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.content-container {
  height: 100%;
  padding: 0;
}

/* ==================== 头部导航 ==================== */
.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tab-nav {
  display: flex;
  gap: 32px;
}

.tab-item {
  font-size: 14px;
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;
  font-weight: 500;
}

.tab-item:hover {
  color: var(--color-primary);
}

.tab-item.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 2px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}

.create-btn:hover {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

.plus-icon {
  width: 14px;
  height: 14px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
}

/* ==================== 项目展示区域 ==================== */
.projects-display {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ==================== 响应式布局 ==================== */
@media (max-width: 768px) {
  .projects-display {
    padding: 16px;
    gap: 16px;
  }

  .header-right {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .tab-nav {
    gap: 16px;
  }

  .tab-item {
    font-size: 14px;
  }

  .create-btn {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 16px;
  }

  .tab-nav {
    gap: 16px;
  }

  .tab-item {
    font-size: 14px;
  }
}
</style>
