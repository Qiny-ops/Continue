<template>
  <div class="test-case-page">
    <div class="case-container">
      <RepoVersionSelector
        v-model:selected-repo="selectedRepo"
        v-model:selected-version="selectedVersion"
        :repo-list="repoList"
        :version-list="versionList"
        :loading="repoVersionLoading"
        @create-repo="handleCreateRepo"
        @create-version="handleCreateVersion"
        @manage-repo="handleManageRepo"
        @manage-version="handleManageVersion"
      />

      <div class="case-layout">
        <div class="sidebar-wrapper" :class="{ collapsed: sidebarCollapsed }">
          <ModuleTree
            v-show="!sidebarCollapsed"
            :tree-data="moduleTreeData"
            :loading="moduleLoading"
            :total-count="total"
            :current-version="selectedVersion"
            @add-module="handleAddModule"
            @add-sub-module="handleAddSubModule"
            @edit-module="handleEditModule"
            @delete-module="handleDeleteModule"
            @node-click="handleModuleClick"
            @show-all-cases="handleShowAllCases"
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
                  placeholder="搜索用例名称、ID..."
                  clearable
                  :prefix-icon="Search"
                />
              </div>
              <div class="filter-group">
                <el-select v-model="filterPriority" placeholder="优先级" clearable class="filter-item">
                  <el-option label="P0 - 紧急" value="p0" />
                  <el-option label="P1 - 高" value="p1" />
                  <el-option label="P2 - 中" value="p2" />
                  <el-option label="P3 - 低" value="p3" />
                </el-select>
                <el-select v-model="filterStatus" placeholder="执行状态" clearable class="filter-item">
                  <el-option label="通过" value="pass" />
                  <el-option label="失败" value="fail" />
                  <el-option label="阻塞" value="block" />
                  <el-option label="跳过" value="skip" />
                </el-select>
              </div>
            </div>
            <div class="toolbar-right">
              <el-button type="primary" @click="handleCreateTestCase">
                <el-icon><Plus /></el-icon>
                新建用例
              </el-button>
              <el-button type="success" plain @click="handleOpenAIGenerate">
                <el-icon><MagicStick /></el-icon>
                AI 生成
              </el-button>
              <el-dropdown
                trigger="click"
                :disabled="!selectedVersion"
                @command="handleExport"
              >
                <el-button plain :loading="exporting">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="excel">
                      导出 Excel (.xlsx)
                    </el-dropdown-item>
                    <el-dropdown-item command="csv">
                      导出 CSV
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <div class="batch-operation-wrapper">
                <el-button
                  :type="batchMode ? 'default' : 'default'"
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
                      :class="{ disabled: selectedCases.length === 0 }"
                      @click="handleBatchAction('execute')"
                    >
                      <el-icon><VideoPlay /></el-icon>
                      <span>批量执行</span>
                    </div>
                    <div
                      class="batch-menu-item"
                      :class="{ disabled: selectedCases.length === 0 }"
                      @click="handleBatchAction('move')"
                    >
                      <el-icon><FolderOpened /></el-icon>
                      <span>批量移动</span>
                    </div>
                    <div
                      class="batch-menu-item"
                      :class="{ disabled: selectedCases.length === 0 }"
                      @click="handleBatchAction('copy')"
                    >
                      <el-icon><CopyDocument /></el-icon>
                      <span>批量复制</span>
                    </div>
                    <div class="batch-menu-divider"></div>
                    <div
                      class="batch-menu-item danger"
                      :class="{ disabled: selectedCases.length === 0 }"
                      @click="handleBatchAction('delete')"
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
            <TestCaseTable
              ref="tableRef"
              :data="testCases.testCases.value"
              :loading="testCaseLoading"
              :show-selection="batchMode"
              @selection-change="handleSelectionChange"
              @command="handleCommand"
              @review="handleReview"
            />
          </div>

          <div class="pagination-section">
            <div class="pagination-info">
              <template v-if="isFiltering">
                搜索结果 <strong>{{ total }}</strong> 条
              </template>
              <template v-else>
                共 <strong>{{ total }}</strong> 条用例
              </template>
              <span v-if="batchMode && selectedCases.length > 0" class="selected-count">
                ，已选择 <strong>{{ selectedCases.length }}</strong> 项
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

    <TestCaseDialog
      v-model:visible="dialogVisible"
      :is-editing="isEditing"
      :form="form"
      :module-tree="moduleTreeData"
      @update:form="handleFormUpdate"
      @save="handleSubmit"
    />

    <!-- 评审对话框 -->
    <el-dialog
      v-model="reviewVisible"
      :title="reviewEditMode ? '编辑用例' : '用例详情'"
      width="960px"
      destroy-on-close
      :close-on-click-modal="false"
      class="test-case-dialog"
      @close="handleReviewDialogClose"
    >
      <div v-if="reviewCase" class="dialog-content">
        <!-- 查看模式 -->
        <template v-if="!reviewEditMode">
          <div class="form-main">
            <div class="form-item">
              <div class="form-label"><span>用例标题</span></div>
              <div class="form-value">{{ reviewCase.title }}</div>
            </div>

            <div class="form-item">
              <div class="form-label"><span>前置条件</span></div>
              <div v-if="reviewCase.precondition" class="form-value precondition">{{ reviewCase.precondition }}</div>
              <div v-else class="form-value empty">无</div>
            </div>

            <div class="form-item">
              <div class="form-label"><span>测试步骤</span></div>
              <div v-if="reviewCase.steps" class="form-value steps-text">{{ reviewCase.steps }}</div>
              <div v-else class="form-value empty">无</div>
            </div>

            <div class="form-item">
              <div class="form-label"><span>预期结果</span></div>
              <div v-if="reviewCase.expected_result" class="form-value expected-text">{{ reviewCase.expected_result }}</div>
              <div v-else class="form-value empty">无</div>
            </div>

            <!-- 评审记录 -->
            <div v-if="reviewComments.length" class="form-item">
              <div class="form-label"><span>评审历史</span></div>
              <div class="review-records">
                <div v-for="r in reviewComments" :key="r.id" class="record-item">
                  <div class="record-header">
                    <span class="record-round">第 {{ r.revision_number || 1 }} 轮</span>
                    <span class="record-status" :class="r.status">
                      {{ r.status === 'approved' ? '通过' : (r.status === 'rejected' ? '驳回' : '待评审') }}
                    </span>
                    <span class="record-user">{{ r.reviewer_name || '-' }}</span>
                    <span class="record-time">{{ formatReviewDate(r.created_at) }}</span>
                  </div>
                  <div v-if="r.comment" class="record-comment">{{ r.comment }}</div>
                  <div v-if="r.revision_note" class="revision-note">修改说明：{{ r.revision_note }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="info-sidebar">
            <div class="sidebar-title">用例属性</div>

            <div class="info-item">
              <div class="form-label"><span>评审状态</span></div>
              <el-tag
                :type="reviewCase.review_status === 'approved' ? 'success' : (reviewCase.review_status === 'rejected' ? 'danger' : 'warning')"
                :class="{ 'revision-tag': reviewCase.review_status === 'revision_pending' }"
                size="large"
                style="width: 100%; justify-content: center;"
              >
                {{ reviewCase.review_status === 'approved' ? '已通过' : (reviewCase.review_status === 'rejected' ? '已驳回' : (reviewCase.review_status === 'revision_pending' ? '待重审' : '待评审')) }}
              </el-tag>
            </div>

            <div class="info-item">
              <div class="form-label"><span>优先级</span></div>
              <div class="priority-display">
                <span class="priority-badge" :class="reviewCase.priority">{{ getPriorityText(reviewCase.priority) }}</span>
              </div>
            </div>

            <div class="info-item">
              <div class="form-label"><span>所属模块</span></div>
              <div class="form-value">{{ reviewCase.module_name || '未分类' }}</div>
            </div>

            <div class="info-item">
              <div class="form-label"><span>创建人</span></div>
              <div class="form-value">{{ reviewCase.created_by_name }}</div>
            </div>

            <div class="info-item">
              <div class="form-label"><span>创建时间</span></div>
              <div class="form-value">{{ formatReviewDate(reviewCase.created_at) }}</div>
            </div>
          </div>
        </template>

        <!-- 编辑模式 -->
        <template v-else>
          <div class="form-main">
            <div class="form-item">
              <div class="form-label"><span>用例标题</span><span class="required">*</span></div>
              <el-input v-model="reviewEditForm.title" placeholder="请输入用例标题" maxlength="128" show-word-limit />
            </div>

            <div class="form-item">
              <div class="form-label"><span>前置条件</span></div>
              <el-input v-model="reviewEditForm.precondition" type="textarea" :rows="2" placeholder="请输入前置条件" />
            </div>

            <div class="form-item">
              <div class="form-label"><span>测试步骤</span><span class="required">*</span></div>
              <el-input v-model="reviewEditForm.steps" type="textarea" :rows="4" placeholder="请输入测试步骤" />
            </div>

            <div class="form-item">
              <div class="form-label"><span>预期结果</span></div>
              <el-input v-model="reviewEditForm.expected_result" type="textarea" :rows="3" placeholder="请输入预期结果" />
            </div>

            <div class="form-item">
              <div class="form-label"><span>修改说明</span></div>
              <el-input v-model="reviewEditForm.revision_note" type="textarea" :rows="2" placeholder="请描述本次修改内容（可选）" />
            </div>
          </div>

          <div class="info-sidebar">
            <div class="sidebar-title">用例属性</div>

            <div class="info-item">
              <div class="form-label"><span>优先级</span></div>
              <el-select v-model="reviewEditForm.priority" style="width: 100%">
                <el-option label="P0" value="p0" />
                <el-option label="P1" value="p1" />
                <el-option label="P2" value="p2" />
                <el-option label="P3" value="p3" />
              </el-select>
            </div>

            <div class="info-item">
              <div class="form-label"><span>所属模块</span></div>
              <el-tree-select
                v-model="reviewEditForm.module"
                :data="moduleTreeData"
                :props="{ label: 'name', children: 'children', value: 'id' }"
                placeholder="请选择模块"
                clearable
                check-strictly
                style="width: 100%"
              />
            </div>

            <div class="info-item">
              <div class="form-label"><span>关联需求</span></div>
              <el-input v-model="reviewEditForm.requirement" placeholder="请输入关联需求" />
            </div>
          </div>
        </template>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <div class="footer-left"></div>
          <div class="footer-right">
            <!-- 查看模式按钮 -->
            <template v-if="!reviewEditMode">
              <el-button size="large" @click="reviewVisible = false">关闭</el-button>
              <!-- 待评审或待重审状态：可以通过或驳回 -->
              <template v-if="reviewCase?.review_status === 'pending' || reviewCase?.review_status === 'revision_pending'">
                <el-button type="danger" size="large" @click="showRejectDialog">驳回</el-button>
                <el-button type="success" size="large" :loading="reviewSubmitting" @click="handleApprove">通过</el-button>
              </template>
              <!-- 已驳回状态：可以编辑用例 -->
              <template v-else-if="reviewCase?.review_status === 'rejected'">
                <el-button type="primary" size="large" @click="enterReviewEditMode">编辑用例</el-button>
              </template>
            </template>
            <!-- 编辑模式按钮 -->
            <template v-else>
              <el-button size="large" @click="cancelReviewEdit">取消</el-button>
              <el-button type="primary" size="large" :loading="reviewSubmitting" @click="saveAndResubmit">保存并提交重审</el-button>
            </template>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 驳回原因对话框 -->
    <el-dialog v-model="rejectVisible" title="驳回原因" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入驳回原因" />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitting" @click="confirmReject">确定驳回</el-button>
      </template>
    </el-dialog>

    <!-- AI 生成对话框 -->
    <AIGenerateDialog
      v-model:visible="aiGenerateVisible"
      :version-id="selectedVersion"
      :default-version-id="defaultVersionId"
      :versions="versionList"
      :project-id="project?.id"
      @generated="handleAIGenerated"
      @go-to-knowledge="handleGoToKnowledge"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Search, ArrowLeft, ArrowRight, VideoPlay, FolderOpened, Delete, Operation, CopyDocument, MagicStick, Download, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import RepoVersionSelector from '@/views/testcase/components/RepoVersionSelector.vue'
import ModuleTree from '@/views/testcase/components/ModuleTree.vue'
import TestCaseTable from '@/views/testcase/components/TestCaseTable.vue'
import TestCaseDialog from '@/views/testcase/components/TestCaseDialog.vue'
import AIGenerateDialog from '@/views/testcase/components/AIGenerateDialog.vue'

import { DEFAULT_TEST_CASE_FORM } from '@/constants/testcase'
import {
  useRepositoryAndVersion,
  useModuleTree,
  useTestCases
} from '@/composables/testcase/useTestCaseApi'
import { testCaseApi, reviewApi } from '@/api/modules/testcase'
import { exportToExcel, exportToCSV } from '@/utils/export'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)
const batchMode = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedCases = ref([])
const selectedModule = ref(null)
const tableRef = ref(null)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingCaseId = ref(null)

