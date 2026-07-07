import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { Project } from '@/constants/project.js'
import projectApi from '@/api/modules/project.js'

const CACHE_KEY = 'projects_cache'
const CACHE_EXPIRY = 5 * 60 * 1000

const loadFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (cached) {
      const { data, timestamp } = JSON.parse(cached)
      if (Date.now() - timestamp < CACHE_EXPIRY) {
        return data
      }
      localStorage.removeItem(CACHE_KEY)
    }
  } catch {
  }
  return null
}

const saveToCache = (data) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      data,
      timestamp: Date.now()
    }))
  } catch {
  }
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const projectsLoaded = ref(false)

  const activeProjects = computed(() =>
    projects.value.filter(p => p.isActive())
  )

  const completedProjects = computed(() =>
    projects.value.filter(p => p.isCompleted())
  )

  const pendingProjects = computed(() =>
    projects.value.filter(p => p.isPending())
  )

  const archivedProjects = computed(() =>
    projects.value.filter(p => p.isArchived())
  )

  const projectCount = computed(() => projects.value.length)

  const fetchProjects = async (params = {}, { force = false, useCache = true } = {}) => {
    if (projectsLoaded.value && !force) {
      return
    }

    if (!force && useCache) {
      const cachedData = loadFromCache()
      if (cachedData && Array.isArray(cachedData)) {
        projects.value = cachedData.map(item => new Project(item))
        projectsLoaded.value = true
        return
      }
    }

    loading.value = true
    error.value = null

    try {
      const response = await projectApi.getProjects(params)

      const rawProjects = response?.data?.data ||
                         response?.data?.results ||
                         response?.data?.projects ||
                         response?.data ||
                         response?.results ||
                         response?.projects ||
                         response || []

      const projectsArray = Array.isArray(rawProjects) ? rawProjects : []

      projects.value = projectsArray.map(item => new Project(item))

      saveToCache(projectsArray)

      projectsLoaded.value = true
    } catch (err) {
      error.value = err.message || '获取项目列表失败'
    } finally {
      loading.value = false
    }
  }

  const fetchProject = async (id) => {
    if (!id) {
      throw new Error('项目ID不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await projectApi.getProject(id)

      const projectData = response?.data?.data || response?.data || response
      if (!projectData || !projectData.id) {
        throw new Error('项目不存在')
      }

      currentProject.value = new Project(projectData)
      return currentProject.value
    } catch (err) {
      error.value = err.message || '获取项目详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createProject = async (projectData) => {
    if (!projectData || typeof projectData !== 'object') {
      throw new Error('项目数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await projectApi.createProject(projectData)
      const newProject = new Project(response?.data || response)
      projects.value.unshift(newProject)

      saveToCache(projects.value.map(p => ({ ...p })))

      return newProject
    } catch (err) {
      error.value = err.message || '创建项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateProject = async (id, projectData) => {
    if (!id) {
      throw new Error('项目ID不能为空')
    }
    if (!projectData || typeof projectData !== 'object') {
      throw new Error('项目数据不能为空')
    }

    loading.value = true
    error.value = null

    try {
      const response = await projectApi.updateProject(id, projectData)
      const projectDataFromResponse = response?.data?.data || response?.data || response
      const updatedProject = new Project(projectDataFromResponse)

      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }

      if (currentProject.value?.id === id) {
        currentProject.value = updatedProject
      }

      saveToCache(projects.value.map(p => ({ ...p })))

      return updatedProject
    } catch (err) {
      error.value = err.message || '更新项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateProjectFavorite = async (id, isFavorite) => {
    if (!id) {
      throw new Error('项目ID不能为空')
    }

    error.value = null

    try {
      const response = await projectApi.setFavorite(id, isFavorite)

      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        const existingProject = projects.value[index]
        projects.value[index] = new Project({
          ...existingProject.toJSON(),
          isFavorite: response?.data?.isFavorite ?? isFavorite
        })
      }

      if (currentProject.value?.id === id) {
        currentProject.value = new Project({
          ...currentProject.value.toJSON(),
          isFavorite: response?.data?.isFavorite ?? isFavorite
        })
      }

      saveToCache(projects.value.map(p => p.toJSON()))

      return projects.value.find(p => p.id === id)
    } catch (err) {
      error.value = err.message || '更新收藏状态失败'
      throw err
    }
  }

  const toggleProjectFavorite = async (id) => {
    if (!id) {
      throw new Error('项目ID不能为空')
    }

    error.value = null

    try {
      const response = await projectApi.toggleFavorite(id)
      const newFavoriteStatus = response?.data?.isFavorite

      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        const existingProject = projects.value[index]
        projects.value[index] = new Project({
          ...existingProject.toJSON(),
          isFavorite: newFavoriteStatus
        })
      }

      if (currentProject.value?.id === id) {
        currentProject.value = new Project({
          ...currentProject.value.toJSON(),
          isFavorite: newFavoriteStatus
        })
      }

      saveToCache(projects.value.map(p => p.toJSON()))

      return newFavoriteStatus
    } catch (err) {
      error.value = err.message || '切换收藏状态失败'
      throw err
    }
  }

  const fetchFavoriteProjects = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await projectApi.getFavoriteProjects()
      const rawProjects = response?.data?.projects || response?.data || []
      return rawProjects.map(item => new Project(item))
    } catch (err) {
      error.value = err.message || '获取收藏项目失败'
      return []
    } finally {
      loading.value = false
    }
  }

  const deleteProject = async (id) => {
    if (!id) {
      throw new Error('项目ID不能为空')
    }

    loading.value = true
    error.value = null

    try {
      await projectApi.deleteProject(id)

      projects.value = projects.value.filter(p => p.id !== id)

      if (currentProject.value?.id === id) {
        currentProject.value = null
      }

      saveToCache(projects.value.map(p => ({ ...p })))
    } catch (err) {
      error.value = err.message || '删除项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const searchProjects = async (keyword) => {
    loading.value = true
    error.value = null

    try {
      const response = await projectApi.searchProjects(keyword)
      const rawProjects = response?.results || response?.data || response || []
      const projectsArray = Array.isArray(rawProjects) ? rawProjects : []
      projects.value = projectsArray.map(item => new Project(item))
    } catch (err) {
      error.value = err.message || '搜索项目失败'
    } finally {
      loading.value = false
    }
  }

  const fetchProjectStats = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await projectApi.getProjectStats()
      return response?.data || response
    } catch (err) {
      error.value = err.message || '获取项目统计失败'
      return null
    } finally {
      loading.value = false
    }
  }

  const setCurrentProject = (project) => {
    currentProject.value = project
  }

  const clearError = () => {
    error.value = null
  }

  const resetState = () => {
    projects.value = []
    currentProject.value = null
    error.value = null
    projectsLoaded.value = false
    localStorage.removeItem(CACHE_KEY)
  }

  return {
    projects,
    currentProject,
    loading,
    error,
    projectsLoaded,

    activeProjects,
    completedProjects,
    pendingProjects,
    archivedProjects,
    projectCount,

    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    updateProjectFavorite,
    toggleProjectFavorite,
    fetchFavoriteProjects,
    deleteProject,
    searchProjects,
    fetchProjectStats,
    setCurrentProject,
    clearError,
    resetState
  }
})
