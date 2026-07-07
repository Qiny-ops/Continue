import { useUserStore } from '@/stores/modules/user'
import { usePermissionStore } from '@/stores/modules/permission'
import { useProjectStore } from '@/stores/modules/project'
import { WHITE_LIST } from './constants'
import projectApi from '@/api/modules/project'

const pendingProjectRequests = new Map()

export function setupRouterGuards(router) {
  router.beforeEach(async (to) => {
    const userStore = useUserStore()
    const hasToken = !!userStore.token

    if (hasToken && !userStore.sessionRestored) {
      userStore.setSessionRestored(true)
      try {
        await userStore.restoreSession()
      } catch {
        userStore.reset()
        return '/login'
      }
    }

    if (WHITE_LIST.includes(to.path)) {
      return true
    }

    if (to.meta.requiresAuth !== false && !userStore.isLoggedIn) {
      if (!hasToken) {
        return {
          path: '/login',
          query: { redirect: to.fullPath }
        }
      }
    }

    if (to.meta.permissions && Array.isArray(to.meta.permissions)) {
      const hasPermission = to.meta.permissions.some(perm => userStore.hasPermission(perm))
      if (!hasPermission) {
        return '/projects'
      }
    }

    if (to.meta.roles && Array.isArray(to.meta.roles)) {
      const userRole = userStore.user?.system_role || userStore.user?.role
      const hasRole = to.meta.roles.includes(userRole)
      if (!hasRole) {
        return '/projects'
      }
    }

    if (to.meta.projectPermissions && Array.isArray(to.meta.projectPermissions)) {
      const permissionStore = usePermissionStore()
      const hasProjectPermission = to.meta.projectPermissions.some(
        perm => permissionStore.hasProjectPermission(perm)
      )
      if (!hasProjectPermission) {
        return '/projects'
      }
    }

    if (to.meta.projectAdmin) {
      const permissionStore = usePermissionStore()
      if (!permissionStore.isCurrentProjectAdmin) {
        return '/projects'
      }
    }

    return true
  })

  router.afterEach(async (to) => {
    const title = to.meta?.title
    if (title) {
      document.title = `${title} - 测试管理平台`
    }

    // 匹配项目路由: /p/:code/...
    const projectMatch = to.path.match(/^\/p\/([^/]+)/)
    if (projectMatch && to.meta.requiresAuth !== false) {
      const projectCode = projectMatch[1]

      const permissionStore = usePermissionStore()
      const projectStore = useProjectStore()

      // 更新访问时间（异步执行，不阻塞导航）
      projectApi.updateVisitTime(projectCode).catch(() => {})

      if (projectStore.currentProject?.id !== projectCode &&
          projectStore.currentProject?.code !== projectCode) {

        if (pendingProjectRequests.has(projectCode)) {
          return
        }

        const requestPromise = (async () => {
          try {
            await projectStore.fetchProject(projectCode)
            await permissionStore.initProjectPermissions(projectCode)
          } catch {
          } finally {
            pendingProjectRequests.delete(projectCode)
          }
        })()

        pendingProjectRequests.set(projectCode, requestPromise)
      }
    }
  })

  router.onError(() => {
  })
}