// 评审相关
const reviewVisible = ref(false)
const rejectVisible = ref(false)
const resubmitVisible = ref(false)
const reviewSubmitting = ref(false)
const reviewCase = ref(null)
const rejectReason = ref('')
const resubmitNote = ref('')
const reviewComments = ref([])
const pendingResubmitCaseId = ref(null) // 待重新提交的用例ID

// 评审对话框编辑模式
const reviewEditMode = ref(false)
const reviewEditForm = reactive({
  title: '',
  module: null,
  priority: 'p2',
  precondition: '',
  steps: '',
  expected_result: '',
  requirement: '',
  revision_note: ''
})

// AI 生成相关
const aiGenerateVisible = ref(false)

const PRIORITY_TEXT = { p0: 'P0', p1: 'P1', p2: 'P2', p3: 'P3' }
const getPriorityText = (p) => PRIORITY_TEXT[p] || 'P2'
const formatReviewDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const repoVersion = useRepositoryAndVersion()
const moduleTree = useModuleTree()
const testCases = useTestCases()

const form = reactive({ ...DEFAULT_TEST_CASE_FORM })

const repoList = computed(() => {
  return repoVersion.repositories.value.map(repo => ({
    id: repo.id,
    name: repo.name,
    icon: repo.is_default ? 'Folder' : 'Collection'
  }))
})

