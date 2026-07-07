<template>
  <div class="execution-panel">
    <!-- 顶部操作栏 -->
    <div class="execution-header">
      <el-button type="primary" @click="showExecuteDialog">
        <el-icon><VideoPlay /></el-icon>
        执行用例
      </el-button>
    </div>

    <!-- 内容区域 -->
    <div class="execution-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
      </div>

      <!-- 空状态 -->
      <div v-else-if="executions.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="40" r="36" stroke="currentColor" stroke-width="2" stroke-dasharray="4 3" />
            <path d="M32 30l20 10-20 10V30z" fill="currentColor" opacity="0.3" />
          </svg>
        </div>
        <h3>暂无执行记录</h3>
        <p>点击上方按钮开始执行测试用例</p>
      </div>

      <!-- 执行历史列表 -->
      <div v-else class="execution-list">
        <div v-for="item in executions" :key="item.id" class="execution-item">
          <div class="execution-result" :class="item.result">
            <el-icon v-if="item.result === 'pass'"><CircleCheck /></el-icon>
            <el-icon v-else-if="item.result === 'fail'"><CircleClose /></el-icon>
            <el-icon v-else-if="item.result === 'block'"><Warning /></el-icon>
            <el-icon v-else><Remove /></el-icon>
          </div>
          <div class="execution-info">
            <div class="execution-header-row">
              <span class="result-text" :class="item.result">{{ getResultText(item.result) }}</span>
              <span class="execution-time">{{ formatDate(item.executed_at) }}</span>
            </div>
            <div class="execution-meta">
              <span class="executor">
                <el-icon><User /></el-icon>
                {{ item.executed_by_name || '未知' }}
              </span>
            </div>
            <div v-if="item.actual_result" class="actual-result">
              实际结果：{{ item.actual_result }}
            </div>
            <div v-if="item.remark" class="remark">
              备注：{{ item.remark }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchExecutions"
      />
    </div>

    <!-- 执行对话框 -->
    <el-dialog v-model="executeDialogVisible" title="执行测试用例" width="500px">
      <div class="execute-form">
        <div class="form-item">
          <label><span class="required">*</span>执行结果</label>
          <el-radio-group v-model="executeForm.result">
            <el-radio value="pass">
              <span class="result-option pass">通过</span>
            </el-radio>
            <el-radio value="fail">
              <span class="result-option fail">失败</span>
            </el-radio>
            <el-radio value="block">
              <span class="result-option block">阻塞</span>
            </el-radio>
            <el-radio value="skip">
              <span class="result-option skip">跳过</span>
            </el-radio>
          </el-radio-group>
        </div>

        <div class="form-item">
          <label>实际结果</label>
          <el-input
            v-model="executeForm.actual_result"
            type="textarea"
            :rows="3"
            placeholder="请输入实际执行结果（可选）"
          />
        </div>

        <div class="form-item">
          <label>备注</label>
          <el-input
            v-model="executeForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息（可选）"
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitExecution">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, CircleCheck, CircleClose, Warning, Remove, User } from '@element-plus/icons-vue'
import { executionApi } from '@/api/modules/testcase'

const props = defineProps({
  testCaseId: { type: [String, Number], default: null },
  projectId: { type: [String, Number], default: null }
})

const emit = defineEmits(['executed'])

const loading = ref(false)
const submitting = ref(false)
const executions = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const executeDialogVisible = ref(false)

const executeForm = reactive({
  result: 'pass',
  actual_result: '',
  remark: ''
})

const RESULT_TEXT = {
  pass: '通过',
  fail: '失败',
  block: '阻塞',
  skip: '跳过'
}

const getResultText = (r) => RESULT_TEXT[r] || r

const formatDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fetchExecutions = async () => {
  if (!props.testCaseId) {
    executions.value = []
    return
  }

  loading.value = true
  try {
    const res = await executionApi.getExecutions({
      test_case: props.testCaseId,
      page: currentPage.value,
      page_size: pageSize.value
    })
    executions.value = res?.results || res || []
    total.value = res?.count || executions.value.length
  } catch (e) {

  } finally {
    loading.value = false
  }
}

const showExecuteDialog = () => {
  executeForm.result = 'pass'
  executeForm.actual_result = ''
  executeForm.remark = ''
  executeDialogVisible.value = true
}

const submitExecution = async () => {
  if (!props.testCaseId) {
    ElMessage.warning('请先选择测试用例')
    return
  }

  submitting.value = true
  try {
    await executionApi.createExecution({
      test_case: props.testCaseId,
      result: executeForm.result,
      actual_result: executeForm.actual_result,
      remark: executeForm.remark
    })
    ElMessage.success('执行记录已提交')
    executeDialogVisible.value = false
    fetchExecutions()
    emit('executed')
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

watch(() => props.testCaseId, (newId) => {
  if (newId) {
    currentPage.value = 1
    fetchExecutions()
  } else {
    executions.value = []
    total.value = 0
  }
}, { immediate: true })
</script>

<style scoped>
.execution-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.execution-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.execution-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border-primary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--color-primary);
  opacity: 0.5;
  margin-bottom: 16px;
}

.empty-icon svg { width: 100%; height: 100%; }

.empty-state h3 {
  font-size: 16px;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.execution-list { display: flex; flex-direction: column; gap: 12px; }

.execution-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-border-secondary);
  border-radius: 4px;
  transition: all 0.2s;
}

.execution-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.execution-result {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.execution-result.pass { background: #d4edda; color: #155724; }
.execution-result.fail { background: #f8d7da; color: #721c24; }
.execution-result.block { background: #fff3cd; color: #856404; }
.execution-result.skip { background: #e2e8f0; color: #64748b; }

.execution-info { flex: 1; min-width: 0; }

.execution-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.result-text {
  font-size: 14px;
  font-weight: 500;
}

.result-text.pass { color: #155724; }
.result-text.fail { color: #721c24; }
.result-text.block { color: #856404; }
.result-text.skip { color: #64748b; }

.execution-time {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.execution-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.executor {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.actual-result,
.remark {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  padding: 8px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
}

.pagination-bar {
  padding: 12px 20px;
  border-top: 1px solid var(--color-border-secondary);
  text-align: right;
}

/* 执行表单样式 */
.execute-form { padding: 0 4px; }

.execute-form .form-item { margin-bottom: 16px; }

.execute-form label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.execute-form label .required {
  color: var(--color-danger);
  margin-right: 4px;
}

.execute-form .el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.result-option {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
}

.result-option.pass { background: #d4edda; color: #155724; }
.result-option.fail { background: #f8d7da; color: #721c24; }
.result-option.block { background: #fff3cd; color: #856404; }
.result-option.skip { background: #e2e8f0; color: #64748b; }
</style>
