import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRepositoryAndVersion, useModuleTree } from '@/composables/testcase/useTestCaseApi'

export function useRepoVersionModuleTree({ projectId, onVersionChange, onModuleChange, onModuleDelete }) {
  const router = useRouter()
  const route = useRoute()

  const repoVersion = useRepositoryAndVersion()
  const moduleTree = useModuleTree()
  const selectedModule = ref(null)
  const sidebarCollapsed = ref(false)

  const selectedRepo = computed({
    get: () => repoVersion.selectedRepo.value,
    set: (val) => { repoVersion.selectedRepo.value = val }
  })

  const selectedVersion = computed({
    get: () => repoVersion.selectedVersion.value,
    set: (val) => { repoVersion.selectedVersion.value = val }
  })

  const repoList = computed(() =>
    repoVersion.repositories.value.map(repo => ({
      id: repo.id,
      name: repo.name,
      icon: repo.is_default ? 'Folder' : 'Collection'
    }))
  )

  const versionList = computed(() =>
    repoVersion.versions.value.map(v => ({
      id: v.id,
      name: v.name,
      is_default: v.is_default
    }))
  )

  const defaultVersionId = computed(() => {
    const defaultVersion = versionList.value.find(v => v.is_default)
    return defaultVersion?.id || null
  })

  const repoVersionLoading = computed(() => repoVersion.loading.value)
  const moduleTreeData = computed(() => moduleTree.modules.value)
  const moduleLoading = computed(() => moduleTree.loading.value)

  const fetchRepositories = async () => {
    try {
      await repoVersion.fetchRepositories(projectId.value)
    } catch (err) {
      ElMessage.error(err.message || '获取用例库失败')
    }
  }

  const fetchVersions = async (repoId) => {
    if (!repoId) return
    try {
      await repoVersion.fetchVersions(repoId)
    } catch (err) {
      ElMessage.error(err.message || '获取版本列表失败')
    }
  }

  const handleCreateRepo = async () => {
    try {
      const { value } = await ElMessageBox.prompt('请输入用例库名称', '新建用例库', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: (val) => {
          if (!val || val.trim() === '') return '用例库名称不能为空'
          return true
        }
      })
      await repoVersion.createRepository({
        name: value.trim(),
        project: projectId.value,
        is_default: repoVersion.repositories.value.length === 0
      })
      ElMessage.success('用例库创建成功')
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '创建用例库失败')
    }
  }

  const handleCreateVersion = async () => {
    if (!repoVersion.selectedRepo.value) {
      ElMessage.warning('请先选择用例库')
      return
    }
    try {
      const { value } = await ElMessageBox.prompt('请输入版本名称', '新建版本', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: (val) => {
          if (!val || val.trim() === '') return '版本名称不能为空'
          return true
        }
      })
      await repoVersion.createVersion({
        name: value.trim(),
        repository: repoVersion.selectedRepo.value,
        is_default: repoVersion.versions.value.length === 0
      })
      ElMessage.success('版本创建成功')
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '创建版本失败')
    }
  }

  const handleManageRepo = () => {
    const projectCode = route.params.code
    router.push({ path: `/p/${projectCode}/t/manage-repo` })
  }

  const handleManageVersion = () => {
    if (!repoVersion.selectedRepo.value) {
      ElMessage.warning('请先选择用例库')
      return
    }
    const projectCode = route.params.code
    router.push({
      path: `/p/${projectCode}/t/manage-version`,
      query: {
        repo: repoVersion.selectedRepo.value,
        name: repoList.value.find(r => r.id === repoVersion.selectedRepo.value)?.name || ''
      }
    })
  }

  const handleAddModule = async () => {
    if (!selectedVersion.value) {
      ElMessage.warning('请先选择版本')
      return
    }
    try {
      const { value } = await ElMessageBox.prompt('请输入模块名称', '添加模块', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: (val) => {
          if (!val || val.trim() === '') return '模块名称不能为空'
          return true
        }
      })
      await moduleTree.createModule({
        name: value.trim(),
        version: Number(selectedVersion.value),
        parent: selectedModule.value ? Number(selectedModule.value) : null
      })
      ElMessage.success('模块添加成功')
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '添加模块失败')
    }
  }

  const handleAddSubModule = async (parentModule) => {
    if (!selectedVersion.value) {
      ElMessage.warning('请先选择版本')
      return
    }
    try {
      const { value } = await ElMessageBox.prompt(`请在 "${parentModule.name}" 下添加子模块`, '添加子模块', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValidator: (val) => {
          if (!val || val.trim() === '') return '模块名称不能为空'
          return true
        }
      })
      await moduleTree.createModule({
        name: value.trim(),
        version: Number(selectedVersion.value),
        parent: parentModule.id
      })
      ElMessage.success('子模块添加成功')
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '添加子模块失败')
    }
  }

  const handleEditModule = async (module) => {
    try {
      const { value } = await ElMessageBox.prompt('修改模块名称', '编辑模块', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: module.name,
        inputValidator: (val) => {
          if (!val || val.trim() === '') return '模块名称不能为空'
          return true
        }
      })
      await moduleTree.updateModule(module.id, { name: value.trim() })
      ElMessage.success('模块更新成功')
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '更新模块失败')
    }
  }

  const handleDeleteModule = async (module) => {
    const hasChildren = module.children && module.children.length > 0
    const hasCases = module.count && module.count > 0

    let confirmMessage = `确定要删除模块 "${module.name}" 吗？`
    if (hasChildren && hasCases) {
      confirmMessage = `模块 "${module.name}" 下有 ${module.children.length} 个子模块和 ${module.count} 个用例，删除后子模块和用例将一并删除，确定要删除吗？`
    } else if (hasChildren) {
      confirmMessage = `模块 "${module.name}" 下有 ${module.children.length} 个子模块，删除后子模块将一并删除，确定要删除吗？`
    } else if (hasCases) {
      confirmMessage = `模块 "${module.name}" 下有 ${module.count} 个用例，删除后用例将一并删除，确定要删除吗？`
    }

    try {
      await ElMessageBox.confirm(confirmMessage, '删除模块', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await moduleTree.deleteModule(module.id, selectedVersion.value)
      ElMessage.success('模块删除成功')

      if (selectedModule.value === module.id) {
        selectedModule.value = null
        onModuleDelete?.()
      }
    } catch (err) {
      if (err !== 'cancel') ElMessage.error(err.message || '删除模块失败')
    }
  }

  const handleModuleClick = (data) => {
    selectedModule.value = data.id
    onModuleChange?.(data.id)
  }

  const handleShowAll = () => {
    selectedModule.value = null
    onModuleChange?.(null)
  }

  const handleModuleRefresh = async () => {
    if (selectedVersion.value) {
      await moduleTree.fetchModuleTree(selectedVersion.value)
      onVersionChange?.(selectedVersion.value)
    }
  }

  watch(() => selectedRepo.value, async (newRepoId, oldRepoId) => {
    if (newRepoId && newRepoId !== oldRepoId) {
      selectedVersion.value = null
      selectedModule.value = null
      repoVersion.versions.value = []
      moduleTree.modules.value = []
      await fetchVersions(newRepoId)
    }
  })

  watch(() => selectedVersion.value, async (newVersionId, oldVersionId) => {
    if (newVersionId && newVersionId !== oldVersionId) {
      selectedModule.value = null
      await moduleTree.fetchModuleTree(newVersionId)
      onVersionChange?.(newVersionId)
    }
  })

  watch(() => projectId.value, (newId) => {
    if (newId) fetchRepositories()
  }, { immediate: true })

  return {
    repoVersion,
    moduleTree,
    selectedModule,
    sidebarCollapsed,
    selectedRepo,
    selectedVersion,
    repoList,
    versionList,
    defaultVersionId,
    repoVersionLoading,
    moduleTreeData,
    moduleLoading,
    fetchRepositories,
    fetchVersions,
    handleCreateRepo,
    handleCreateVersion,
    handleManageRepo,
    handleManageVersion,
    handleAddModule,
    handleAddSubModule,
    handleEditModule,
    handleDeleteModule,
    handleModuleClick,
    handleShowAll,
    handleModuleRefresh
  }
}