const versionList = computed(() => {
  return repoVersion.versions.value.map(v => ({
    id: v.id,
    name: v.name,
    is_default: v.is_default
  }))
})

// 获取默认版本ID
const defaultVersionId = computed(() => {
  const defaultVersion = versionList.value.find(v => v.is_default)
  return defaultVersion?.id || null
})

const moduleTreeData = computed(() => {
  return moduleTree.modules.value
})

const selectedRepo = computed({
  get: () => repoVersion.selectedRepo.value,
  set: (val) => { repoVersion.selectedRepo.value = val }
})

const selectedVersion = computed({
  get: () => repoVersion.selectedVersion.value,
  set: (val) => { repoVersion.selectedVersion.value = val }
})

const repoVersionLoading = computed(() => repoVersion.loading.value)
const moduleLoading = computed(() => moduleTree.loading.value)
const testCaseLoading = computed(() => testCases.loading.value)
const total = computed(() => testCases.total.value)

// 导出相关状态
const exporting = ref(false)

// 是否处于过滤状态
const isFiltering = computed(() => {
  return searchQuery.value.trim() || filterStatus.value || filterPriority.value
})

const fetchRepositories = async () => {
  try {
    await repoVersion.fetchRepositories(props.project?.id)
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
        if (!val || val.trim() === '') {
          return '用例库名称不能为空'
        }
        return true
      }
    })

    await repoVersion.createRepository({
      name: value.trim(),
      project: props.project?.id,
      is_default: repoVersion.repositories.value.length === 0
    })
    ElMessage.success('用例库创建成功')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '创建用例库失败')
    }
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
        if (!val || val.trim() === '') {
          return '版本名称不能为空'
        }
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
    if (err !== 'cancel') {
      ElMessage.error(err.message || '创建版本失败')
    }
  }
}

