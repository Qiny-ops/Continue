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

    <!-- 提交重审对话框（被驳回用例编辑保存后弹出） -->
    <el-dialog
      v-model="resubmitVisible"
      title="提交重审"
      width="440px"
      @close="resubmitNote = ''; pendingResubmitCaseId = null"
    >
      <div class="resubmit-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>该用例此前被驳回，已保存修改。确认后将以「修改后待重审」状态重新进入评审流程。</span>
      </div>
      <el-input
        v-model="resubmitNote"
        type="textarea"
        :rows="3"
        maxlength="500"
        show-word-limit
        placeholder="请填写本次修改说明（可选）"
      />
      <template #footer>
        <el-button @click="resubmitVisible = false">暂不提交</el-button>
        <el-button type="primary" :loading="resubmitSubmitting" @click="confirmResubmit">提交重审</el-button>
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

    <!-- Web 自动化执行对话框 -->
    <WebExecuteDialog
      v-model:visible="webExecuteVisible"
      :cases="webExecuteCases"
      :project-id="project?.id"
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
import WebExecuteDialog from '@/views/projects/components/WebExecuteDialog.vue'

import { DEFAULT_TEST_CASE_FORM } from '@/constants/testcase'
import { useTestCases } from '@/composables/testcase/useTestCaseApi'
import { useRepoVersionModuleTree } from '@/composables/testcase/useRepoVersionModuleTree'
import { useTestCaseReview } from '@/composables/testcase/useTestCaseReview'
import { useBatchOperation } from '@/composables/testcase/useBatchOperation'
import { testCaseApi, reviewApi } from '@/api/modules/testcase'
import { exportToExcel, exportToCSV } from '@/utils/export'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

const projectId = computed(() => props.project?.id)
const router = useRouter()
const route = useRoute()

const testCases = useTestCases()

const {
  moduleTree,
  selectedRepo,
  selectedVersion,
  repoList,
  versionList,
  defaultVersionId,
  repoVersionLoading,
  moduleTreeData,
  moduleLoading,
  selectedModule,
  sidebarCollapsed,
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
} = useRepoVersionModuleTree({
  projectId,
  onVersionChange: (versionId) => {
    currentPage.value = 1
    searchQuery.value = ''
    filterPriority.value = ''
    filterStatus.value = ''
    testCases.fetchTestCasesByVersion(versionId, { page: 1, page_size: pageSize.value })
  },
  onModuleChange: (moduleId) => {
    currentPage.value = 1
    if (moduleId) {
      testCases.fetchTestCasesByModule(moduleId, { page: 1, page_size: pageSize.value })
    } else if (selectedVersion.value) {
      testCases.fetchTestCasesByVersion(selectedVersion.value, { page: 1, page_size: pageSize.value })
    }
  },
  onModuleDelete: () => {
    currentPage.value = 1
    if (selectedVersion.value) {
      testCases.fetchTestCasesByVersion(selectedVersion.value, { page: 1, page_size: pageSize.value })
    }
  }
})

const searchQuery = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const tableRef = ref(null)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingCaseId = ref(null)

// 被驳回用例编辑保存后「提交重审」相关状态
const pendingResubmitCaseId = ref(null)
const resubmitVisible = ref(false)
const resubmitNote = ref('')
const resubmitSubmitting = ref(false)

const aiGenerateVisible = ref(false)
const exporting = ref(false)

// Web 自动化执行弹窗
const webExecuteVisible = ref(false)
const webExecuteCases = ref([])

const form = reactive({ ...DEFAULT_TEST_CASE_FORM })

const testCaseLoading = computed(() => testCases.loading.value)
const total = computed(() => testCases.total.value)

const isFiltering = computed(() => {
  return searchQuery.value.trim() || filterStatus.value || filterPriority.value
})

const PRIORITY_TEXT = { p0: 'P0', p1: 'P1', p2: 'P2', p3: 'P3' }
const getPriorityText = (p) => PRIORITY_TEXT[p] || 'P2'

const handleCreateTestCase = () => {
  isEditing.value = false
  editingCaseId.value = null
  pendingResubmitCaseId.value = null
  Object.assign(form, {
    ...DEFAULT_TEST_CASE_FORM,
    module: selectedModule.value || null
  })
  dialogVisible.value = true
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

const handleExecuteCase = (row) => {
  // 点击功能用例表格的「执行」按钮：调用 Web 自动化微服务
  webExecuteCases.value = [row]
  webExecuteVisible.value = true
}

const handleEditCase = async (row) => {
  isEditing.value = true
  editingCaseId.value = row.id
  // 标记：若编辑的是被驳回用例，保存后弹出「提交重审」对话框
  pendingResubmitCaseId.value = row.review_status === 'rejected' ? row.id : null

  try {
    const response = await testCases.getTestCase(row.id)
    const caseDetail = response?.data || response || {}
    Object.assign(form, {
      title: caseDetail.title || '',
      module: caseDetail.module,
      version: caseDetail.version || selectedVersion.value,
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
      version: selectedVersion.value,
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
        resubmitNote.value = ''
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

// 被驳回用例编辑保存后，在重提对话框中确认「提交重审」
const confirmResubmit = async () => {
  resubmitSubmitting.value = true
  try {
    await reviewApi.resubmitReview(editingCaseId.value, resubmitNote.value)
    ElMessage.success('已提交重审')
    resubmitVisible.value = false
    resubmitNote.value = ''
    pendingResubmitCaseId.value = null
    await refreshTestCases()
  } catch (err) {
    ElMessage.error(err.message || '提交重审失败')
  } finally {
    resubmitSubmitting.value = false
  }
}

const handlePageChange = (page, size) => {
  currentPage.value = page
  pageSize.value = size
  loadTestCases()
}

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
  } else if (selectedVersion.value) {
    await testCases.fetchTestCasesByVersion(selectedVersion.value, params)
  }
}

const refreshTestCases = async () => {
  await loadTestCases()
}

// ---- 批量操作（Composable，必须在 refreshTestCases 之后） ----
const {
  batchMode, selectedCases,
  handleSelectionChange,
  handleBatchExecute, handleBatchMove, handleBatchCopy, handleBatchDelete,
  toggleBatchMode, handleBatchAction
} = useBatchOperation(refreshTestCases, testCases, {
  onExecute: (cases) => {
    webExecuteCases.value = cases
    webExecuteVisible.value = true
  }
})

// ---- 评审流程（Composable，必须在 refreshTestCases 之后） ----
const {
  reviewVisible, rejectVisible, reviewSubmitting, reviewCase,
  rejectReason, reviewComments, reviewEditMode, reviewEditForm,
  formatReviewDate,
  handleReview, handleApprove, showRejectDialog, confirmReject,
  enterReviewEditMode, cancelReviewEdit, saveAndResubmit, handleReviewDialogClose
} = useTestCaseReview(refreshTestCases)

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
    const versionInfo = versionList.value.find(v => v.id === selectedVersion.value)
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
let searchDebounceTimer = null

watch([searchQuery, filterPriority, filterStatus], () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadTestCases()
  }, 300)
})
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
