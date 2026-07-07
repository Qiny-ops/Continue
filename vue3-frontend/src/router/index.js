import { createRouter, createWebHistory } from 'vue-router'
import { setupRouterGuards } from './guards'
import { ROUTE_NAMES } from './constants'

import authRoutes from './modules/auth'
import projectRoutes from './modules/project'
import systemRoutes from './modules/system'

const routes = [
  { path: '/', redirect: '/projects' },
  ...authRoutes,
  ...projectRoutes,
  ...systemRoutes,
  // Web自动化测试验证页面
  {
    path: '/webtest',
    name: 'WebTest',
    component: () => import('@/views/webtest/TestPage.vue'),
    meta: {
      title: 'Web自动化测试',
      requiresAuth: false
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: ROUTE_NAMES.NOT_FOUND,
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      title: '页面未找到',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

setupRouterGuards(router)

router.afterEach(() => {
})

export default router