const handleManageRepo = () => {
  const projectCode = route.params.code
  router.push({
    path: `/p/${projectCode}/t/manage-repo`
  })
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
  if (!repoVersion.selectedVersion.value) {
    ElMessage.warning('请先选择版本')
    return
  }

  try {
    const { value } = await ElMessageBox.prompt('请输入模块名称', '添加模块', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValidator: (val) => {
        if (!val || val.trim() === '') {
          return '模块名称不能为空'
        }
        return true
      }
    })

    await moduleTree.createModule({
      name: value.trim(),
      version: Number(repoVersion.selectedVersion.value),
      parent: selectedModule.value ? Number(selectedModule.value) : null
    })
    ElMessage.success('模块添加成功')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '添加模块失败')
    }
  }
}

const handleAddSubModule = async (parentModule) => {
  if (!repoVersion.selectedVersion.value) {
    ElMessage.warning('请先选择版本')
    return
  }

  try {
    const { value } = await ElMessageBox.prompt(`请在 "${parentModule.name}" 下添加子模块`, '添加子模块', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValidator: (val) => {
        if (!val || val.trim() === '') {
          return '模块名称不能为空'
        }
        return true
      }
    })

    await moduleTree.createModule({
      name: value.trim(),
      version: Number(repoVersion.selectedVersion.value),
      parent: parentModule.id
    })
    ElMessage.success('子模块添加成功')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '添加子模块失败')
    }
  }
}

const handleEditModule = async (module) => {
  try {
    const { value } = await ElMessageBox.prompt('修改模块名称', '编辑模块', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: module.name,
      inputValidator: (val) => {
        if (!val || val.trim() === '') {
          return '模块名称不能为空'
        }
        return true
      }
    })

    await moduleTree.updateModule(module.id, {
      name: value.trim()
    })
    ElMessage.success('模块更新成功')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '更新模块失败')
    }
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

    await moduleTree.deleteModule(module.id, repoVersion.selectedVersion.value)
    ElMessage.success('模块删除成功')

    if (selectedModule.value === module.id) {
      selectedModule.value = null
      currentPage.value = 1
      await testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value, { page: 1, page_size: pageSize.value })
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除模块失败')
    }
  }
}

const handleModuleClick = (data) => {
  selectedModule.value = data.id
  currentPage.value = 1
  testCases.fetchTestCasesByModule(data.id, { page: 1, page_size: pageSize.value })
}

const handleShowAllCases = () => {
  selectedModule.value = null
  currentPage.value = 1
  if (repoVersion.selectedVersion.value) {
    testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value, { page: 1, page_size: pageSize.value })
  }
}

const handleModuleRefresh = async () => {
  if (repoVersion.selectedVersion.value) {
    await moduleTree.fetchModuleTree(repoVersion.selectedVersion.value)
    await testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value, { page: currentPage.value, page_size: pageSize.value })
  }
}

const handleCreateTestCase = () => {
  isEditing.value = false
  editingCaseId.value = null
  Object.assign(form, {
    ...DEFAULT_TEST_CASE_FORM,
    module: selectedModule.value || null
  })
  dialogVisible.value = true
}

const handleSelectionChange = (selection) => {
  selectedCases.value = selection
}

const handleCommand = ({ command, row }) => {
  const handlers = {
    execute: handleExecuteCase,
    edit: handleEditCase,
    copy: handleCopyCase,
    delete: handleDeleteCase
  }
  handlers[command]?.(row)
}

