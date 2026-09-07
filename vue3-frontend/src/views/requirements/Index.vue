<template>
  <div class="requirement-page">
    <div class="requirement-container">
      <div class="version-bar">
        <div class="version-group">
          <span class="page-title">需求管理</span>
          <div class="version-divider"></div>
          <span class="version-label">版本</span>
          <el-select
            v-model="selectedVersion"
            placeholder="选择版本"
            class="version-select"
            :loading="versionLoading"
            @change="handleVersionChange"
          >
            <el-option
              v-for="v in versionList"
              :key="v.id"
              :label="v.name"
              :value="v.id"
            >
              <div class="option-content">
                <el-icon class="option-icon"><PriceTag /></el-icon>
                <span class="option-name">{{ v.name }}</span>
              </div>
            </el-option>
            <template #footer>
              <div class="select-footer-actions">
                <span class="footer-action" @mousedown.prevent @click="handleCreateVersion">
                  <el-icon><Plus /></el-icon>
                  <span>新建版本</span>
                </span>
              </div>
            </template>
          </el-select>
        </div>
      </div>

      <div class="case-layout">
        <div class="sidebar-wrapper" :class="{ collapsed: sidebarCollapsed }">
          <ModuleTree
            v-show="!sidebarCollapsed"
            :tree-data="moduleTreeData"
            :loading="moduleLoading"
            :total-count="total"
            :current-version="selectedVersion"
            all-label="全部需求"
            @add-module="handleAddModule"
            @add-sub-module="handleAddSubModule"
            @edit-module="handleEditModule"
            @delete-module="handleDeleteModule"
            @node-click="handleModuleClick"
            @show-all-cases="handleShowAll"
            @refresh="handleModuleRefresh"
          />
          <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
            <el-icon :size="16">
              <ArrowLeft v-if="!sidebarCollapsed" />
              <ArrowRight v-else />
            </el-icon>
          </div>
        </div>

        <div class="case-main">
          <div class="toolbar-section">
            <div class="toolbar-left">
              <div class="search-box">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索需求标题、功能点..."
                  clearable
                  :prefix-icon="Search"
                />
              </div>
              <div class="filter-group">
                <el-select v-model="filterStatus" placeholder="状态" clearable class="filter-item">
                  <el-option label="草稿" value="draft" />
                  <el-option label="活跃" value="active" />
                  <el-option label="已完成" value="completed" />
                  <el-option label="已归档" value="archived" />
                </el-select>
                <el-select v-model="filterPriority" placeholder="优先级" clearable class="filter-item">
                  <el-option label="P0" value="p0" />
                  <el-option label="P1" value="p1" />
                  <el-option label="P2" value="p2" />
                  <el-option label="P3" value="p3" />
                </el-select>
              </div>
            </div>
            <div class="toolbar-right">
              <el-button type="primary" :disabled="!selectedVersion" @click="handleCreate">
                <el-icon><Plus /></el-icon>
                新建需求
              </el-button>
              <div class="batch-operation-wrapper">
                <el-button
                  :class="{ 'batch-active': batchMode }"
                  @click="toggleBatchMode"
                >
                  <el-icon><Operation /></el-icon>
                  {{ batchMode ? '取消操作' : '批量操作' }}
                </el-button>
                <Transition name="menu-fade">
                  <div v-if="batchMode" class="batch-menu">
                    <div
                      class="batch-menu-item"
                      :class="{ disabled: selectedRequirements.length === 0 }"
                      @click="handleBatchGenerate"
                    >
                      <el-icon><MagicStick /></el-icon>
                      <span>批量生成用例</span>
                    </div>
                    <div class="batch-menu-divider"></div>
                    <div
                      class="batch-menu-item danger"
                      :class="{ disabled: selectedRequirements.length === 0 }"
                      @click="handleBatchDelete"
                    >
                      <el-icon><Delete /></el-icon>
                      <span>批量删除</span>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </div>

          <div class="table-section">
            <RequirementTable
              ref="tableRef"
              :data="requirements"
              :loading="loading"
              :show-selection="batchMode"
              @selection-change="handleSelectionChange"
              @command="handleCommand"
              @generate="handleGenerate"
            />
          </div>

          <div class="pagination-section">
            <div class="pagination-info">
              <template v-if="isFiltering">
                搜索结果 <strong>{{ total }}</strong> 条
              </template>
              <template v-else>
                共 <strong>{{ total }}</strong> 条需求
              </template>
              <span v-if="batchMode && selectedRequirements.length > 0" class="selected-count">
                ，已选择 <strong>{{ selectedRequirements.length }}</strong> 项
              </span>
            </div>
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="sizes, prev, pager, next, jumper"
              @change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>

    <RequirementDialog
      v-model:visible="dialogVisible"
      :is-editing="isEditing"
      :form="form"
      :project-id="project?.id"
      :version-id="selectedVersion"
      @save="handleDialogSave"
    />

    <RequirementGenerateDialog
      v-model:visible="generateVisible"
      :requirement-id="generateRequirementId"
      :requirement-ids="generateRequirementIds"
      :project="project"
      :default-version-id="selectedVersion"
      @generated="handleGenerateComplete"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Plus, Search, Delete, Operation, MagicStick, ArrowLeft, ArrowRight, PriceTag } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ModuleTree from '@/views/testcase/components/ModuleTree.vue'
