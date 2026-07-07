/**
 * 导航栏缓存管理器
 * 提供智能缓存机制，减少重复数据加载和计算
 * 使用Map数据结构实现，支持TTL（生存时间）和最大缓存数量限制
 */

class NavigationCache {
  constructor() {
    this.cache = new Map()
    this.timers = new Map()
    this.defaultTTL = 5 * 60 * 1000
    this.maxSize = 100
  }

  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {*} value - 缓存值
   * @param {number} ttl - 过期时间（毫秒），可选，默认使用defaultTTL
   */
  set(key, value, ttl = this.defaultTTL) {
    this.cleanup()

    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      this.delete(oldestKey)
    }

    const expiresAt = Date.now() + ttl
    this.cache.set(key, {
      value,
      expiresAt,
      createdAt: Date.now()
    })

    const timer = setTimeout(() => {
      this.delete(key)
    }, ttl)

    this.timers.set(key, timer)
  }

  /**
   * 获取缓存
   * @param {string} key - 缓存键
   * @returns {*} 缓存值，如果不存在或已过期返回null
   */
  get(key) {
    const cached = this.cache.get(key)

    if (!cached) {
      return null
    }

    if (Date.now() > cached.expiresAt) {
      this.delete(key)
      return null
    }

    return cached.value
  }

  /**
   * 删除缓存
   * @param {string} key - 缓存键
   */
  delete(key) {
    this.cache.delete(key)

    const timer = this.timers.get(key)
    if (timer) {
      clearTimeout(timer)
      this.timers.delete(key)
    }
  }

  /**
   * 清理所有过期缓存
   */
  cleanup() {
    const now = Date.now()
    const expiredKeys = []

    for (const [key, cached] of this.cache.entries()) {
      if (now > cached.expiresAt) {
        expiredKeys.push(key)
      }
    }

    expiredKeys.forEach(key => this.delete(key))
  }

  /**
   * 清空所有缓存
   */
  clear() {
    for (const timer of this.timers.values()) {
      clearTimeout(timer)
    }

    this.cache.clear()
    this.timers.clear()
  }

  /**
   * 获取缓存统计信息
   * @returns {Object} 缓存统计对象
   */
  getStats() {
    const stats = {
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: 0,
      missRate: 0,
      oldestItem: null,
      newestItem: null
    }

    if (this.cache.size > 0) {
      const items = Array.from(this.cache.values())
      const oldest = items.reduce((oldest, current) =>
        oldest.createdAt < current.createdAt ? oldest : current
      )
      const newest = items.reduce((newest, current) =>
        newest.createdAt > current.createdAt ? newest : current
      )

      stats.oldestItem = new Date(oldest.createdAt).toISOString()
      stats.newestItem = new Date(newest.createdAt).toISOString()
    }

    return stats
  }

  /**
   * 检查缓存是否存在且有效
   * @param {string} key - 缓存键
   * @returns {boolean} 缓存是否存在且未过期
   */
  has(key) {
    return this.get(key) !== null
  }
}

const navigationCache = new NavigationCache()

export default navigationCache
export { NavigationCache }