const handleExecuteCase = (row) => ElMessage.success(`开始执行用例: ${row.name || row.title}`)

const handleEditCase = async (row) => {
  isEditing.value = true
  editingCaseId.value = row.id

  try {
    const response = await testCases.getTestCase(row.id)
    const caseDetail = response?.data || response || {}
    Object.assign(form, {
      title: caseDetail.title || '',
      module: caseDetail.module,
      version: caseDetail.version || repoVersion.selectedVersion.value,
      precondition: caseDetail.precondition || '',
      steps: caseDetail.steps || '',
      expected_result: caseDetail.expected_result || '',
      priority: caseDetail.priority || 'p2',
      estimated_hours: caseDetail.estimated_hours ?? null,
      tags: caseDetail.tags || [],
      automation_status: caseDetail.automation_status || 'not_analyzed',
      automation_case_id: caseDetail.automation_case_id || '',
      requirement: caseDetail.requirement || ''
    })
    dialogVisible.value = true
  } catch (err) {
    ElMessage.error(err.message || '获取用例详情失败')
  }
}

const handleCopyCase = async (row) => {
  try {
    await testCases.copyTestCase(row.id)
    ElMessage.success(`已复制用例: ${row.name || row.title}`)
    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || '复制用例失败')
  }
}

const handleDeleteCase = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试用例 "${row.name || row.title}" 吗？`, '警告', {
      type: 'warning'
    })
    await testCases.deleteTestCase(row.id)
    ElMessage.success('删除成功')
    await refreshTestCases()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除用例失败')
    }
  }
}

// 评审相关方法
const handleReview = async (row) => {
  try {
    const res = await testCaseApi.getTestCase(row.id)
    reviewCase.value = res || row
    // 获取评审历史
    try {
      const reviewRes = await reviewApi.getReviewHistory(row.id)
      reviewComments.value = reviewRes || []
    } catch {
      reviewComments.value = []
    }
    reviewVisible.value = true
  } catch (err) {
    ElMessage.error(err.message || '获取用例详情失败')
  }
}

const handleApprove = async () => {
  reviewSubmitting.value = true
  try {
    await reviewApi.approveReview(reviewCase.value.id, '评审通过')
    ElMessage.success('评审通过')
    reviewVisible.value = false
    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    reviewSubmitting.value = false
  }
}

const showRejectDialog = () => {
  rejectReason.value = ''
  rejectVisible.value = true
}

const confirmReject = async () => {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  reviewSubmitting.value = true
  try {
    await reviewApi.rejectReview(reviewCase.value.id, rejectReason.value)
    ElMessage.success('已驳回')
    rejectVisible.value = false
    reviewVisible.value = false
    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    reviewSubmitting.value = false
  }
}

// 处理编辑用例（从评审面板触发）
const handleEditFromReview = (caseData) => {
  isEditing.value = true
  editingCaseId.value = caseData.id
  form.value = { ...DEFAULT_TEST_CASE_FORM, ...caseData }
  dialogVisible.value = true
}

// 进入评审对话框的编辑模式
const enterReviewEditMode = () => {
  if (!reviewCase.value) return

  reviewEditMode.value = true
  // 将当前用例内容填充到编辑表单
  reviewEditForm.title = reviewCase.value.title || ''
  reviewEditForm.module = reviewCase.value.module || null
  reviewEditForm.priority = reviewCase.value.priority || 'p2'
  reviewEditForm.precondition = reviewCase.value.precondition || ''
  reviewEditForm.steps = reviewCase.value.steps || ''
  reviewEditForm.expected_result = reviewCase.value.expected_result || ''
  reviewEditForm.requirement = reviewCase.value.requirement || ''
  reviewEditForm.revision_note = ''
}

// 取消编辑模式
const cancelReviewEdit = () => {
  reviewEditMode.value = false
}

// 保存编辑并重新提交评审
const saveAndResubmit = async () => {
  if (!reviewEditForm.title.trim()) {
    ElMessage.warning('请填写用例标题')
    return
  }
  if (!reviewEditForm.steps.trim()) {
    ElMessage.warning('请填写测试步骤')
    return
  }

  reviewSubmitting.value = true
  try {
    // 1. 更新用例内容
    const updateData = {
      title: reviewEditForm.title,
      module: reviewEditForm.module,
      version: reviewCase.value.version, // 必须传递 version
      priority: reviewEditForm.priority,
      precondition: reviewEditForm.precondition,
      steps: reviewEditForm.steps,
      expected_result: reviewEditForm.expected_result,
      requirement: reviewEditForm.requirement
    }
    await testCaseApi.updateTestCase(reviewCase.value.id, updateData)

    // 2. 重新提交评审
    await reviewApi.resubmitReview(reviewCase.value.id, reviewEditForm.revision_note)

    ElMessage.success('已保存并重新提交评审')
    reviewVisible.value = false
    reviewEditMode.value = false
    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    reviewSubmitting.value = false
  }
}

// 评审对话框关闭时重置编辑模式
const handleReviewDialogClose = () => {
  reviewEditMode.value = false
}

// AI 生成相关方法
const handleOpenAIGenerate = () => {
  if (!selectedVersion.value) {
    ElMessage.warning('请先选择版本')
    return
  }
  aiGenerateVisible.value = true
}

const handleAIGenerated = async (result) => {
  if (result.created_count > 0) {
    ElMessage.success(`成功生成 ${result.created_count} 条测试用例`)
    await refreshTestCases()
    // 刷新模块树
    if (selectedVersion.value) {
      await moduleTree.fetchModuleTree(selectedVersion.value)
    }
  }
}

const handleGoToKnowledge = () => {
  const projectCode = route.params.code
  router.push({
    path: `/p/${projectCode}/knowledge`
  })
}

const handleBatchExecute = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return false
  }
  ElMessage.success(`批量执行 ${selectedCases.value.length} 个用例`)
  return true
}

const handleBatchMove = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要移动的用例')
    return false
  }
  ElMessage.info('批量移动功能开发中')
  return false
}

const handleBatchCopy = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要复制的用例')
    return false
  }
  try {
    const ids = selectedCases.value.map(c => c.id)
    const response = await testCases.batchCopy?.(ids)
    const copiedCount = response?.data?.copied_count || selectedCases.value.length
    ElMessage.success(`成功复制 ${copiedCount} 个用例`)
    await refreshTestCases()
    return true
  } catch (err) {
    ElMessage.error(err.message || '批量复制失败')
    return false
  }
}

const handleBatchDelete = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的用例')
    return false
  }
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCases.value.length} 个用例吗？`, '警告', {
      type: 'warning'
    })
    const ids = selectedCases.value.map(c => c.id)
    const response = await testCases.batchDelete?.(ids)
    const deletedCount = response?.data?.deleted_count || selectedCases.value.length
    ElMessage.success(`成功删除 ${deletedCount} 个用例`)
    await refreshTestCases()
    return true
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '批量删除失败')
    }
    return false
  }
}

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    selectedCases.value = []
    tableRef.value?.clearSelection()
  }
}