import RequirementTable from './components/RequirementTable.vue'
import RequirementDialog from './components/RequirementDialog.vue'
import RequirementGenerateDialog from './components/RequirementGenerateDialog.vue'
import { useRequirements } from '@/composables/requirement/useRequirementApi'
import { useModuleTree } from '@/composables/testcase/useTestCaseApi'
import { versionApi, moduleApi, repositoryApi } from '@/api/modules/testcase'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const projectId = computed(() => props.project?.id)

const {
  requirements,
  total,
  loading,
  fetchRequirements,
  createRequirement,
  updateRequirement,
  deleteRequirement,
  batchDeleteRequirements,
} = useRequirements()

// 版本管理（通过用例库）
const selectedVersion = ref(null)
const versionList = ref([])
const versionLoading = ref(false)
const repositoryId = ref(null)

const fetchVersions = async () => {
  if (!projectId.value) return
  versionLoading.value = true
  try {
    // 先获取项目的默认用例库
    const repoRes = await repositoryApi.getRepositories({ project: projectId.value })
    const repoList = repoRes?.results || repoRes || []
    const defaultRepo = repoList.find(r => r.is_default) || repoList[0]
    if (defaultRepo) {
      repositoryId.value = defaultRepo.id
    }

    const res = await versionApi.getVersions({ repository: repositoryId.value })
    const list = res?.results || res || []
    versionList.value = list
    const defaultVersion = list.find(v => v.is_default)
    if (defaultVersion) {
      selectedVersion.value = defaultVersion.id
    } else if (list.length > 0) {
      selectedVersion.value = list[0].id
    }
  } catch (err) {
    ElMessage.error(err.message || '获取版本列表失败')
  } finally {
    versionLoading.value = false
  }
}

const handleVersionChange = () => {
  selectedModule.value = null
  currentPage.value = 1
  searchQuery.value = ''
  filterPriority.value = ''
  filterStatus.value = ''
  if (selectedVersion.value) {
    Promise.all([
      moduleTree.fetchModuleTree(selectedVersion.value),
      loadRequirements()
    ])
  }
}

const handleCreateVersion = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入版本名称', '新建版本', {
      confirmButtonText: '确定', cancelButtonText: '取消',
      inputValidator: (val) => (!val || val.trim() === '') ? '版本名称不能为空' : true
    })
    await versionApi.createVersion({
      name: value.trim(),
      repository: repositoryId.value,
      is_default: versionList.value.length === 0
    })
    ElMessage.success('版本创建成功')
    await fetchVersions()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '创建版本失败')
  }
}

// 模块树
const moduleTree = useModuleTree('requirement')
const selectedModule = ref(null)
const sidebarCollapsed = ref(false)
const moduleTreeData = computed(() => moduleTree.modules.value)
const moduleLoading = computed(() => moduleTree.loading.value)

const handleAddModule = async () => {
  if (!selectedVersion.value) { ElMessage.warning('请先选择版本'); return }
  try {
    const { value } = await ElMessageBox.prompt('请输入模块名称', '添加模块', {
      confirmButtonText: '确定', cancelButtonText: '取消',
      inputValidator: (val) => (!val || val.trim() === '') ? '模块名称不能为空' : true
    })
    await moduleTree.createModule({ name: value.trim(), version: Number(selectedVersion.value), parent: selectedModule.value ? Number(selectedModule.value) : null })
    ElMessage.success('模块添加成功')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '添加模块失败')
  }
}

