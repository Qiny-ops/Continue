import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores/modules/project'
import { useUserStore } from '@/stores/modules/user'
import { debounce, withLock } from '@/utils/debounce.js'
import { getAvatarUrl } from '@/utils/avatar.js'
import { PROJECT_ROUTE_PREFIX } from '@/router/constants'
import {
  PROJECT_TABS,
  PROJECT_TABLE_COLUMNS,
  getProjectTypeLabel,
  getProjectTypeType,
  getStatusLabel,
  getStatusType
} from '@/constants/project.js'
import {
  getEmptyMessage,
  getModuleRoute,
  filterProjects
} from '@/utils/project.js'

export function useProjectList() {
  const router = useRouter()
  const projectStore = useProjectStore()
  const userStore = useUserStore()

  const activeTab = ref('projects')
  const searchKeyword = ref('')
  const globalLoading = ref(false)

  const projects = computed(() => projectStore.projects || [])

  const favoriteProjects = computed(() => projects.value.filter(p => p?.isFavorite))

  const filteredProjects = computed(() => {
    return filterProjects(projects.value, {
      activeTab: activeTab.value,
      searchKeyword: searchKeyword.value,
      currentUserName: userStore.userName
    })
  })

  const debouncedSearch = debounce((value) => {
    searchKeyword.value = value
  }, 300)

  const handleSearchChange = (value) => {
    debouncedSearch(value)
  }

  const handleCreateProject = () => {
    router.push('/projects/create')
  }

  const handleView = (project) => {
    if (project?.code) {
      router.push(`${PROJECT_ROUTE_PREFIX}/${project.code}/`)
    } else if (project?.id) {
      router.push(`${PROJECT_ROUTE_PREFIX}/${project.id}/`)
    }
  }

  const handleNavigate = (moduleType, project) => {
    const projectCode = project?.code || project?.id
    const route = getModuleRoute(moduleType, projectCode)
    if (route) {
      router.push(route)
    }
  }

  const toggleFavorite = withLock(async (project) => {
    if (!project?.id) return

    try {
      const newFavoriteStatus = !project.isFavorite
      await projectStore.updateProjectFavorite(project.id, newFavoriteStatus)
      ElMessage.success(newFavoriteStatus ? '已添加到常用项目' : '已从常用项目移除')
    } catch (error) {
      ElMessage.error(error?.message || '操作失败，请重试')
    }
  })

  const handleDelete = async (project) => {
    if (!project?.id) return

    try {
      await ElMessageBox.confirm(
        `确定删除项目「${project.name}」？删除后将无法恢复，项目下的所有测试用例、测试计划等数据都将被删除。`,
        '删除项目',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      )

      await projectStore.deleteProject(project.id)
      ElMessage.success('项目已删除')
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(error?.message || '删除失败，请重试')
      }
    }
  }

  const initProjectList = async () => {
    await projectStore.fetchProjects({}, { force: true })
  }

  onMounted(() => {
    initProjectList()
  })

  return {
    activeTab,
    searchKeyword,
    globalLoading,
    projects,
    favoriteProjects,
    filteredProjects,
    tabs: PROJECT_TABS,
    tableColumns: PROJECT_TABLE_COLUMNS,
    handleSearchChange,
    handleCreateProject,
    handleView,
    handleNavigate,
    toggleFavorite,
    handleDelete,
    getAvatarUrl,
    getEmptyMessage,
    getProjectTypeLabel,
    getProjectTypeType,
    getStatusLabel,
    getStatusType
  }
}