const handleBatchAction = async (action) => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择用例后再进行批量操作')
    return
  }

  const handlers = {
    execute: handleBatchExecute,
    move: handleBatchMove,
    copy: handleBatchCopy,
    delete: handleBatchDelete
  }

  const success = await handlers[action]?.()
  if (success) {
    batchMode.value = false
    selectedCases.value = []
    tableRef.value?.clearSelection()
  }
}

const handleFormUpdate = (updatedForm) => {
  Object.assign(form, updatedForm)
}

const handleSubmit = async (continueCreate = false) => {
  if (!form.title || !form.module) {
    ElMessage.warning('请填写用例标题和所属模块')
    return
  }

  if (!form.steps.trim()) {
    ElMessage.warning('请至少填写测试步骤')
    return
  }

  try {
    const data = {
      title: form.title,
      module: form.module,
      version: repoVersion.selectedVersion.value,
      priority: form.priority,
      automation_status: form.automation_status,
      estimated_hours: form.estimated_hours,
      requirement: form.requirement,
      automation_case_id: form.automation_case_id,
      tags: form.tags || [],
      precondition: form.precondition,
      steps: form.steps,
      expected_result: form.expected_result
    }

    if (isEditing.value) {
      await testCases.updateTestCase(editingCaseId.value, data)
      ElMessage.success('更新成功')
      dialogVisible.value = false

      // 如果是被驳回的用例，编辑保存后弹出重新提交对话框
      if (pendingResubmitCaseId.value === editingCaseId.value) {
        await refreshTestCases()
        resubmitVisible.value = true
      }
    } else {
      await testCases.createTestCase(data)
      ElMessage.success('创建成功')
      if (continueCreate) {
        resetForm()
      } else {
        dialogVisible.value = false
      }
    }

    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || (isEditing.value ? '更新失败' : '创建失败'))
  }
}

const resetForm = () => {
  Object.assign(form, { ...DEFAULT_TEST_CASE_FORM })
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  loadTestCases()
}

// 搜索防抖定时器
let searchDebounceTimer = null

const loadTestCases = async () => {
  const params = { page: currentPage.value, page_size: pageSize.value }

  // 添加搜索参数
  if (searchQuery.value.trim()) {
    params.search = searchQuery.value.trim()
  }

  // 添加优先级筛选参数
  if (filterPriority.value) {
    params.priority = filterPriority.value
  }

  // 添加执行状态筛选参数
  if (filterStatus.value) {
    params.last_execution_result = filterStatus.value
  }

  if (selectedModule.value) {
    await testCases.fetchTestCasesByModule(selectedModule.value, params)
  } else if (repoVersion.selectedVersion.value) {
    await testCases.fetchTestCasesByVersion(repoVersion.selectedVersion.value, params)
  }
}

const refreshTestCases = async () => {
  await loadTestCases()
}

