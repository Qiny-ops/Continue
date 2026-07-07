/**
 * 导航栏状态管理 Store
 * 管理导航栏的所有状态和交互逻辑
 * 集成缓存和性能优化
 */

import { defineStore } from 'pinia'
import { ref, reactive, markRaw, computed } from 'vue'
import navigationCache from '@/utils/nav-cache'
import { Odometer, Menu, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/modules/user'

// 所有可用的导航项定义
const allActivityItems = [
  { key: 'project', icon: markRaw(Menu), tooltip: '项目' },
  { key: 'system', icon: markRaw(Setting), tooltip: '系统管理', roles: ['admin'] }
]

export const useNavigationStore = defineStore('navigation', () => {
  // ==================== 状态定义 ====================

  const activeActivity = ref('project')
  const hoveredActivity = ref('')
  const searchQuery = ref('')
  const isAnimating = ref(false)

  const performanceState = reactive({
    lastActivityChange: 0,
    searchCount: 0,
    cacheHitRate: 0
  })

  // 根据用户权限过滤导航项
  const activityItems = computed(() => {
    const userStore = useUserStore()
    const userRole = userStore.user?.system_role || userStore.user?.role

    return allActivityItems.filter(item => {
      // 如果没有角色限制，则所有人可见
      if (!item.roles) return true
      // 有角色限制时，检查用户角色
      return item.roles.includes(userRole)
    })
  })

  // ==================== 计算属性 ====================

  const routeMap = {
    'project': '/projects',
    'system': '/system/users',
  }

  // ==================== 方法定义 ====================

  /**
   * 处理活动项点击事件
   * @param {Object} item - 点击的活动项对象
   * @param {Object} router - Vue Router实例
   */
  const handleActivityClick = (item, router) => {
    if (isAnimating.value) {
      return
    }

    performanceState.lastActivityChange = Date.now()
    isAnimating.value = true
    activeActivity.value = item.key

    setTimeout(() => {
      isAnimating.value = false
    }, 300)

    const targetRoute = routeMap[item.key]
    if (targetRoute && router) {
      router.push(targetRoute)
    }
  }

  /**
   * 处理活动项悬停事件
   * @param {Object} item - 悬停的活动项对象
   */
  const hoverActivity = (item) => {
    if (isAnimating.value) {
      return
    }
    hoveredActivity.value = item.key
  }

  /**
   * 处理活动项鼠标离开事件
   */
  const handleActivityMouseLeave = () => {
    hoveredActivity.value = ''
  }

  /**
   * 获取活动项简称
   * @param {string} tooltip - 完整提示文本
   * @returns {string} 简称（前两个字符）
   */
  const getShortName = (tooltip) => {
    return tooltip.substring(0, 2)
  }

  /**
   * 获取缓存的活动项数据
   * @param {string} activityKey - 活动项键
   * @returns {Object|null} 缓存的数据
   */
  const getCachedActivityData = (activityKey) => {
    const cacheKey = `activity_${activityKey}`
    return navigationCache.get(cacheKey)
  }

  /**
   * 缓存活动项数据
   * @param {string} activityKey - 活动项键
   * @param {Object} data - 要缓存的数据
   * @param {number} ttl - 缓存时间（毫秒）
   */
  const cacheActivityData = (activityKey, data, ttl = 300000) => {
    const cacheKey = `activity_${activityKey}`
    navigationCache.set(cacheKey, data, ttl)
  }

  /**
   * 获取性能统计
   * @returns {Object} 性能统计信息
   */
  const getPerformanceStats = () => {
    const cacheStats = navigationCache.getStats()
    return {
      ...performanceState,
      cache: cacheStats,
      timestamp: Date.now()
    }
  }

  /**
   * 清理缓存和重置状态
   */
  const reset = () => {
    navigationCache.clear()
    performanceState.lastActivityChange = 0
    performanceState.sidebarToggleCount = 0
    performanceState.searchCount = 0
    performanceState.cacheHitRate = 0
  }

  /**
   * 设置活动项
   * @param {string} key - 活动项键值
   */
  const setActiveActivity = (key) => {
    const item = activityItems.value.find(item => item.key === key)
    if (item) {
      activeActivity.value = key
      cacheActivityData(key, {
        activeTime: Date.now(),
        route: routeMap[key]
      })
    }
  }

  // ==================== 返回暴露的状态和方法 ====================

  return {
    activeActivity,
    hoveredActivity,
    searchQuery,
    activityItems,
    isAnimating,
    handleActivityClick,
    hoverActivity,
    handleActivityMouseLeave,
    getShortName,
    setActiveActivity,
    getCachedActivityData,
    cacheActivityData,
    getPerformanceStats,
    reset
  }
})
