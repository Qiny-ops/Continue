<template>
  <el-dialog
    :model-value="visible"
    title="AI 生成测试用例"
    width="960px"
    :close-on-click-modal="!generating"
    :close-on-press-escape="!generating"
    class="ai-generate-dialog"
    @update:model-value="handleVisibleUpdate"
  >
    <div class="dialog-content">
      <!-- 步骤 1: 选择知识库和文件 -->
      <div v-if="step === 1" class="form-main">
        <!-- 上次生成结果提示 -->
        <div v-if="hasPreviousResult" class="previous-result-bar">
          <div class="previous-info">
            <el-icon><Clock /></el-icon>
            <span>上次生成：<strong>{{ previousResultSummary }}</strong></span>
          </div>
          <el-button type="primary" size="small" plain @click="viewPreviousResult">
            查看详情
          </el-button>
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>项目知识库</span>
            <span class="required">*</span>
          </div>
          <div v-if="kbLoading" class="kb-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="projectKnowledgeBase" class="kb-info">
            <el-icon><FolderOpened /></el-icon>
            <span class="kb-name">{{ projectKnowledgeBase.name }}</span>
            <el-tag type="success" size="small">已关联</el-tag>
          </div>
          <div v-else class="kb-empty">
            <el-icon><WarningFilled /></el-icon>
            <span>当前项目未关联知识库</span>
            <el-button type="primary" size="small" link @click="handleGoToKnowledge">
              前往设置
            </el-button>
          </div>
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>需求文档</span>
            <span class="required">*</span>
          </div>
          <el-select
            v-model="selectedFiles"
            multiple
            placeholder="请选择需求文档"
            :loading="fileLoading"
            :disabled="!projectKnowledgeBase"
            size="large"
            style="width: 100%"
          >
            <el-option
              v-for="file in files"
              :key="file.id"
              :label="file.title || file.name"
              :value="file.id"
            />
          </el-select>
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>目标版本</span>
            <span class="required">*</span>
          </div>
          <el-select
            v-model="targetVersion"
            placeholder="请选择版本"
            size="large"
            style="width: 100%"
          >
            <el-option
              v-for="v in versions"
              :key="v.id"
              :label="v.name"
              :value="v.id"
            >
              <span>{{ v.name }}</span>
              <el-tag v-if="v.is_default" type="success" size="small" style="margin-left: 8px;">默认</el-tag>
            </el-option>
          </el-select>
        </div>

        <div v-if="aiStatus" class="ai-status-bar">
          <span class="status-label">AI 服务状态：</span>
          <el-tag :type="aiStatus.healthy ? 'success' : 'danger'" size="small">
            {{ aiStatus.healthy ? '正常' : '异常' }}
          </el-tag>
        </div>
      </div>

      <!-- 步骤 2: 生成过程 -->
      <div v-else-if="step === 2" class="process-content">
        <div class="process-log" ref="chatMessagesRef">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="log-item"
            :class="msg.type"
          >
            <!-- 系统消息（进度、状态） -->
            <template v-if="msg.type === 'system'">
              <div class="log-header">
                <div class="log-icon" :class="msg.status">
                  <el-icon v-if="msg.status === 'loading'" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else-if="msg.status === 'success'"><CircleCheck /></el-icon>
                  <el-icon v-else-if="msg.status === 'error'"><CircleClose /></el-icon>
                  <el-icon v-else><InfoFilled /></el-icon>
                </div>
                <span class="log-text" :class="{ clickable: canExpandDetail(msg) && msg.status === 'success' }" @click="toggleDetail(msg)">
                  {{ msg.content }}
                </span>
                <span v-if="msg.elapsed" class="log-elapsed">{{ msg.elapsed.toFixed(1) }}s</span>
                <el-icon v-if="canExpandDetail(msg) && msg.status === 'success'" class="expand-icon" @click="toggleDetail(msg)">
                  <CaretRight v-if="!msg.showDetail" /><CaretBottom v-else />
                </el-icon>
              </div>
              <!-- 功能点详情 -->
              <div v-if="msg.data?.requirements?.length && msg.showDetail" class="log-detail">
                <div class="detail-list">
                  <div v-for="(r, rIdx) in msg.data.requirements" :key="rIdx" class="detail-row">
                    <span class="module-tag">{{ r.module }}</span>
                    <span class="func-text">{{ r.func_point }}</span>
                  </div>
                </div>
              </div>
              <!-- 检索详情 -->
              <div v-else-if="msg.data?.retrieve_details?.length && msg.showDetail" class="log-detail">
                <div class="detail-summary">
                  共 {{ msg.data.total }} 个功能点，{{ msg.data.has_related }} 个有关联内容
                </div>
                <div class="detail-list">
                  <div v-for="(r, rIdx) in msg.data.retrieve_details" :key="rIdx">
                    <div class="detail-row clickable" @click="r.showContent = !r.showContent">
                      <span class="status-dot" :class="{ active: r.has_related }"></span>
                      <span class="module-tag">{{ r.module }}</span>
                      <span class="func-text">{{ r.func_point }}</span>
                      <span v-if="r.chunks_count" class="chunks-badge">{{ r.chunks_count }} 条</span>
                      <el-icon v-if="r.has_related" class="row-expand-icon">
                        <CaretRight v-if="!r.showContent" /><CaretBottom v-else />
                      </el-icon>
                    </div>
                    <div v-if="r.showContent && r.related_chunks?.length" class="chunk-list">
                      <div v-for="(chunk, cIdx) in r.related_chunks" :key="cIdx" class="chunk-item">
                        <div class="chunk-header">
                          <span class="chunk-title">{{ chunk.knowledge_title || '文档' }}</span>
                          <span class="chunk-score">相关度 {{ (chunk.score * 100).toFixed(0) }}%</span>
                        </div>
                        <div class="chunk-content">{{ chunk.content }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- AI 请求日志 -->
            <template v-else-if="msg.type === 'request'">
              <div class="request-header" :class="{ clickable: msg.status !== 'sending' }" @click="msg.status !== 'sending' && (msg.showDetail = !msg.showDetail)">
                <div class="request-left">
                  <span class="request-badge" :class="msg.status">
                    {{ msg.status === 'sending' ? '生成中' : msg.status === 'success' ? '成功' : '失败' }}
                  </span>
                  <span class="request-index">[{{ msg.index }}/{{ msg.total }}]</span>
                  <span class="request-info">{{ msg.module }} - {{ msg.func_point }}</span>
                  <el-icon v-if="msg.status !== 'sending'" class="expand-icon">
                    <CaretRight v-if="!msg.showDetail" /><CaretBottom v-else />
                  </el-icon>
                </div>
                <div class="request-right">
                  <span v-if="msg.elapsed" class="elapsed-time">{{ msg.elapsed.toFixed(1) }}s</span>
                </div>
              </div>
              <div v-if="msg.showDetail" class="request-body">
                <!-- 流式生成内容 -->
                <div v-if="msg.streamingContent" class="streaming-box">
                  <div class="streaming-label">
                    <el-icon class="is-loading"><Loading /></el-icon>
                    <span>AI 正在生成...</span>
                  </div>
                  <div class="streaming-text">{{ msg.streamingContent }}</div>
                </div>
                <!-- 成功结果 -->
                <div v-if="msg.status === 'success' && msg.cases?.length" class="result-cases">
                  <div class="result-header clickable" @click.stop="msg.showCases = !msg.showCases">
                    <el-icon><CaretRight v-if="!msg.showCases" /><CaretBottom v-else /></el-icon>
                    <span class="result-label">生成用例 ({{ msg.cases.length }} 条)</span>
                  </div>
                  <div v-if="msg.showCases" class="case-list">
                    <div v-for="c in msg.cases" :key="c.id" class="case-row">
                      <span class="case-id">{{ c.id }}</span>
                      <span class="case-title">{{ c.title }}</span>
                      <el-tag :type="getPriorityType(c.priority)" size="small">{{ c.priority }}</el-tag>
                    </div>
                  </div>
                </div>
                <!-- 错误信息 -->
                <div v-else-if="msg.status === 'error'" class="error-text">
                  <el-icon><WarningFilled /></el-icon>
                  {{ msg.error || '生成失败' }}
                </div>
                <!-- Thinking -->
                <div v-if="msg.thinking" class="thinking-box">
                  <div class="thinking-header" @click.stop="msg.showThinking = !msg.showThinking">
                    <el-icon><CaretRight v-if="!msg.showThinking" /><CaretBottom v-else /></el-icon>
                    <span v-if="msg.status === 'sending'" class="thinking-label-streaming">
                      <span class="thinking-indicator">
                        <span class="indicator-dot"></span>
                        <span class="indicator-ring"></span>
                      </span>
                      AI 思考中...
                    </span>
                    <span v-else>AI 思考过程</span>
                    <span class="thinking-count">{{ msg.thinking.length }} 字符</span>
                  </div>
                  <div v-if="msg.showThinking" class="thinking-content">
                    {{ msg.thinking }}<span v-if="msg.status === 'sending'" class="thinking-cursor"></span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- 完成统计 -->
          <div v-if="completed && finalResult.created_count !== undefined" class="complete-summary">
            <div class="summary-row">
              <div class="summary-item">
                <span class="summary-value success">{{ finalResult.created_count || 0 }}</span>
                <span class="summary-label">成功生成</span>
              </div>
              <div class="summary-item">
                <span class="summary-value error">{{ finalResult.error_count || 0 }}</span>
                <span class="summary-label">生成失败</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ finalResult.total_requests || 0 }}</span>
                <span class="summary-label">总请求数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ finalResult.total_elapsed?.toFixed(1) || 0 }}s</span>
                <span class="summary-label">总耗时</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <span v-if="step === 2 && generating" class="generating-hint">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在生成中...
          </span>
          <span v-else-if="completed" class="complete-hint">
            <el-icon><CircleCheck /></el-icon>
            生成完成
          </span>
        </div>
        <div class="footer-right">
          <el-button v-if="step === 1" size="large" @click="handleClose">取消</el-button>
          <el-button
            v-if="step === 1"
            type="primary"
            size="large"
            :disabled="!canGenerate"
            :loading="generating"
            @click="handleGenerate"
          >
            开始生成
          </el-button>
          <el-button v-if="step === 2 && generating" size="large" :disabled="generating" @click="handleCancel">
            取消生成
          </el-button>
          <el-button v-if="step === 2 && completed" size="large" @click="handleRegenerate">
            重新生成
          </el-button>
          <el-button v-if="step === 2 && completed" type="primary" size="large" @click="handleClose">
            完成
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import {
  CircleCheck, CircleClose, Loading, FolderOpened, WarningFilled,
  InfoFilled, CaretRight, CaretBottom, Clock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listKnowledge } from '@/api/modules/knowledge'
