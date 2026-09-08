<template>
  <div class="project-navigation" :class="{ collapsed }">
    <!-- 导航菜单 -->
    <nav class="nav-menu">
      <!-- 核心功能 -->
      <div class="nav-group">
        <ul class="nav-list">
          <li
            v-for="item in navItems"
            :key="item.key"
            :class="['nav-item', { active: activeMenu === item.key }]"
            :title="collapsed ? item.label : ''"
            @click="handleNavClick(item.key)"
          >
            <div class="nav-item-content">
              <el-icon class="nav-icon" :size="18">
                <component :is="item.icon" />
              </el-icon>
              <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
            </div>
          </li>
        </ul>
      </div>

      <!-- 设置 -->
      <div class="nav-group nav-group-settings">
        <span v-if="!collapsed" class="nav-group-title">设置</span>
        <ul class="nav-list">
          <li
            :class="['nav-item', { active: activeMenu === 'settings' }]"
            :title="collapsed ? '项目设置' : ''"
            @click="handleNavClick('settings')"
          >
            <div class="nav-item-content">
              <el-icon class="nav-icon" :size="18">
                <Setting />
              </el-icon>
              <span v-if="!collapsed" class="nav-label">项目设置</span>
            </div>
          </li>
        </ul>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DataAnalysis,
  List,
  Setting,
  Collection,
  Monitor,
  Document,
  Cpu,
  Aim
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { PROJECT_ROUTE_PREFIX } from '@/router/constants'

defineProps({
  projectName: {
    type: String,
    default: '未命名项目'
  },
  projectStatus: {
    type: String,
    default: 'active'
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()
const route = useRoute()

const NAV_ITEMS = [
  { key: 'overview', label: '项目概览', icon: DataAnalysis },
  { key: 'testcases', label: '测试用例', icon: List },
  { key: 'requirements', label: '需求管理', icon: Document },
  { key: 'apitest', label: '接口测试', icon: Monitor },
  { key: 'environments', label: '环境管理', icon: Cpu },
  { key: 'knowledge', label: '知识库', icon: Collection },
  { key: 'codecheck', label: '代码检查', icon: Aim }
]

const ROUTE_MAP = {
  overview: '',
  testcases: '/testcases',
  requirements: '/requirements',
  apitest: '/apitest',
  environments: '/environments',
  knowledge: '/knowledge',
  codecheck: '/codecheck',
  settings: '/settings'
}

const navItems = NAV_ITEMS

const activeMenu = computed(() => {
  // 匹配 /p/:code/xxx 格式
  const match = route.path.match(/^\/p\/[^/]+\/([^/]*)/)
  if (match) {
    const navKey = match[1] || 'overview'
    const allKeys = [...NAV_ITEMS.map(i => i.key), 'settings']
    return allKeys.includes(navKey) ? navKey : 'overview'
  }
  return 'overview'
})

const projectId = computed(() => route.params.code || route.params.id || route.params.projectId)

const handleNavClick = (key) => {
  if (!projectId.value) {
    ElMessage.error('缺少项目ID，无法导航')
    return
  }

  const suffix = ROUTE_MAP[key]
  const targetRoute = suffix
    ? `${PROJECT_ROUTE_PREFIX}/${projectId.value}${suffix}`
    : `${PROJECT_ROUTE_PREFIX}/${projectId.value}/`

  // 避免重复跳转到当前路由引起回弹
  if (route.path === targetRoute || route.path + '/' === targetRoute || route.path === targetRoute + '/') return

  router.push(targetRoute)
}
</script>

<style scoped>
.project-navigation {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

/* 导航菜单 */
.nav-menu {
  flex: 1;
  padding: 24px 0;
  overflow-y: auto;
}

.nav-menu::-webkit-scrollbar {
  width: 6px;
}

.nav-menu::-webkit-scrollbar-track {
  background: transparent;
}

.nav-menu::-webkit-scrollbar-thumb {
  background: var(--color-border-primary);
  border-radius: 2px;
}

.nav-menu::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-light);
}

.nav-group {
  margin-bottom: 4px;
}

.nav-group-settings {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary);
}

.nav-group-title {
  display: block;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  letter-spacing: 0;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin: 1px 8px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.nav-item:hover {
  background: var(--color-primary-light);
}

.nav-item.active {
  background: var(--color-primary-light);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.nav-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.nav-item:hover .nav-icon {
  color: var(--color-primary);
}

.nav-item.active .nav-icon {
  color: var(--color-primary);
}

.nav-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item.active .nav-label {
  color: var(--color-primary);
  font-weight: 500;
}

/* 收起状态 */
.project-navigation.collapsed .nav-menu {
  padding: 12px 0;
}

.project-navigation.collapsed .nav-group {
  margin-bottom: 8px;
}

.project-navigation.collapsed .nav-group-settings {
  margin-top: 8px;
  padding-top: 8px;
}

.project-navigation.collapsed .nav-item {
  justify-content: center;
  padding: 10px 0;
  margin: 2px 8px;
}

.project-navigation.collapsed .nav-item-content {
  justify-content: center;
  gap: 0;
}

.project-navigation.collapsed .nav-item.active::before {
  display: none;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .nav-group-title {
    padding: 8px 12px;
  }

  .nav-item {
    padding: 8px 10px;
    margin: 1px 6px;
  }

  .nav-label {
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .project-navigation {
    flex-direction: row;
    align-items: center;
    padding: 0 12px;
    height: 56px;
    border-bottom: 1px solid var(--color-border-primary);
  }

  .nav-menu {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0;
    flex: 1;
    display: flex;
    align-items: center;
  }

  .nav-group {
    display: flex;
    align-items: center;
    margin: 0;
    padding: 0 8px;
    border-right: 1px solid var(--color-border-primary);
  }

  .nav-group:last-child {
    border-right: none;
  }

  .nav-group-title {
    display: none;
  }

  .nav-list {
    display: flex;
    gap: 4px;
  }

  .nav-item {
    margin: 0;
    padding: 8px 12px;
    white-space: nowrap;
  }

  .nav-item.active::before {
    display: none;
  }

  .nav-item.active {
    background: var(--color-primary-light);
  }
}
</style>
