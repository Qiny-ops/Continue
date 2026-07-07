<template>
  <div class="apitest-page">
    <div class="apitest-container">
      <!-- 环境选择栏 -->
      <EnvSelector
        :env-list="environments"
        :selected-env="selectedEnvironmentId"
        :loading="envLoading"
        @update:selected-env="selectedEnvironmentId = $event"
        @create="handleAddEnv"
        @manage="handleGoEnvironments"
      />

      <!-- 工具栏 -->
      <div class="toolbar-section">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索测试用例..."
            clearable
            style="width: 280px"
            :prefix-icon="Search"
          />
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="handleAddCase">
            <el-icon><Plus /></el-icon>
            新建用例
          </el-button>
          <el-button type="success" plain @click="handleAIGenerate">
            <el-icon><MagicStick /></el-icon>
            AI生成
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
                  :class="{ disabled: selectedCases.length === 0 }"
                  @click="handleBatchAction('execute')"
                >
                  <el-icon><VideoPlay /></el-icon>
                  <span>批量执行</span>
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

      <!-- 表格区域 -->
      <div class="table-section">
        <el-table
          ref="tableRef"
          :data="tableData"
          v-loading="loading"
          style="width: 100%; height: 100%"
          empty-text="暂无测试用例"
          row-key="id"
          @selection-change="handleSelectionChange"
        >
          <el-table-column v-if="batchMode" type="selection" width="50" reserve-selection />

          <el-table-column prop="name" label="接口名称" min-width="180">
            <template #default="{ row }">
              <span class="case-title">{{ row.name }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="precondition" label="前置条件" min-width="150">
            <template #default="{ row }">
              <span class="cell-text">{{ row.precondition || '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="testpoint" label="测试点" min-width="200">
            <template #default="{ row }">
              <span class="cell-text">{{ row.testpoint || '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="expectation" label="预期结果" min-width="200">
            <template #default="{ row }">
              <span class="cell-text">{{ row.expectation || '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="执行状态" width="100" align="center">
            <template #default="{ row }">
              <span class="status-badge" :class="row.last_run_result || 'none'">
                {{ getRunResultLabel(row.last_run_result) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-cell">
                <el-tooltip content="执行" placement="top">
                  <span class="action-btn execute" @click="handleExecuteCase(row)">
                    <el-icon><VideoPlay /></el-icon>
                  </span>
                </el-tooltip>
                <el-tooltip content="编辑" placement="top">
                  <span class="action-btn edit" @click="handleEditCase(row)">
                    <el-icon><Edit /></el-icon>
                  </span>
                </el-tooltip>
                <el-dropdown trigger="click" @command="(cmd) => handleActionCommand(cmd, row)">
                  <span class="action-btn more">
                    <el-icon><MoreFilled /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="delete">
                        <el-icon><Delete /></el-icon>
                        <span class="delete-text">删除用例</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
      </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-section">
        <div class="pagination-info">
          共 <strong>{{ totalCases }}</strong> 条测试用例
          <span v-if="batchMode && selectedCases.length > 0" class="selected-count">
            ，已选择 <strong>{{ selectedCases.length }}</strong> 项
          </span>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalCases"
          layout="sizes, prev, pager, next"
          @current-change="fetchData"
          @size-change="handlePageSizeChange"
        />
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="caseDialogVisible"
      :title="editingCase?.id ? '编辑测试用例' : '新建测试用例'"
      width="700px"
      destroy-on-close
    >
      <el-form :model="caseForm" label-width="100px">
        <el-form-item label="接口名称" required>
          <el-input v-model="caseForm.name" placeholder="请输入接口名称" />
        </el-form-item>

        <el-form-item label="测试点" required>
          <el-input
            v-model="caseForm.testpoint"
            type="textarea"
            :rows="3"
            placeholder="请输入测试点"
          />
        </el-form-item>

        <el-form-item label="前置条件">
          <el-input
            v-model="caseForm.precondition"
            type="textarea"
            :rows="2"
            placeholder="请输入前置条件（可选）"
          />
        </el-form-item>

        <el-form-item label="预期结果" required>
          <el-input
            v-model="caseForm.expectation"
            type="textarea"
            :rows="3"
            placeholder="请输入预期结果"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCase">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI生成对话框 -->
    <AIGenerateDialog
      v-model:visible="aiGenerateDialogVisible"
      :project-knowledge-base="projectKnowledgeBase"
      :project-id="projectId"
      @generated="handleGenerated"
    />

    <!-- 新建环境对话框 -->
    <el-dialog
      v-model="envDialogVisible"
      title="新建环境"
      width="500px"
      destroy-on-close
    >
      <el-form ref="envFormRef" :model="envForm" :rules="envRules" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="envForm.name" placeholder="如: 测试环境" />
        </el-form-item>
        <el-form-item label="环境类型" prop="env_type">
          <el-select v-model="envForm.env_type" placeholder="选择环境类型" style="width: 100%">
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="test" />
            <el-option label="预发布环境" value="staging" />
            <el-option label="生产环境" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="envForm.base_url" placeholder="如: http://api.example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="envForm.description" type="textarea" :rows="2" placeholder="环境描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="envDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="envSubmitting" @click="handleSaveEnv">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行对话框 -->
    <ExecuteDialog
      v-model:visible="executeDialogVisible"
      :executing="executing"
      :validating="validating"
      :status="executeStatus"
      :case-name="executingCase?.name"
      :testpoint="executingCase?.testpoint"
      :duration="executeDuration"
      :logs="executePreview"
      :key-decisions="executeSteps"
      :thinking-content="thinkingContent"
      :failure-analysis="failureAnalysis"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, MagicStick, Loading, CircleCheck, VideoPlay, Edit, MoreFilled, Delete, Operation } from '@element-plus/icons-vue'
import { apiTestCaseApi, environmentApi } from '@/api/modules/apitest'
import { useProjectStore } from '@/stores/modules/project'
import EnvSelector from './components/EnvSelector.vue'
import ExecuteDialog from './components/ExecuteDialog.vue'
import AIGenerateDialog from './components/AIGenerateDialog.vue'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const envLoading = ref(false)
const caseList = ref([])
const totalCases = ref(0)
const environments = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const projectId = computed(() => projectStore.currentProject?.id)
const projectCode = computed(() => projectStore.currentProject?.code)

// 表格数据直接使用 caseList（已由后端分页）
const tableData = computed(() => caseList.value)

// 对话框
const caseDialogVisible = ref(false)
const editingCase = ref(null)
const caseForm = ref({
  name: '',
  testpoint: '',
  precondition: '',
  expectation: ''
})

const aiGenerateDialogVisible = ref(false)

const projectKnowledgeBase = computed(() => {
  const project = projectStore.currentProject
  if (project?.knowledgeBaseId) {
    return {
      id: project.knowledgeBaseId,
      name: project.knowledgeBaseName || project.knowledgeBaseId
    }
  }
  return null
})

const executingCase = ref(null)
const selectedEnvironmentId = ref(null)
const executing = ref(false)
const executeDialogVisible = ref(false)
const executePreview = ref('')
const executeStatus = ref('idle')
const executeDuration = ref(null)
const executeEnvId = ref(null)
const tableRef = ref(null)
const selectedCases = ref([])

// AI 分析相关
const aiKeyDecisions = ref([])
// 执行步骤详情（包含更丰富的信息）
const executeSteps = ref([])
// 流式思考内容
const thinkingContent = ref('')
// 当前正在执行的步骤索引
const runningStepIndex = ref(-1)
// 执行结果列表（用于校验）
const executionResults = ref([])
// 失败分析结果
const failureAnalysis = ref(null)
// 校验中状态
const validating = ref(false)

// 环境对话框
const envDialogVisible = ref(false)
const envSubmitting = ref(false)
const envFormRef = ref(null)
const envForm = ref({
  name: '',
  env_type: 'test',
  base_url: '',
  description: ''
})
const envRules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }]
}

// 执行结果映射
const RUN_RESULT_LABELS = {
  pass: '通过',
  fail: '失败',
  error: '错误',
  running: '执行中',
  cancelled: '已取消',
  none: '未执行'
}

const getRunResultLabel = (result) => RUN_RESULT_LABELS[result] || '未执行'

// 批量选择相关
const batchMode = ref(false)

const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  if (!batchMode.value) {
    clearSelection()
  }
}

const isAllSelected = computed(() => {
  return selectedCases.value.length === tableData.value.length && tableData.value.length > 0
})

const isIndeterminate = computed(() => {
  return selectedCases.value.length > 0 && selectedCases.value.length < tableData.value.length
})

const handleSelectionChange = (selection) => {
  selectedCases.value = selection
}

const handleSelectAll = (val) => {
  if (val) {
    tableRef.value?.toggleAllSelection()
  } else {
    clearSelection()
  }
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
  selectedCases.value = []
}

// 批量执行
const handleBatchExecute = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要执行的用例')
    return false
  }
  const envId = selectedEnvironmentId.value || environments.value.find(e => e.is_default)?.id
  if (!envId) {
    ElMessage.warning('请先选择执行环境')
    return false
  }

  ElMessage.info(`即将执行 ${selectedCases.value.length} 个用例`)
  // TODO: 实现批量执行逻辑
  return true
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的用例')
    return false
  }

  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCases.value.length} 个用例吗？`, '警告', { type: 'warning' })
    for (const caseItem of selectedCases.value) {
      await apiTestCaseApi.deleteCase(caseItem.id)
    }
    ElMessage.success(`成功删除 ${selectedCases.value.length} 个用例`)
    fetchData()
    return true
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
    return false
  }
}

// 批量操作处理
const handleBatchAction = async (action) => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择用例后再进行批量操作')
    return
  }

  const handlers = {
    execute: handleBatchExecute,
    delete: handleBatchDelete
  }

  const success = await handlers[action]?.()
  if (success) {
    batchMode.value = false
    selectedCases.value = []
    tableRef.value?.clearSelection()
  }
}

// 分页处理
const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchData()
}

// 获取环境列表
const fetchEnvironments = async () => {
  if (!projectId.value) return
  envLoading.value = true
  try {
    const envsRes = await environmentApi.getEnvironments({ project: projectId.value })
    environments.value = envsRes?.results || envsRes || []
    // 设置默认环境
    const defaultEnv = environments.value.find(e => e.is_default)
    if (defaultEnv) {
      selectedEnvironmentId.value = defaultEnv.id
    } else if (environments.value.length > 0) {
      selectedEnvironmentId.value = environments.value[0].id
    }
  } catch {
    // 静默处理，环境列表将在界面显示为空
  } finally {
    envLoading.value = false
  }
}

// 数据获取
const fetchData = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const casesRes = await apiTestCaseApi.getCases({
      project: projectId.value,
      page: currentPage.value,
      page_size: pageSize.value
    })
    caseList.value = casesRes?.results || casesRes || []
    totalCases.value = casesRes?.count || caseList.value.length
  } catch {
    // 静默处理，数据加载失败时显示空列表
  } finally {
    loading.value = false
  }
}

// 事件处理
const handleAddCase = () => {
  editingCase.value = null
  caseForm.value = {
    name: '',
    testpoint: '',
    precondition: '',
    expectation: ''
  }
  caseDialogVisible.value = true
}

const handleEditCase = (row) => {
  editingCase.value = row
  caseForm.value = {
    name: row.name,
    testpoint: row.testpoint,
    precondition: row.precondition,
    expectation: row.expectation
  }
  caseDialogVisible.value = true
}

const handleSaveCase = async () => {
  if (!caseForm.value.name || !caseForm.value.testpoint || !caseForm.value.expectation) {
    ElMessage.warning('请填写必填项')
    return
  }

  try {
    const data = {
      ...caseForm.value,
      project: projectId.value
    }

    if (editingCase.value?.id) {
      await apiTestCaseApi.updateCase(editingCase.value.id, data)
      const index = caseList.value.findIndex(c => c.id === editingCase.value.id)
      if (index !== -1) {
        caseList.value[index] = { ...caseList.value[index], ...data }
      }
      ElMessage.success('更新成功')
    } else {
      const res = await apiTestCaseApi.createCase(data)
      caseList.value.unshift(res?.data || res)
      ElMessage.success('创建成功')
    }
    caseDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

const handleDeleteCase = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    await apiTestCaseApi.deleteCase(row.id)
    ElMessage.success('删除成功')
    await fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 操作命令处理
const handleActionCommand = (command, row) => {
  if (command === 'delete') {
    handleDeleteCase(row)
  }
}

// 直接执行测试用例
const handleExecuteCase = (row) => {
  const envId = selectedEnvironmentId.value || environments.value.find(e => e.is_default)?.id
  if (!envId) {
    ElMessage.warning('请先选择执行环境')
    return
  }

  executingCase.value = row
  executeEnvId.value = envId
  executePreview.value = ''
  executeStatus.value = 'idle'
  executeDuration.value = null
  aiKeyDecisions.value = []
  executeSteps.value = []
  thinkingContent.value = ''
  runningStepIndex.value = -1
  executionResults.value = []
  failureAnalysis.value = null
  validating.value = false
  executeDialogVisible.value = true
  executing.value = true

  const startTime = Date.now()

  apiTestCaseApi.executeCaseStream(
    executingCase.value.id,
    envId,
    (event) => {
      if (event.type === 'step') {
        // 更新日志
        const message = event.data?.message || ''
        executePreview.value += `▶ ${message}\n`
        // 流式内容直接追加到思考卡片
        thinkingContent.value += message + '\n'
        // 添加正在执行的步骤到步骤列表
        if (message.includes('正在执行')) {
          const match = message.match(/\[(\d+)\]/)
          const stepIdx = match ? parseInt(match[1]) - 1 : executeSteps.value.length
          // 添加一个 running 状态的步骤
          executeSteps.value.push({
            type: 'running',
            text: message.replace('正在执行', '').trim(),
            summary: '执行中...',
            detail: null
          })
          runningStepIndex.value = executeSteps.value.length - 1
        }
      } else if (event.type === 'dependency') {
        const runList = event.data?.run_list || []
        executePreview.value += `\n📋 依赖分析完成，共 ${runList.length} 个接口待执行\n\n`
        // 依赖分析步骤
        executeSteps.value.push({
          type: 'success',
          text: '依赖分析完成',
          summary: `发现 ${runList.length} 个接口需要执行`,
          detail: runList.length > 0 ? `接口列表:\n${runList.map((r, i) => `${i + 1}. ${r.api_name || r.name || '未知接口'}`).join('\n')}` : null
        })
        aiKeyDecisions.value.push({ type: 'info', text: `发现 ${runList.length} 个依赖接口` })
      } else if (event.type === 'result') {
        const data = event.data || {}
        const icon = data.success ? '✓' : '✗'
        executePreview.value += `  ${icon} ${data.api_name || '接口'}\n`

        // 收集执行结果用于后续校验
        executionResults.value.push(data)

        // 构建详细的步骤信息
        const stepInfo = {
          type: data.success ? 'success' : 'warning',
          text: data.api_name || '接口调用',
          summary: `${data.method || 'GET'} ${data.status_code ? `→ ${data.status_code}` : ''} ${data.duration_ms ? `(${data.duration_ms}ms)` : ''}`,
          detail: null
        }

        // 构建详情
        const details = []
        if (data.method && data.url) {
          details.push(`请求: ${data.method} ${data.url}`)
        }
        if (data.request) {
          try {
            const reqData = typeof data.request === 'string' ? JSON.parse(data.request) : data.request
            if (Object.keys(reqData).length > 0) {
              details.push(`参数: ${JSON.stringify(reqData, null, 2)}`)
            }
          } catch {
            if (data.request) details.push(`参数: ${data.request}`)
          }
        }
        if (data.response) {
          try {
            const respData = typeof data.response === 'string' ? JSON.parse(data.response) : data.response
            details.push(`响应: ${JSON.stringify(respData, null, 2)}`)
          } catch {
            if (data.response) details.push(`响应: ${data.response}`)
          }
        }
        if (!data.success && data.error) {
          details.push(`错误: ${data.error}`)
          executePreview.value += `    错误: ${data.error}\n`
        }

        stepInfo.detail = details.length > 0 ? details.join('\n') : null

        // 替换正在执行的步骤，或者添加新步骤
        if (runningStepIndex.value >= 0 && runningStepIndex.value < executeSteps.value.length) {
          executeSteps.value[runningStepIndex.value] = stepInfo
          runningStepIndex.value = -1
        } else {
          executeSteps.value.push(stepInfo)
        }
      } else if (event.type === 'report') {
        executeDuration.value = Date.now() - startTime
        const report = event.data || {}
        // 根据执行结果判断是否通过：success === total 表示全部通过
        const isPassed = report.success === report.total && report.total > 0
        executeStatus.value = isPassed ? 'pass' : 'fail'
        executePreview.value += `\n━━━━━━━━━━━━━━━━━━━━━━\n`
        executePreview.value += `执行完成，总耗时: ${executeDuration.value}ms\n`
        executePreview.value += `成功: ${report.success || 0}/${report.total || 0}\n`

        ElMessage.success('执行完成')
        executing.value = false
        fetchData()

        // 执行失败时自动调用校验接口获取失败分析
        if (!isPassed && executionResults.value.length > 0) {
          callValidateForAnalysis()
        }
      } else if (event.type === 'error') {
        executeStatus.value = 'error'
        executePreview.value += `\n❌ 错误: ${event.data?.message || '执行失败'}\n`
        aiKeyDecisions.value.push({ type: 'warning', text: event.data?.message || '执行失败' })
        executeSteps.value.push({
          type: 'warning',
          text: '执行失败',
          summary: event.data?.message || '发生错误',
          detail: event.data?.detail || null
        })
        ElMessage.error(event.data?.message || '执行失败')
        executing.value = false
      } else if (event.type === 'chunk') {
        const content = event.data?.content || ''
        if (content) {
          executeStatus.value = 'running'
          // 流式内容直接追加到思考卡片
          thinkingContent.value += content
        }
      }
    },
    (error) => {
      executeStatus.value = 'error'
      executePreview.value += `\n❌ 执行失败: ${error.message}\n`
      aiKeyDecisions.value.push({ type: 'warning', text: error.message })
      executeSteps.value.push({
        type: 'warning',
        text: '执行失败',
        summary: error.message,
        detail: null
      })
      ElMessage.error('执行失败: ' + error.message)
      executing.value = false
    },
    () => {
      if (executing.value) {
        executing.value = false
        fetchData()
      }
    }
  )
}

// 调用校验接口获取失败分析
const callValidateForAnalysis = () => {
  if (!executingCase.value || executionResults.value.length === 0) return

  validating.value = true

  apiTestCaseApi.validateCaseStream(
    executingCase.value.id,
    executionResults.value,
    (event) => {
      if (event.type === 'chunk') {
        thinkingContent.value += event.data?.content || ''
      } else if (event.type === 'result') {
        // 解析校验结果，提取 failure_analysis
        const result = event.data || {}
        if (result.failure_analysis) {
          failureAnalysis.value = result.failure_analysis
          executePreview.value += `\n📌 失败原因: ${result.failure_analysis.root_cause}\n`
        }
        validating.value = false
      } else if (event.type === 'error') {
        validating.value = false
      }
    },
    (error) => {
      validating.value = false
    },
    () => {
      validating.value = false
    }
  )
}

// AI生成
const handleAIGenerate = () => {
  if (!projectKnowledgeBase.value) {
    ElMessage.warning('当前项目未关联知识库')
    return
  }
  aiGenerateDialogVisible.value = true
}

const handleGenerated = () => {
  fetchData()
}

// 环境管理
const handleGoEnvironments = () => {
  const projectCode = projectStore.currentProject?.code || projectId.value
  router.push(`/p/${projectCode}/apitest/environments`)
}

// 打开新建环境对话框
const handleAddEnv = () => {
  envForm.value = {
    name: '',
    env_type: 'test',
    base_url: '',
    description: ''
  }
  envDialogVisible.value = true
}

// 保存环境
const handleSaveEnv = async () => {
  try {
    await envFormRef.value.validate()
    envSubmitting.value = true

    const data = {
      ...envForm.value,
      project: projectCode.value
    }

    await environmentApi.createEnvironment(data)
    ElMessage.success('创建成功')

    envDialogVisible.value = false
    fetchEnvironments()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(error.message || '保存失败')
    }
  } finally {
    envSubmitting.value = false
  }
}

// 监听项目变化
watch(projectId, (newId) => {
  if (newId) {
    fetchEnvironments()
    fetchData()
  }
}, { immediate: true })
</script>

<style scoped>
.apitest-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.apitest-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-secondary);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-section {
  flex: 1;
  background: #fff;
  margin: 16px;
  margin-bottom: 0;
  border-radius: 4px;
  overflow: hidden;
}

.table-section :deep(.el-table) {
  --el-table-border-color: var(--color-border-secondary);
  --el-table-header-bg-color: var(--color-bg-secondary);
}

.table-section :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.table-section :deep(.el-table__row) {
  font-size: 13px;
}

.table-section :deep(.el-table .cell) {
  padding: 0 12px;
}

.table-section :deep(.el-table__row td) {
  border-bottom: 1px solid var(--color-border-secondary);
  padding: 10px 0;
}

.table-section :deep(.el-table__row:hover td) {
  background-color: var(--color-bg-secondary);
}

.table-section :deep(.el-table__empty-block) {
  min-height: 300px;
}

.case-title {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-text {
  color: var(--color-text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
}

.status-badge.none {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
}

.status-badge.running {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.status-badge.pass {
  background: var(--color-success-light);
  color: var(--color-success);
}

.status-badge.fail {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.status-badge.error {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.status-badge.cancelled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
}

.action-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
}

.action-btn.execute:hover {
  background: var(--color-success-light);
  color: var(--color-success);
}

.action-btn.edit:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.action-btn.more:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.delete-text {
  color: var(--color-danger);
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

.pagination-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  margin: 0 16px 16px;
  border-radius: 0 0 4px 4px;
}

.pagination-info {
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