import { getProjectKnowledgeBase } from '@/api/modules/projectKnowledgeBase'
import { aiApi } from '@/api/modules/testcase'
import { useMessageQueue } from '@/composables/testcase/useMessageQueue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  versionId: { type: [String, Number], default: null },
  defaultVersionId: { type: [String, Number], default: null },
  versions: { type: Array, default: () => [] },
  projectId: { type: [String, Number], default: null }
})

const emit = defineEmits(['update:visible', 'generated', 'goToKnowledge'])

const step = ref(1)
const generating = ref(false)
const completed = ref(false)
const kbLoading = ref(false)
const fileLoading = ref(false)

const projectKnowledgeBase = ref(null)
const files = ref([])
const selectedFiles = ref([])
const targetVersion = ref(null)
const aiStatus = ref(null)

const messages = ref([])
const chatMessagesRef = ref(null)

const successCount = ref(0)
const errorCount = ref(0)
const totalRequests = ref(0)

const finalResult = ref({})
const currentTaskId = ref(null)  // 当前任务ID，用于取消
const currentAbortController = ref(null)  // 当前 SSE 请求的 AbortController

// 保存上次生成结果（关闭弹框时保留）
const savedResult = ref(null)
const savedMessages = ref([])

// 是否有上次结果
const hasPreviousResult = computed(() => {
  return savedResult.value && savedResult.value.created_count !== undefined
})