// 导出功能
const handleExport = async (format) => {
  if (!selectedVersion.value) {
    ElMessage.warning('请先选择版本')
    return
  }

  exporting.value = true
  try {
    // 使用专门的导出API（不分页）
    const params = {}
    if (selectedModule.value) {
      params.module = selectedModule.value
    } else {
      params.version = selectedVersion.value
    }

    const res = await testCaseApi.exportTestCases(params)
    const testCasesData = res?.data?.results || res?.data || res || []

    if (!testCasesData.length) {
      ElMessage.warning('没有测试用例可导出')
      return
    }

    // 获取版本名称用于文件名
    const versionInfo = repoVersion.versions.value.find(v => v.id === selectedVersion.value)
    const versionName = versionInfo?.name || '测试用例'
    const filename = `${versionName}_${new Date().toISOString().slice(0, 10)}`

    if (format === 'excel') {
      await exportToExcel(testCasesData, filename)
      ElMessage.success(`已导出 ${testCasesData.length} 条测试用例到 Excel`)
    } else if (format === 'csv') {
      exportToCSV(testCasesData, filename)
      ElMessage.success(`已导出 ${testCasesData.length} 条测试用例到 CSV`)
    }
  } catch (err) {
    ElMessage.error(err.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

// 监听搜索条件变化，触发后端搜索（带防抖）
watch([searchQuery, filterPriority, filterStatus], () => {
  // 清除之前的定时器
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }

  // 设置新的防抖定时器（300ms）
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadTestCases()
  }, 300)
})

watch(() => repoVersion.selectedRepo.value, async (newRepoId, oldRepoId) => {
  if (newRepoId && newRepoId !== oldRepoId) {
    repoVersion.selectedVersion.value = null
    selectedModule.value = null
    repoVersion.versions.value = []
    moduleTree.modules.value = []
    testCases.testCases.value = []
    // 清空搜索条件
    searchQuery.value = ''
    filterPriority.value = ''
    filterStatus.value = ''
    await fetchVersions(newRepoId)
  }
})

watch(() => repoVersion.selectedVersion.value, async (newVersionId, oldVersionId) => {
  if (newVersionId && newVersionId !== oldVersionId) {
    selectedModule.value = null
    currentPage.value = 1
    // 清空搜索条件
    searchQuery.value = ''
    filterPriority.value = ''
    filterStatus.value = ''
    await Promise.all([
      moduleTree.fetchModuleTree(newVersionId),
      testCases.fetchTestCasesByVersion(newVersionId, { page: 1, page_size: pageSize.value })
    ])
  }
})

watch(() => props.project, (newProject) => {
  if (newProject?.id) {
    fetchRepositories()
  }
}, { immediate: true })
</script>

<style scoped>
.test-case-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.case-container {
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

.search-box {
  width: 280px;
}

.search-box :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-light) inset;
}

.search-box :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item {
  width: 120px;
}

.filter-item :deep(.el-input__wrapper) {
  border-radius: 2px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-right .el-button {
  border-radius: 2px;
}

.selected-count {
  color: var(--color-primary);
  font-size: 13px;
}

.selected-count strong {
  color: var(--color-primary);
}

.batch-operation-wrapper {
  position: relative;
  display: inline-block;
}

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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #333;
  font-size: 14px;
}

.batch-menu-item:hover {
  background: var(--color-bg-secondary);
}

.batch-menu-item.disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.batch-menu-item.disabled:hover {
  background: transparent;
}

.batch-menu-item.danger {
  color: var(--color-danger);
}

.batch-menu-item.danger:hover {
  background: var(--color-danger-light);
}

.batch-menu-item.danger.disabled {
  color: var(--color-danger);
}

.batch-menu-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--color-bg-tertiary);
}

.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: all 0.2s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.table-section {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #fff;
  margin: 16px;
  margin-bottom: 0;
  border-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid var(--color-border-secondary);
  margin: 0 16px 16px;
  border-radius: 0 0 2px 2px;
  flex-shrink: 0;
}

.pagination-info {
  font-size: 13px;
  color: #666;
}

.pagination-info strong {
  color: #333;
}

.review-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

@media screen and (max-width: 1400px) {
  .filter-item {
    width: 100px;
  }

  .search-box {
    width: 240px;
  }
}