const handleAddSubModule = async (parentModule) => {
  if (!selectedVersion.value) { ElMessage.warning('请先选择版本'); return }
  try {
    const { value } = await ElMessageBox.prompt(`请在 "${parentModule.name}" 下添加子模块`, '添加子模块', {
      confirmButtonText: '确定', cancelButtonText: '取消',
      inputValidator: (val) => (!val || val.trim() === '') ? '模块名称不能为空' : true
    })
    await moduleTree.createModule({ name: value.trim(), version: Number(selectedVersion.value), parent: parentModule.id })
    ElMessage.success('子模块添加成功')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '添加子模块失败')
  }
}

const handleEditModule = async (module) => {
  try {
    const { value } = await ElMessageBox.prompt('修改模块名称', '编辑模块', {
      confirmButtonText: '确定', cancelButtonText: '取消', inputValue: module.name,
      inputValidator: (val) => (!val || val.trim() === '') ? '模块名称不能为空' : true
    })
    await moduleTree.updateModule(module.id, { name: value.trim() })
    ElMessage.success('模块更新成功')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '更新模块失败')
  }
}

const handleDeleteModule = async (module) => {
  try {
    await ElMessageBox.confirm(`确定要删除模块 "${module.name}" 吗？`, '删除模块', { type: 'warning' })
    await moduleTree.deleteModule(module.id, selectedVersion.value)
    ElMessage.success('模块删除成功')
    if (selectedModule.value === module.id) {
      selectedModule.value = null
      await loadRequirements()
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '删除模块失败')
  }
}

const handleModuleClick = (data) => {
  selectedModule.value = data.id
  currentPage.value = 1
  loadRequirements()
}

const handleShowAll = () => {
  selectedModule.value = null
  currentPage.value = 1
  loadRequirements()
}

const handleModuleRefresh = async () => {
  if (selectedVersion.value) {
    await moduleTree.fetchModuleTree(selectedVersion.value)
    await loadRequirements()
  }
}

const searchQuery = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const batchMode = ref(false)
const selectedRequirements = ref([])
const tableRef = ref(null)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const form = reactive({
  title: '',
  description: '',
  func_point: '',
  priority: 'p2',
  status: 'draft',
})

const generateVisible = ref(false)
const generateRequirementId = ref(null)
const generateRequirementIds = ref([])

const isFiltering = computed(() => {
  return searchQuery.value.trim() || filterStatus.value || filterPriority.value
})

const loadRequirements = async () => {
  if (!selectedVersion.value) {
    requirements.value = []
    return
  }
  const params = {
    page: currentPage.value,
    page_size: pageSize.value,
    version: selectedVersion.value,
  }
  if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
  if (filterStatus.value) params.status = filterStatus.value
  if (filterPriority.value) params.priority = filterPriority.value
  if (selectedModule.value) params.module = selectedModule.value
  await fetchRequirements(params)
}

const handlePageChange = () => { loadRequirements() }

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedRequirements.value = []
    tableRef.value?.clearSelection()
  }
}

const handleSelectionChange = (selection) => { selectedRequirements.value = selection }

const handleCreate = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, { title: '', description: '', func_point: '', priority: 'p2', status: 'draft' })
  dialogVisible.value = true
}

const handleCommand = ({ command, row }) => {
  if (row.is_readonly) {
    ElMessage.warning('该需求所属版本已归档，不可操作')
    return
  }
  if (command === 'edit') {
    isEditing.value = true
    editingId.value = row.id
    Object.assign(form, {
      title: row.title,
      description: row.description || '',
      func_point: row.func_point || '',
      priority: row.priority,
      status: row.status,
    })
    dialogVisible.value = true
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定删除该需求？', '提示', { type: 'warning' })
      .then(async () => {
        await deleteRequirement(row.id)
        ElMessage.success('删除成功')
        await loadRequirements()
      })
      .catch(() => {})
  }
}