// 上次结果摘要
const previousResultSummary = computed(() => {
  if (!savedResult.value) return ''
  const r = savedResult.value
  return `成功 ${r.created_count || 0} 条，失败 ${r.error_count || 0} 条`
})

const canGenerate = computed(() => {
  return projectKnowledgeBase.value &&
    selectedFiles.value.length > 0 &&
    targetVersion.value
})

const getPriorityType = (priority) => {
  const map = { p0: 'danger', p1: 'warning', p2: 'primary', p3: 'info' }
  return map[priority] || 'info'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

const { add: addMessage, update: updateMessage } = useMessageQueue(messages, scrollToBottom)

const toggleDetail = (msg) => {
  if (canExpandDetail(msg) && msg.status === 'success') {
    msg.showDetail = !msg.showDetail
    // 展开详情时不自动滚动，保持用户当前查看位置
  }
}

const canExpandDetail = (msg) => {
  return msg.data?.requirements?.length || msg.data?.retrieve_details?.length
}

const fetchProjectKnowledgeBase = async () => {
  if (!props.projectId) return
  kbLoading.value = true
  try {
    const res = await getProjectKnowledgeBase(props.projectId)
    projectKnowledgeBase.value = res?.data || null
    if (projectKnowledgeBase.value?.id) {
      await fetchFiles(projectKnowledgeBase.value.id)
    }
  } catch {
    projectKnowledgeBase.value = null
  } finally {
    kbLoading.value = false
  }
}

const fetchFiles = async (kbId) => {
  if (!kbId) return
  fileLoading.value = true
  try {
    const res = await listKnowledge(kbId)
    const data = res?.data || res
    const list = data?.results || data?.list || data || []
    files.value = Array.isArray(list) ? list : (list.list || [])
  } catch {
    ElMessage.error('获取文件列表失败')
  } finally {
    fileLoading.value = false
  }
}

const checkAIStatus = async () => {
  try {
    const res = await aiApi.getAIStatus()
    aiStatus.value = res
  } catch {
    aiStatus.value = { healthy: false }
  }
}

const handleGenerate = async () => {
  if (!canGenerate.value) {
    ElMessage.warning('请选择需求文档和目标版本')
    return
  }

  step.value = 2
  generating.value = true
  completed.value = false
  messages.value = []
  successCount.value = 0
  errorCount.value = 0
  totalRequests.value = 0

  const abortController = aiApi.generateTestCasesStream(
    {
      knowledge_base_ids: [projectKnowledgeBase.value.id],
      knowledge_ids: selectedFiles.value,
      version_id: targetVersion.value
    },
    {
      onStarted: (data) => {
        // 保存task_id用于取消
        currentTaskId.value = data.task_id
      },
      onProgress: (data) => {
        const statusMap = {
          'start': 'loading',
          'processing': 'loading',
          'preparing': 'loading',
          'complete': 'success',
          'error': 'error'
        }

        const newStatus = statusMap[data.status] || 'loading'

        if (data.status === 'complete' || data.status === 'error') {
          const existingIndex = messages.value.findIndex(
            m => m.type === 'system' && m.step === data.step
          )
          if (existingIndex !== -1) {
            messages.value[existingIndex] = {
              ...messages.value[existingIndex],
              status: newStatus,
              content: data.message,
              data: data.data,
              elapsed: data.elapsed,
              showDetail: false
            }
            return
          }
        }

        addMessage({
          type: 'system',
          step: data.step,
          status: newStatus,
          content: data.message,
          data: data.data,
          elapsed: data.elapsed,
          showDetail: false
        })

        if (data.data?.total_requests) {
          totalRequests.value = data.data.total_requests
        }
      },
      onRequest: (data) => {
        if (data.status === 'sending') {
          addMessage({
            type: 'request',
            index: data.index,
            total: data.total,
            status: 'sending',
            module: data.module,
            func_point: data.func_point,
            thinking: null,
            streamingContent: '',
            showDetail: false,
            showThinking: false,
            elapsed: null
          })
        } else {
          updateMessage(
            m => m.type === 'request' && m.index === data.index,
            (existing) => ({
              status: data.status,
              cases: data.cases,
              cases_count: data.cases_count,
              error: data.error,
              // 优先使用流式累积的 thinking，若无则使用 request 事件中的 thinking
              thinking: existing?.thinking || data.thinking || null,
              // 若已有流式 thinking，保持展开状态
              showThinking: existing?.thinking ? existing.showThinking : false,
              showCases: false,
              elapsed: data.elapsed
            })
          )

          if (data.status === 'success') {
            successCount.value += data.cases_count || 0
          } else if (data.status === 'error') {
            errorCount.value += 1
          }
        }
      },
      onChunk: (data) => {
        updateMessage(
          m => m.type === 'request' && m.index === data.index,
          (existing) => ({
            streamingContent: (existing.streamingContent || '') + data.chunk,
            chunkCount: data.chunk_count
          })
        )
      },
      onThinkingChunk: (data) => {
        updateMessage(
          m => m.type === 'request' && m.index === data.index,
          (existing) => ({
            thinking: (existing.thinking || '') + data.chunk,
            showThinking: true,
            showDetail: true
          })
        )
      },
      onComplete: (data) => {
        generating.value = false
        completed.value = true
        finalResult.value = data

        if (data.created_count > 0) {
          ElMessage.success(`成功生成 ${data.created_count} 条测试用例`)
          emit('generated', data)
        }
      },
      onError: (data) => {
        generating.value = false

        addMessage({
          type: 'system',
          status: 'error',
          content: '生成失败',
          detail: data.error || '未知错误'
        })

        ElMessage.error(data.error || '生成失败')
      }
    }
  )

  // 保存 abort 控制器用于取消
  currentAbortController.value = abortController
}

const handleCancel = async () => {
  // 中断前端 SSE 连接
  if (currentAbortController.value) {
    currentAbortController.value.abort()
    currentAbortController.value = null
  }
  // 调用后端取消API
  if (currentTaskId.value) {
    try {
      await aiApi.cancelGeneration(currentTaskId.value)
      ElMessage.info('已发送取消请求')
    } catch {
      // 后端取消失败不影响前端中断
    }
  }
  generating.value = false
  step.value = 1
  currentTaskId.value = null
}

const handleGoToKnowledge = () => {
  emit('update:visible', false)
  emit('goToKnowledge')
}

const handleClose = () => {
  if (generating.value) {
    ElMessage.warning('正在生成中，请稍候...')
    return
  }

  // 如果已完成，保存结果供下次查看
  if (completed.value && finalResult.value.created_count !== undefined) {
    savedResult.value = { ...finalResult.value }
    savedMessages.value = [...messages.value]
  }

  emit('update:visible', false)
}

// 查看上次生成结果
const viewPreviousResult = () => {
  if (savedResult.value && savedMessages.value.length > 0) {
    // 恢复上次的数据
    finalResult.value = { ...savedResult.value }
    messages.value = [...savedMessages.value]
    completed.value = true
    generating.value = false
    step.value = 2
  }
}

const handleRegenerate = () => {
  step.value = 1
  completed.value = false
  generating.value = false
  messages.value = []
  finalResult.value = {}
  successCount.value = 0
  errorCount.value = 0
  totalRequests.value = 0
  // 清空保存的结果
  savedResult.value = null
  savedMessages.value = []
}

const handleVisibleUpdate = (val) => {
  if (generating.value && !val) {
    ElMessage.warning('正在生成中，请稍候...')
    return
  }
  emit('update:visible', val)
}

watch(() => props.visible, (val) => {
  if (val) {
    // 打开弹框时，重置到步骤1（如果有上次结果会显示提示）
    if (!generating.value && !completed.value) {
      step.value = 1
    }
    targetVersion.value = props.defaultVersionId || props.versionId
    fetchProjectKnowledgeBase()
    checkAIStatus()
  }
})
</script>

<style scoped>
.ai-generate-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-bg-tertiary);
  margin-right: 0;
}

