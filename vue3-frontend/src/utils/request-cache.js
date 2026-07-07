const cache = new Map()
const DEFAULT_TTL = 5 * 60 * 1000

export function setCache(key, data, ttl = DEFAULT_TTL) {
  const expireTime = Date.now() + ttl
  cache.set(key, { data, expireTime })
}

export function getCache(key) {
  const cached = cache.get(key)
  if (!cached) return null

  if (Date.now() > cached.expireTime) {
    cache.delete(key)
    return null
  }

  return cached.data
}

export function clearCache(key) {
  if (key) {
    cache.delete(key)
  } else {
    cache.clear()
  }
}

export function clearCacheByPrefix(prefix) {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) {
      cache.delete(key)
    }
  }
}

export function hasCache(key) {
  return getCache(key) !== null
}

export function getCacheInfo(key) {
  const cached = cache.get(key)
  if (!cached) return null

  const remaining = cached.expireTime - Date.now()
  return {
    exists: remaining > 0,
    remainingTime: remaining > 0 ? remaining : 0,
    isExpired: remaining <= 0
  }
}

export function createCachedRequest(fn, keyGenerator, ttl = DEFAULT_TTL) {
  return async (...args) => {
    const cacheKey = keyGenerator(...args)
    const cachedData = getCache(cacheKey)

    if (cachedData) {
      return cachedData
    }

    const data = await fn(...args)
    setCache(cacheKey, data, ttl)
    return data
  }
}

export function withCache(fn, keyGenerator, ttl = DEFAULT_TTL) {
  const cachedFn = createCachedRequest(fn, keyGenerator, ttl)

  cachedFn.invalidate = (...args) => {
    const cacheKey = keyGenerator(...args)
    clearCache(cacheKey)
  }

  cachedFn.refresh = async (...args) => {
    cachedFn.invalidate(...args)
    return cachedFn(...args)
  }

  return cachedFn
}

export const CACHE_KEYS = {
  USER_LIST: 'user_list',
  PROJECT_LIST: 'project_list',
  PROJECT_DETAIL: (id) => `project_detail_${id}`,
  PROJECT_ROLES: (projectId) => `project_roles_${projectId}`,
  PROJECT_MEMBERS: (projectId) => `project_members_${projectId}`,
  TESTCASE_LIST: (versionId) => `testcase_list_${versionId}`,
  MODULE_TREE: (versionId) => `module_tree_${versionId}`,
  INTERFACE_LIST: (projectId) => `interface_list_${projectId}`,
}

export const CACHE_TTL = {
  SHORT: 1 * 60 * 1000,
  DEFAULT: 5 * 60 * 1000,
  LONG: 15 * 60 * 1000,
  VERY_LONG: 60 * 60 * 1000,
}