@media screen and (max-width: 1200px) {
  .toolbar-section {
    flex-wrap: wrap;
    padding: 12px 16px;
  }

  .toolbar-left {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-box {
    width: 200px;
  }

  .filter-item {
    width: 90px;
  }

  .toolbar-right {
    width: 100%;
    justify-content: flex-end;
    margin-top: 8px;
  }
}

@media screen and (max-width: 992px) {
  .sidebar-wrapper:not(.collapsed) {
    position: absolute;
    z-index: 100;
    background: #fff;
    height: 100%;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }

  .sidebar-wrapper.collapsed {
    width: 0;
  }

  .filter-group {
    flex-wrap: wrap;
    gap: 6px;
  }

  .filter-item {
    width: 85px;
  }

  .search-box {
    width: 180px;
  }
}

@media screen and (max-width: 768px) {
  .toolbar-section {
    padding: 10px 12px;
  }

  .toolbar-left {
    gap: 10px;
  }

  .search-box {
    width: 100%;
    order: 1;
  }

  .filter-group {
    width: 100%;
    order: 2;
    margin-top: 8px;
  }

  .filter-item {
    flex: 1;
    min-width: 80px;
  }

  .toolbar-right {
    margin-top: 12px;
    gap: 6px;
  }

  .toolbar-right .el-button {
    padding: 8px 12px;
    font-size: 13px;
  }

  .table-section {
    margin: 12px;
    margin-bottom: 0;
  }

  .pagination-section {
    margin: 0 12px 12px;
    flex-direction: column;
    gap: 10px;
    padding: 10px 12px;
  }
}

@media screen and (max-width: 576px) {
  .toolbar-right {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .toolbar-right .el-button {
    flex: 1;
    min-width: 100px;
  }

  .batch-operation-wrapper {
    flex: 1;
    min-width: 100px;
  }

  .batch-menu {
    right: auto;
    left: 0;
  }
}

/* 评审详情样式 - 与新建用例对话框一致 */
.test-case-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-bg-tertiary);
  margin-right: 0;
}

.test-case-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.test-case-dialog :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

.test-case-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.test-case-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

.dialog-content {
  display: flex;
  min-height: 300px;
  max-height: 480px;
}

.form-main {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-value {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.form-value.empty {
  color: var(--color-text-tertiary);
}

.form-value.precondition {
  white-space: pre-wrap;
}

.form-value.steps-text {
  white-space: pre-wrap;
  background: var(--color-bg-secondary);
  padding: 8px 12px;
  border-radius: 2px;
  border: 1px solid var(--color-bg-tertiary);
}

.form-value.expected-text {
  white-space: pre-wrap;
  color: var(--color-success);
  background: var(--color-bg-secondary);
  padding: 8px 12px;
  border-radius: 2px;
  border: 1px solid var(--color-bg-tertiary);
}

.steps-container {
  border: 1px solid var(--color-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.steps-header {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-bg-tertiary);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.col-index {
  width: 32px;
  text-align: center;
}

.col-step {
  flex: 1;
  padding: 0 8px;
}

.col-expected {
  flex: 1;
  padding: 0 8px;
}

.steps-body {
  max-height: 200px;
  overflow-y: auto;
}

.step-row {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border-secondary);
  gap: 8px;
}

.step-row:last-child {
  border-bottom: none;
}

.step-index {
  width: 20px;
  height: 20px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content,
.step-expected {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.5;
}

.review-records {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  font-size: 13px;
}

.record-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-round {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
}

.record-status {
  padding: 2px 8px;
  border-radius: 2px;
  font-weight: 500;
  font-size: 12px;
}

.record-status.approved {
  background: #d4edda;
  color: #155724;
}

.record-status.rejected {
  background: #f8d7da;
  color: #721c24;
}

.record-status.pending {
  background: #fef3cd;
  color: #856404;
}

.record-status.revision_pending {
  background: #f3e8ff;
  color: #7c3aed;
}

.record-user {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.record-time {
  color: var(--color-text-tertiary);
  font-size: 12px;
  margin-left: auto;
}

.record-comment {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.revision-note {
  color: var(--color-primary);
  font-size: 12px;
  padding-top: 6px;
  border-top: 1px dashed var(--color-border-secondary);
}

.resubmit-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-primary-light);
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-primary);
}

/* 待重审状态标签样式 - 紫色 */
.revision-tag {
  --el-tag-bg-color: #f3e8ff !important;
  --el-tag-border-color: #c4b5fd !important;
  --el-tag-text-color: #7c3aed !important;
}

.revision-tag:deep(.el-tag__content) {
  color: #7c3aed !important;
}

.record-user {
  color: var(--color-text-primary);
}

.record-time {
  color: var(--color-text-tertiary);
}

.record-comment {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.info-sidebar {
  width: 220px;
  background: var(--color-bg-secondary);
  padding: 16px 12px;
  border-left: 1px solid var(--color-bg-tertiary);
  overflow-y: auto;
}

.info-sidebar .form-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.form-label .required {
  color: var(--color-danger);
  margin-left: 2px;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.info-item {
  margin-bottom: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .form-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.info-item .form-value {
  font-size: 13px;
  color: var(--color-text-primary);
}

.priority-display {
  display: flex;
  align-items: center;
}

.priority-badge {
  width: 32px;
  height: 20px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.priority-badge.p0 {
  background: var(--color-danger);
}

.priority-badge.p1 {
  background: var(--color-warning);
}

.priority-badge.p2 {
  background: var(--color-primary);
}

.priority-badge.p3 {
  background: var(--color-text-tertiary);
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-top: 1px solid var(--color-bg-tertiary);
  background: var(--color-bg-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-right {
  display: flex;
  gap: 8px;
}
</style>