.ai-generate-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.ai-generate-dialog :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

.ai-generate-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.ai-generate-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

.dialog-content {
  min-height: 400px;
  max-height: 520px;
}

/* 表单区域 */
.form-main {
  padding: 16px;
  overflow-y: auto;
}

/* 上次结果提示 */
.previous-result-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.08) 0%, rgba(24, 144, 255, 0.08) 100%);
  border: 1px solid rgba(82, 196, 26, 0.2);
  border-radius: 4px;
  margin-bottom: 16px;
}

.previous-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.previous-info .el-icon {
  color: var(--color-success);
}

.previous-info strong {
  color: var(--color-success);
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

.form-label .required {
  color: var(--color-danger);
}

.kb-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.kb-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.kb-info .el-icon {
  color: var(--color-warning);
  font-size: 18px;
}

.kb-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.kb-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 77, 79, 0.05);
  border: 1px solid rgba(255, 77, 79, 0.2);
  border-radius: 2px;
  color: var(--color-danger);
  font-size: 13px;
}

.ai-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  margin-top: 8px;
}

.status-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 生成过程 */
.process-content {
  height: 480px;
  display: flex;
  flex-direction: column;
}

.process-log {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-item {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 系统消息 */
.log-item.system {
  background: var(--color-bg-secondary);
  border-radius: 2px;
  padding: 10px 12px;
  border-left: 3px solid var(--color-primary);
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
}

.log-icon.loading {
  color: var(--color-primary);
}

.log-icon.success {
  color: var(--color-success);
}

.log-icon.error {
  color: var(--color-danger);
}

.log-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.log-text.clickable {
  cursor: pointer;
  color: var(--color-primary);
}

.log-text.clickable:hover {
  text-decoration: underline;
}

.log-elapsed {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  padding: 2px 8px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  margin-left: auto;
}

.expand-icon {
  font-size: 14px;
  color: var(--color-primary);
  cursor: pointer;
}

/* 详情展开 */
.log-detail {
  margin-top: 10px;
  padding: 10px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

.detail-summary {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.detail-list {
  max-height: 200px;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--color-border-secondary);
  font-size: 12px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row.clickable {
  cursor: pointer;
}

.detail-row.clickable:hover {
  background: var(--color-bg-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-tertiary);
  flex-shrink: 0;
}

.status-dot.active {
  background: var(--color-success);
}

.module-tag {
  flex-shrink: 0;
  padding: 2px 6px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 2px;
  font-size: 11px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.func-text {
  flex: 1;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chunks-badge {
  font-size: 11px;
  color: var(--color-success);
  background: rgba(82, 196, 26, 0.1);
  padding: 2px 6px;
  border-radius: 2px;
}

.row-expand-icon {
  font-size: 12px;
  color: var(--color-primary);
}

/* Chunk 列表 */
.chunk-list {
  margin: 8px 0 8px 16px;
  padding: 8px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  border-left: 2px solid var(--color-primary);
}

.chunk-item {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--color-border-secondary);
}

.chunk-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.chunk-title {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-primary);
}

.chunk-score {
  font-size: 10px;
  color: var(--color-text-tertiary);
}

.chunk-content {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
}

/* 请求日志 */
.log-item.request {
  background: #fff;
  border: 1px solid var(--color-border-secondary);
  border-radius: 2px;
}

.log-item.request.sending {
  border-color: var(--color-primary);
}

.log-item.request.success {
  border-color: var(--color-success);
}

.log-item.request.error {
  border-color: var(--color-danger);
}

.request-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-secondary);
}

.request-header.clickable {
  cursor: pointer;
}

.request-header.clickable:hover {
  background: var(--color-bg-tertiary);
}

.request-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.request-left .expand-icon {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.request-right {
  display: flex;
  align-items: center;
}

.request-badge {
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
}

.request-badge.sending {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.request-badge.success {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.request-badge.error {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

.request-index {
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.request-info {
  font-size: 12px;
  color: var(--color-text-secondary);
  max-width: 380px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.elapsed-time {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  padding: 2px 8px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

.request-body {
  padding: 10px 12px;
}

/* 流式生成 */
.streaming-box {
  margin-top: 8px;
  padding: 10px;
  background: rgba(24, 144, 255, 0.05);
  border-radius: 2px;
  border-left: 2px solid var(--color-primary);
}

.streaming-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-primary);
  margin-bottom: 6px;
}

.streaming-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 160px;
  overflow-y: auto;
  font-family: monospace;
}

/* 结果用例 */
.result-cases {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border-secondary);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-header.clickable {
  cursor: pointer;
  padding: 6px 8px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

.result-header.clickable:hover {
  background: var(--color-bg-secondary);
}

.result-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.case-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.case-id {
  font-size: 11px;
  color: var(--color-text-tertiary);
  font-family: monospace;
  min-width: 40px;
}

.case-title {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-text {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-danger);
  font-size: 12px;
}

/* Thinking */
.thinking-box {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border-secondary);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 6px 8px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

.thinking-header:hover {
  background: var(--color-bg-secondary);
}

.thinking-count {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.thinking-content {
  margin-top: 8px;
  padding: 10px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.thinking-label-streaming {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-primary);
}

.thinking-indicator {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
}

.thinking-indicator .indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

.thinking-indicator .indicator-ring {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--color-primary);
  opacity: 0;
  animation: thinking-ring 1.5s ease-out infinite;
}

@keyframes thinking-ring {
  0% { transform: scale(0.5); opacity: 0.8; }
  100% { transform: scale(1.2); opacity: 0; }
}

.thinking-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: var(--color-primary);
  margin-left: 1px;
  vertical-align: text-bottom;
  animation: thinking-blink 0.8s step-end infinite;
}

@keyframes thinking-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 完成统计 */
.complete-summary {
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  border-left: 3px solid var(--color-success);
}

.summary-row {
  display: flex;
  justify-content: space-around;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.summary-value.success {
  color: var(--color-success);
}

.summary-value.error {
  color: var(--color-danger);
}

.summary-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* Footer */
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

.generating-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.complete-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-success);
}

.footer-right {
  display: flex;
  gap: 8px;
}
</style>
