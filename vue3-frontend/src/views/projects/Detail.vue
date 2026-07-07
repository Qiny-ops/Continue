<template>
  <div class="project-detail-page">
    <!-- 主体内容区域 - 包含左侧导航和主内容 -->
    <div class="body-container">
      <!-- 左侧导航栏 -->
      <aside class="left-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-content">
          <ProjectNavigation
            :project-name="project?.name || '未命名项目'"
            :project-status="project?.status || 'active'"
            :collapsed="sidebarCollapsed"
          />
        </div>
        <div class="sidebar-footer">
          <div class="sidebar-toggle" @click="toggleSidebar">
            <el-icon :size="16">
              <ArrowLeft v-if="!sidebarCollapsed" />
              <ArrowRight v-else />
            </el-icon>
          </div>
        </div>
      </aside>

      <!-- 主要内容区域 -->
      <main class="page-content">
        <div class="content-container">
          <!-- 加载状态 -->
          <div v-if="projectStore.loading" class="loading-container">
            <div class="loading-spinner" />
            <p class="loading-text">正在加载项目详情...</p>
          </div>

          <!-- 错误状态 -->
          <div v-else-if="projectStore.error" class="error-container">
            <div class="error-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
            </div>
            <h3 class="error-title">加载失败</h3>
            <p class="error-description">{{ projectStore.error }}</p>
            <el-button type="primary" class="retry-button" @click="fetchProjectDetail">
              重试
            </el-button>
          </div>

          <!-- 项目详情内容 -->
          <div v-else-if="project" class="project-content">
            <!-- 动态内容模块 -->
            <component
              :is="currentComponent"
              v-if="currentComponent"
              :project="project"
            />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineAsyncComponent, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElButton } from 'element-plus'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/modules/project'
import ProjectNavigation from './components/ProjectNavigation.vue'

const route = useRoute()
const projectStore = useProjectStore()

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const project = computed(() => projectStore.currentProject)

const TAB_TO_ROUTE = {
  overview: '',
  testcases: '/testcases',
  apitest: '/apitest',
  knowledge: '/knowledge',
  settings: '/settings'
}

const ROUTE_TO_TAB = Object.fromEntries(
  Object.entries(TAB_TO_ROUTE).map(([tab, suffix]) => [suffix || 'base', tab])
)

const COMPONENT_MAP = {
  overview: defineAsyncComponent(() => import('./components/ProjectOverview.vue')),
  testcases: defineAsyncComponent(() => import('./components/ProjectTestCases.vue')),
  apitest: defineAsyncComponent(() => import('@/views/apitest/Index.vue')),
  'apitest-environments': defineAsyncComponent(() => import('@/views/apitest/Environment.vue')),
  knowledge: defineAsyncComponent(() => import('@/views/knowledge/Index.vue')),
  settings: defineAsyncComponent(() => import('./Settings.vue')),
  'manage-repo': defineAsyncComponent(() => import('@/views/testcase/ManageRepo.vue')),
  'manage-version': defineAsyncComponent(() => import('@/views/testcase/ManageVersion.vue'))
}

const activeTab = ref('overview')

const currentComponent = computed(() => COMPONENT_MAP[activeTab.value])

const setActiveTabFromRoute = () => {
  const path = route.path

  // 处理 t/manage-repo 和 t/manage-version 路由
  if (path.includes('/t/manage-repo')) {
    activeTab.value = 'manage-repo'
  } else if (path.includes('/t/manage-version')) {
    activeTab.value = 'manage-version'
  } else if (path.includes('/apitest/environments')) {
    // 环境管理路由
    activeTab.value = 'apitest-environments'
  } else if (path.includes('/apitest')) {
    // 接口测试路由
    activeTab.value = 'apitest'
  } else {
    // 匹配 /p/:code/xxx 格式
    const match = path.match(/^\/p\/[^/]+(\/[^/]*)?/)
    if (match) {
      const suffix = match[1] || ''
      activeTab.value = ROUTE_TO_TAB[suffix] || ROUTE_TO_TAB['base']
    } else {
      activeTab.value = ROUTE_TO_TAB['base']
    }
  }
}

watch(() => route.path, setActiveTabFromRoute)

onMounted(() => {
  // 项目信息由路由守卫 (guards.js afterEach) 统一获取
  // 这里只处理 tab 状态，不再重复请求项目详情
  setActiveTabFromRoute()
})
</script>

<style scoped>
/* 页面布局 */
.project-detail-page {
  height: 100%;
  background: var(--color-bg-secondary);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 主体容器 */
.body-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 左侧导航栏 - 与 CODING 一致 */
.left-sidebar {
  width: 192px;
  min-width: 192px;
  max-width: 192px;
  flex: 0 0 192px;
  background: #fff;
  border-right: 1px solid var(--color-border-primary);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.2s ease, min-width 0.2s ease, max-width 0.2s ease, flex 0.2s ease;
}

.left-sidebar.collapsed {
  width: 64px;
  min-width: 64px;
  max-width: 64px;
  flex: 0 0 64px;
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--color-bg-tertiary);
  display: flex;
  justify-content: flex-end;
}

/* 收起按钮 - 悬浮圆形按钮 */
.sidebar-toggle {
  width: 28px;
  height: 28px;
  background: #fff;
  border: 1px solid var(--color-border-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.sidebar-toggle:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
}

.sidebar-toggle:hover .el-icon {
  color: #fff;
}

.sidebar-toggle .el-icon {
  color: var(--color-text-secondary);
  transition: color 0.2s ease;
}

/* 主要内容区域 */
.page-content {
  flex: 1;
  overflow: hidden;
  background: var(--color-bg-secondary);
  display: flex;
  flex-direction: column;
}

.content-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}


/* 加载和错误状态 */
.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--color-text-secondary);
  text-align: center;
  background: #fff;
  margin: 24px;
  border-radius: 2px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-primary);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.error-icon {
  color: var(--color-danger);
  margin-bottom: 16px;
}

.error-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.error-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px 0;
  max-width: 300px;
  line-height: 1.5;
}

.retry-button {
  padding: 8px 16px;
  border-radius: 2px;
  font-size: 14px;
}

/* 项目内容 */
.project-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>