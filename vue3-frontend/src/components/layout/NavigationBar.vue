<template>
  <div class="navigation-layout">
    <!-- 左侧活动栏 -->
    <nav class="activity-bar" role="navigation" aria-label="主导航">
      <!-- Logo区域 -->
      <div class="logo-container">
        <img
          src="/logo.png"
          alt="AI测试平台"
          class="logo"
          @click="handleLogoClick"
          role="button"
          tabindex="0"
          @keydown.enter="handleLogoClick"
        />
      </div>

      <!-- 活动项列表 -->
      <ul class="activity-items" role="menubar">
        <li
          v-for="item in activityItems"
          :key="item.key"
          :class="getActivityItemClass(item.key)"
          @click="handleActivityClick(item)"
          @mouseenter="handleActivityMouseEnter(item)"
          @mouseleave="handleActivityMouseLeave"
          role="menuitem"
          :aria-current="activeActivity === item.key ? 'page' : undefined"
          :aria-label="item.tooltip"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span class="activity-name">{{ getShortName(item.tooltip) }}</span>
          <span class="activity-tooltip" role="tooltip">{{ item.tooltip }}</span>
        </li>
      </ul>
    </nav>

    <!-- 右侧主区域 -->
    <div class="main-area">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <!-- 面包屑 -->
          <el-breadcrumb separator="/" v-if="breadcrumbs.length > 0">
            <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
              <router-link v-if="item.path && index < breadcrumbs.length - 1" :to="item.path">{{ item.title }}</router-link>
              <span v-else :class="{ 'breadcrumb-current': index === breadcrumbs.length - 1 }">{{ item.title }}</span>
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="top-bar-right">
          <!-- 用户信息 -->
          <el-dropdown trigger="click" @command="handleUserCommand">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userInitial }}
              </el-avatar>
              <span class="user-name">{{ userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区域 -->
      <main class="content-panel">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ArrowDown, User, SwitchButton } from '@element-plus/icons-vue'
import { useNavigationStore } from '@/stores/modules/nav'
import { useUserStore } from '@/stores/modules/user'
import { useProjectStore } from '@/stores/modules/project'

// Router
const router = useRouter()
const route = useRoute()

// Store
const navigationStore = useNavigationStore()
const userStore = useUserStore()
const projectStore = useProjectStore()
const { activeActivity } = storeToRefs(navigationStore)
const { activityItems, getShortName, handleActivityMouseLeave: storeHandleActivityMouseLeave } = navigationStore

// 用户信息
const userName = computed(() => {
  return userStore.user?.name || userStore.user?.username || '用户'
})

const userInitial = computed(() => {
  const name = userName.value
  return name ? name.charAt(0).toUpperCase() : 'U'
})

// 面包屑
const breadcrumbs = computed(() => {
  const crumbs = []
  const path = route.path

  // 项目详情 - 一级显示导航菜单名称，二级显示项目名称
  const projectMatch = path.match(/^\/p\/([^/]+)/)
  if (projectMatch) {
    const projectIdentifier = projectMatch[1]
    crumbs.push({ title: '项目管理', path: '/projects' })
    const projectName = projectStore.currentProject?.name || projectIdentifier
    crumbs.push({ title: projectName, path: `/p/${projectIdentifier}` })

    if (path.includes('/testcases')) {
      crumbs.push({ title: '测试用例' })
    } else if (path.includes('/apitest')) {
      crumbs.push({ title: '接口测试' })
    } else if (path.includes('/knowledge')) {
      crumbs.push({ title: '知识库' })
    } else if (path.includes('/settings')) {
      crumbs.push({ title: '项目设置' })
    }
  }

  // 项目列表页
  if (path.startsWith('/projects') && !projectMatch) {
    crumbs.push({ title: '项目管理', path: '/projects' })
  }

  // 系统管理
  if (path.startsWith('/system')) {
    crumbs.push({ title: '系统管理' })
    if (path.includes('/users')) {
      crumbs.push({ title: '用户管理' })
    } else if (path.includes('/roles')) {
      crumbs.push({ title: '角色管理' })
    } else if (path.includes('/permissions')) {
      crumbs.push({ title: '权限管理' })
    }
  }

  return crumbs
})

// Route mapping
const routeMap = {
  '/projects': 'project',
  '/p/': 'project',
  '/system/': 'system'
}

// Methods
const handleActivityClick = (item) => {
  navigationStore.handleActivityClick(item, router)
}

const handleActivityMouseEnter = (item) => {
  navigationStore.hoverActivity(item)
}

const handleActivityMouseLeave = () => {
  storeHandleActivityMouseLeave()
}

const handleLogoClick = () => {
  router.push('/projects')
}

const handleUserCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

const getActivityItemClass = (itemKey) => {
  const classes = ['activity-item']

  if (activeActivity.value === itemKey) {
    classes.push('active')
  }

  return classes
}

const updateActiveActivityFromRoute = () => {
  const path = route.path

  for (const [prefix, activity] of Object.entries(routeMap)) {
    if (path.startsWith(prefix)) {
      navigationStore.setActiveActivity(activity)
      return
    }
  }

  if (path === '/' || path === '') {
    navigationStore.setActiveActivity('project')
  }
}

// Watchers
watch(() => route.path, updateActiveActivityFromRoute, { immediate: true })
</script>

<style scoped>
.navigation-layout {
  display: flex;
  height: 100vh;
  min-height: 600px;
  background: var(--color-bg-secondary);
  overflow: hidden;
}

/* 左侧活动栏 */
.activity-bar {
  width: 64px;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border-right: 1px solid var(--color-border-primary);
  box-shadow: var(--shadow-sm);
  z-index: 50;
  flex-shrink: 0;
}

.logo-container {
  margin-bottom: 16px;
}

.logo {
  width: 48px;
  height: 48px;
  object-fit: contain;
  cursor: pointer;
  transition: transform 0.15s ease-out;
  border-radius: 2px;
}

.logo:hover {
  transform: scale(1.1);
}

.activity-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
  width: 100%;
}

.activity-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin: 0 auto;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid transparent;
  transition: all 0.15s ease-out;
  position: relative;
}

.activity-item:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.activity-item.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.activity-name {
  font-size: 10px;
  font-weight: 500;
  margin-top: 2px;
  color: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 40px;
}

.activity-tooltip {
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%);
  padding: 6px 12px;
  background: var(--color-text-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  border-radius: 2px;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.15s ease-out;
  pointer-events: none;
  z-index: 100;
  box-shadow: var(--shadow-md);
}

.activity-tooltip::before {
  content: '';
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-right-color: var(--color-text-primary);
}

.activity-item:hover .activity-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(-50%) translateX(4px);
}

/* 右侧主区域 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏 */
.top-bar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 2px;
  transition: background 0.2s;
}

.user-info:hover {
  background: var(--color-bg-tertiary);
}

.user-avatar {
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.user-name {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

/* 内容区域 */
.content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-bg-secondary);
}

/* 面包屑当前页样式 */
.breadcrumb-current {
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 面包屑链接样式 - 不加粗 */
:deep(.el-breadcrumb__inner a) {
  font-weight: 400 !important;
  color: var(--color-text-secondary);
}

:deep(.el-breadcrumb__inner a:hover) {
  color: var(--color-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .activity-bar {
    width: 56px;
    padding: 4px;
  }

  .activity-item {
    width: 40px;
    height: 40px;
  }

  .activity-name {
    display: none;
  }

  .top-bar {
    padding: 0 16px;
  }

  .user-name {
    display: none;
  }
}
</style>
