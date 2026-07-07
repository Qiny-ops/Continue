import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@/api/modules/auth'

const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000
let refreshTimer = null
let isRefreshing = false
let refreshPromise = null

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const roles = ref([])
  const token = ref(null)
  const sessionRestored = ref(false)
  const systemPermissions = ref([]) // 系统权限列表

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.system_role === 'admin')
  const userName = computed(() => user.value?.username || '')
  const userEmail = computed(() => user.value?.email || '')
  const isSessionRestored = computed(() => sessionRestored.value)

  const setSessionRestored = (value) => {
    sessionRestored.value = value
  }

  const clearRefreshTimer = () => {
    if (refreshTimer) {
      clearTimeout(refreshTimer)
      refreshTimer = null
    }
  }

  const scheduleTokenRefresh = () => {
    clearRefreshTimer()

    if (!token.value) return

    try {
      const payload = JSON.parse(atob(token.value.split('.')[1]))
      const expiresAt = payload.exp * 1000
      const now = Date.now()
      const timeUntilRefresh = expiresAt - now - TOKEN_REFRESH_THRESHOLD

      if (timeUntilRefresh <= 0) {
        refreshToken().catch(() => {
          clearRefreshTimer()
        })
        return
      }

      refreshTimer = setTimeout(async () => {
        try {
          await refreshToken()
        } catch {
          clearRefreshTimer()
        }
      }, timeUntilRefresh)
    } catch {
      clearRefreshTimer()
    }
  }

  const refreshToken = async () => {
    if (isRefreshing && refreshPromise) {
      return refreshPromise
    }

    isRefreshing = true
    refreshPromise = (async () => {
      try {
        const response = await authApi.refreshToken()
        if (response.code === 200 && response.data?.token) {
          token.value = response.data.token
          scheduleTokenRefresh()
          return response.data.token
        }
        throw new Error(response.message || 'Token刷新失败')
      } catch (error) {
        clearRefreshTimer()
        throw error
      } finally {
        isRefreshing = false
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  const login = async (credentials) => {
    const response = await authApi.login(credentials)

    if (!response || response.code !== 200) {
      throw new Error(response?.message || '登录失败')
    }

    const tokenValue = response.data?.token
    if (!tokenValue) {
      throw new Error('登录响应缺少 token')
    }

    user.value = response.data
    token.value = tokenValue
    // 保存系统权限
    systemPermissions.value = response.data?.system_permissions || []
    scheduleTokenRefresh()

    return response.data
  }

  const logout = async () => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch {
    } finally {
      user.value = null
      token.value = null
      roles.value = []
      systemPermissions.value = []
      clearRefreshTimer()
    }
  }

  const register = async (userData) => {
    const response = await authApi.register(userData)
    if (response.code === 201) {
      return response.data
    } else {
      throw new Error(response.message || '注册失败')
    }
  }

  const fetchUserInfo = async () => {
    const response = await authApi.getUserInfo()

    if (response && response.code === 200 && response.data) {
      user.value = response.data
      // 更新系统权限
      systemPermissions.value = response.data?.system_permissions || []
    } else if (response && response.id) {
      user.value = response
    } else {
      throw new Error(response?.message || '获取用户信息失败')
    }

    return user.value
  }

  const updateUserInfo = async (userData) => {
    const response = await authApi.updateUserInfo(userData)
    if (response.code === 200) {
      user.value = response.data
      return response.data
    } else {
      throw new Error(response.message || '更新失败')
    }
  }

  const hasPermission = (permission) => {
    if (!user.value) return false
    if (user.value.system_role === 'admin') return true
    return user.value.permissions?.includes(permission) || false
  }

  const hasSystemPermission = (permissionCode) => {
    if (!user.value) return false
    if (user.value.system_role === 'admin') return true
    return systemPermissions.value.includes(permissionCode)
  }

  const hasRole = (role) => {
    if (!user.value) return false
    return user.value.system_role === role
  }

  const restoreSession = async () => {
    if (token.value) {
      try {
        await fetchUserInfo()
        scheduleTokenRefresh()
        return true
      } catch {
        user.value = null
        token.value = null
        systemPermissions.value = []
        clearRefreshTimer()
        return false
      }
    }
    return false
  }

  const reset = () => {
    user.value = null
    token.value = null
    roles.value = []
    systemPermissions.value = []
    clearRefreshTimer()
  }

  return {
    user,
    roles,
    token,
    sessionRestored,
    systemPermissions,
    isLoggedIn,
    isAdmin,
    userName,
    userEmail,
    isSessionRestored,
    setSessionRestored,
    login,
    logout,
    register,
    fetchUserInfo,
    updateUserInfo,
    hasPermission,
    hasSystemPermission,
    hasRole,
    refreshToken,
    restoreSession,
    reset
  }
}, {
  persist: {
    key: 'user-store',
    paths: ['user', 'token', 'systemPermissions'],
    storage: localStorage
  }
})
