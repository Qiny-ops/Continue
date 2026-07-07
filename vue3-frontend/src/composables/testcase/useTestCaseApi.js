/**
 * 测试用例 API 组合式函数
 * 提供测试用例管理的数据获取和操作方法
 */

import { ref, computed } from 'vue'
import {
  repositoryApi,
  versionApi,
  moduleApi,
  testCaseApi
} from '@/api/modules/testcase.js'

/**
 * 用例库和版本管理
 */
export function useRepositoryAndVersion() {
  const repositories = ref([])
  const versions = ref([])
  const selectedRepo = ref(null)
  const selectedVersion = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // 获取用例库列表
  const fetchRepositories = async (projectId = null) => {
    loading.value = true
    error.value = null
    try {
      const params = projectId ? { project: projectId } : {}
      const response = await repositoryApi.getRepositories(params)
      repositories.value = response.results || response || []

      const defaultRepo = repositories.value.find(r => r.is_default)
      if (defaultRepo && !selectedRepo.value) {
        selectedRepo.value = defaultRepo.id
      }

      return repositories.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取版本列表
  const fetchVersions = async (repoId) => {
    if (!repoId) return

    loading.value = true
    error.value = null
    try {
      const response = await versionApi.getVersions({ repository: repoId })
      versions.value = response.results || response || []

      // 如果有默认版本，自动选中
      const defaultVersion = versions.value.find(v => v.is_default)
      if (defaultVersion) {
        selectedVersion.value = defaultVersion.id
      } else if (versions.value.length > 0) {
        selectedVersion.value = versions.value[0].id
      }

      return versions.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 创建用例库
  const createRepository = async (data) => {
    loading.value = true
    try {
      const response = await repositoryApi.createRepository(data)
      await fetchRepositories(data.project)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 创建版本
  const createVersion = async (data) => {
    loading.value = true
    try {
      const response = await versionApi.createVersion(data)
      await fetchVersions(data.repository)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 设置默认版本
  const setDefaultVersion = async (versionId) => {
    try {
      await versionApi.setDefaultVersion(versionId)
      await fetchVersions(selectedRepo.value)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 当选择用例库时，自动加载版本
  const handleRepoChange = async (repoId) => {
    selectedRepo.value = repoId
    selectedVersion.value = null
    versions.value = []
    if (repoId) {
      await fetchVersions(repoId)
    }
  }

  return {
    // 状态
    repositories,
    versions,
    selectedRepo,
    selectedVersion,
    loading,
    error,

    // 计算属性
    currentRepo: computed(() =>
      repositories.value.find(r => r.id === selectedRepo.value)
    ),
    currentVersion: computed(() =>
      versions.value.find(v => v.id === selectedVersion.value)
    ),

    // 方法
    fetchRepositories,
    fetchVersions,
    createRepository,
    createVersion,
    setDefaultVersion,
    handleRepoChange
  }
}

/**
 * 模块树管理
 */
export function useModuleTree() {
  const modules = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pendingRequests = new Map()

  // 获取模块树
  const fetchModuleTree = async (versionId) => {
    if (!versionId) {
      modules.value = []
      return
    }

    if (pendingRequests.has(versionId)) {
      return pendingRequests.get(versionId)
    }

    loading.value = true
    error.value = null
    
    const request = (async () => {
      try {
        const response = await moduleApi.getModuleTree(versionId)
        const data = response?.data?.data || response?.data || response || []
        modules.value = Array.isArray(data) ? data : []
        return modules.value
      } catch (err) {
        error.value = err.message
        throw err
      } finally {
        pendingRequests.delete(versionId)
        loading.value = false
      }
    })()
    
    pendingRequests.set(versionId, request)
    return request
  }

  // 创建模块
  const createModule = async (data) => {
    loading.value = true
    try {
      const response = await moduleApi.createModule(data)
      await fetchModuleTree(data.version)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 更新模块
  const updateModule = async (id, data) => {
    try {
      const response = await moduleApi.updateModule(id, data)
      await fetchModuleTree(data.version)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 删除模块
  const deleteModule = async (id, versionId) => {
    try {
      await moduleApi.deleteModule(id)
      await fetchModuleTree(versionId)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  return {
    modules,
    loading,
    error,
    fetchModuleTree,
    createModule,
    updateModule,
    deleteModule
  }
}

/**
 * 测试用例管理
 */
export function useTestCases() {
  const testCases = ref([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref(null)

  // 获取用例列表
  const fetchTestCases = async (params = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await testCaseApi.getTestCases(params)
      testCases.value = response.results || response || []
      total.value = response.count || testCases.value.length
      return testCases.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 根据版本获取用例
  const fetchTestCasesByVersion = async (versionId, params = {}) => {
    if (!versionId) {
      testCases.value = []
      return
    }

    loading.value = true
    error.value = null
    try {
      const response = await testCaseApi.getTestCasesByVersion(versionId, params)
      testCases.value = response.results || response || []
      total.value = response.count || testCases.value.length
      return testCases.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 根据模块获取用例（包含所有子模块的用例）
  const fetchTestCasesByModule = async (moduleId, params = {}) => {
    if (!moduleId) {
      testCases.value = []
      return
    }

    loading.value = true
    error.value = null
    try {
      const response = await testCaseApi.getTestCasesByModuleTree(moduleId, params)
      testCases.value = response.results || response || []
      total.value = response.count || testCases.value.length
      return testCases.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 创建用例
  const createTestCase = async (data) => {
    loading.value = true
    try {
      const response = await testCaseApi.createTestCase(data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 更新用例
  const updateTestCase = async (id, data) => {
    try {
      const response = await testCaseApi.updateTestCase(id, data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 删除用例
  const deleteTestCase = async (id) => {
    try {
      await testCaseApi.deleteTestCase(id)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 复制用例
  const copyTestCase = async (id) => {
    try {
      const response = await testCaseApi.copyTestCase(id)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  // 获取单个用例详情
  const getTestCase = async (id) => {
    loading.value = true
    error.value = null
    try {
      const response = await testCaseApi.getTestCase(id)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 批量复制用例
  const batchCopy = async (ids) => {
    loading.value = true
    try {
      const response = await testCaseApi.batchCopyTestCases(ids)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 批量删除用例
  const batchDelete = async (ids) => {
    loading.value = true
    try {
      const response = await testCaseApi.batchDeleteTestCases(ids)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 批量移动用例
  const batchMove = async (ids, targetModuleId) => {
    loading.value = true
    try {
      const response = await testCaseApi.batchMoveTestCases(ids, targetModuleId)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // 批量更新用例
  const batchUpdate = async (data) => {
    loading.value = true
    try {
      const response = await testCaseApi.batchUpdateTestCases(data)
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    testCases,
    total,
    loading,
    error,
    fetchTestCases,
    fetchTestCasesByVersion,
    fetchTestCasesByModule,
    createTestCase,
    updateTestCase,
    deleteTestCase,
    copyTestCase,
    getTestCase,
    batchCopy,
    batchDelete,
    batchMove,
    batchUpdate
  }
}

/**
 * 完整的测试用例管理
 */
export function useTestCaseManager() {
  const repoVersion = useRepositoryAndVersion()
  const moduleTree = useModuleTree()
  const testCases = useTestCases()

  // 当前选中的模块
  const selectedModule = ref(null)

  // 当版本变化时，重新加载模块树和用例
  const handleVersionChange = async (versionId) => {
    repoVersion.selectedVersion.value = versionId
    selectedModule.value = null

    if (versionId) {
      // 并行加载模块树和用例
      await Promise.all([
        moduleTree.fetchModuleTree(versionId),
        testCases.fetchTestCasesByVersion(versionId)
      ])
    } else {
      moduleTree.modules.value = []
      testCases.testCases.value = []
    }
  }

  // 当模块变化时，加载对应用例
  const handleModuleChange = async (moduleId) => {
    selectedModule.value = moduleId

    if (moduleId) {
      await testCases.fetchTestCasesByModule(moduleId)
    } else if (repoVersion.selectedVersion.value) {
      await testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value)
    }
  }

  // 刷新当前数据
  const refresh = async () => {
    if (repoVersion.selectedVersion.value) {
      await Promise.all([
        moduleTree.fetchModuleTree(repoVersion.selectedVersion.value),
        testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value)
      ])
    }
  }

  return {
    // 用例库和版本
    ...repoVersion,

    // 模块树
    ...moduleTree,

    // 测试用例
    ...testCases,

    // 选中状态
    selectedModule,

    // 事件处理
    handleVersionChange,
    handleModuleChange,
    refresh
  }
}