const handleDialogSave = async (data) => {
  if (isEditing.value) {
    await updateRequirement(editingId.value, { ...data, project: props.project?.id, version: selectedVersion.value })
    ElMessage.success('更新成功')
  } else {
    await createRequirement({ ...data, project: props.project?.id, version: selectedVersion.value })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  await loadRequirements()
}

const handleGenerate = (row) => {
  generateRequirementId.value = row.id
  generateRequirementIds.value = []
  generateVisible.value = true
}

const handleBatchGenerate = () => {
  if (selectedRequirements.value.length === 0) { ElMessage.warning('请先选择需求'); return }
  generateRequirementId.value = null
  generateRequirementIds.value = selectedRequirements.value.map(r => r.id)
  generateVisible.value = true
}

const handleBatchDelete = async () => {
  if (selectedRequirements.value.length === 0) { ElMessage.warning('请先选择需求'); return }
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRequirements.value.length} 个需求？`, '警告', { type: 'warning' })
    const ids = selectedRequirements.value.map(r => r.id)
    await batchDeleteRequirements(ids)
    ElMessage.success('批量删除成功')
    batchMode.value = false
    selectedRequirements.value = []
    await loadRequirements()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '批量删除失败')
  }
}

const handleGenerateComplete = () => {
  ElMessage.success('测试用例生成完成')
  loadRequirements()
}

let searchDebounceTimer = null
watch([searchQuery, filterStatus, filterPriority], () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => { currentPage.value = 1; loadRequirements() }, 300)
})

watch(() => projectId.value, (newId) => {
  if (newId) fetchVersions()
}, { immediate: true })
</script>

<style scoped>
.requirement-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.version-bar {
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-secondary);
  flex-shrink: 0;
}

.version-group {
  display: flex;
  align-items: center;
  gap: 0;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-right: 4px;
}

.version-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.version-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border-primary);
  margin: 0 20px;
}

.version-select {
  width: 180px;
}

.version-select :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-light) inset;
}

.version-select :deep(.el-input__wrapper:hover),
.version-select :deep(.el-input__wrapper2.is-focus) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-icon {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.option-name {
  font-size: 13px;
  color: var(--color-text-primary);
}

.select-footer-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  margin: 8px -12px -8px;
  border-top: 1px solid var(--color-border-secondary);
}

.footer-action {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  color: var(--color-primary);
  font-size: 13px;
  cursor: pointer;
  border-radius: 2px;
}

.footer-action:hover {
  background-color: var(--color-primary-light);
}

.footer-action .el-icon {
  font-size: 14px;
}

.requirement-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.case-layout {
  flex: 1;
  display: flex;
  gap: 0;
  min-height: 0;
  background: #fff;
  overflow: hidden;
}

.sidebar-wrapper {
  position: relative;
  display: flex;
  flex-shrink: 0;
  transition: width 0.3s ease;
}

.sidebar-wrapper.collapsed {
  width: 0;
}

.sidebar-toggle {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: #fff;
  border: 1px solid var(--color-bg-tertiary);
  border-left: none;
  border-radius: 0 2px 2px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  box-shadow: var(--shadow-md);
  transition: all 0.2s ease;
}

.sidebar-toggle:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.sidebar-toggle:hover .el-icon {
  color: #fff;
}

.case-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border-left: 1px solid var(--color-bg-tertiary);
  background: var(--color-bg-secondary);
}

.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-bg-tertiary);
  flex-shrink: 0;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.search-box { width: 280px; }

.search-box :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-light) inset;
}

.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-item { width: 120px; }
.filter-item :deep(.el-input__wrapper) { border-radius: 2px; }

.toolbar-right { display: flex; align-items: center; gap: 8px; }
.toolbar-right .el-button { border-radius: 2px; }

.batch-operation-wrapper { position: relative; display: inline-block; }

.selected-count { color: var(--color-primary); font-size: 13px; }
.selected-count strong { color: var(--color-primary); }

.batch-active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.batch-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 140px;
  padding: 6px 0;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border: 1px solid var(--color-bg-tertiary);
  z-index: 1000;
}

.batch-menu-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; cursor: pointer; transition: all 0.2s ease;
  color: #333; font-size: 14px;
}
.batch-menu-item:hover { background: var(--color-bg-secondary); }
.batch-menu-item.disabled { color: var(--color-text-tertiary); cursor: not-allowed; }
.batch-menu-item.danger { color: var(--color-danger); }
.batch-menu-item.danger:hover { background: var(--color-danger-light); }
.batch-menu-divider { height: 1px; margin: 6px 0; background: var(--color-bg-tertiary); }

.table-section {
  flex: 1; min-height: 0; overflow: hidden;
  background: #fff; margin: 16px; margin-bottom: 0;
  border-radius: 2px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-section {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: #fff;
  border-top: 1px solid var(--color-border-secondary);
  margin: 0 16px 16px; border-radius: 0 0 2px 2px; flex-shrink: 0;
}

.pagination-info { font-size: 13px; color: #666; }
.pagination-info strong { color: #333; }

.menu-fade-enter-active, .menu-fade-leave-active { transition: all 0.2s ease; }
.menu-fade-enter-from, .menu-fade-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
