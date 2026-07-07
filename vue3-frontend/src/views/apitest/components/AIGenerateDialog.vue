<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="handleVisibleUpdate"
    :title="dialogTitle"
    width="760px"
    :close-on-click-modal="!generating"
    :close-on-press-escape="!generating"
    :show-close="!generating"
    class="ai-generate-dialog"
    destroy-on-close
  >
    <div class="dialog-body">
      <!-- 步骤 1: 选择知识库文件 -->
      <div v-if="step === 1" class="form-section">
        <div class="form-item">
          <div class="form-label">
            <span>项目知识库</span>
            <span class="required">*</span>
          </div>
          <div v-if="kbLoading" class="kb-status">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="projectKnowledgeBase" class="kb-status linked">
            <el-icon><FolderOpened /></el-icon>
            <span class="kb-name">{{ projectKnowledgeBase.name }}</span>
            <el-tag type="success" size="small">已关联</el-tag>
          </div>
          <div v-else class="kb-status empty">
            <el-icon><WarningFilled /></el-icon>
            <span>当前项目未关联知识库</span>
          </div>
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>需求文档</span>
            <span class="required">*</span>
          </div>
          <el-select
            v-model="selectedFile"
            placeholder="请选择知识库文件"
            :loading="fileLoading"
            :disabled="!projectKnowledgeBase"
            size="large"
            style="width: 100%"
          >
            <el-option
              v-for="file in knowledgeFiles"
              :key="file.id || file.knowledge_id"
              :label="file.title || file.name || file.filename"
              :value="file.id || file.knowledge_id"
            />
          </el-select>
        </div>
      </div>

      <!-- 步骤 2: 生成过程 -->
      <div v-else class="process-section">
        <!-- 思考卡片 -->
        <div v-if="hasThinking" class="think-card">
          <div class="think-header" @click="toggleThinking">
            <div class="think-title">
              <span v-if="generating" class="think-status">
                <span class="think-indicator">
                  <span class="indicator-dot"></span>
                  <span class="indicator-ring"></span>
                </span>
                <span class="think-text">正在生成测试用例...</span>
              </span>
              <span v-else class="think-done">
                <span class="done-icon">✓</span>
                <span class="done-text">已完成用例生成，耗时 {{ stats.elapsed }}</span>
              </span>
            </div>
            <el-icon :size="14" :class="{ rotated: !thinkFold }">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="think-content" v-show="!thinkFold || generating">
            <div class="content-inner" ref="thinkRef">{{ thinkingText }}</div>
          </div>
        </div>

        <!-- 生成结果列表 -->
        <div class="result-list" ref="resultListRef">
          <div
            v-for="(item, idx) in resultItems"
            :key="idx"
            class="result-item"
            :class="item.type"
          >
            <div class="item-header" @click="toggleItem(idx)">
              <div class="item-main">
                <span class="item-icon">
                  <span v-if="item.type === 'generating'" class="mini-spinner"></span>
                  <span v-else-if="item.type === 'success'">✓</span>
                  <span v-else-if="item.type === 'error'">✗</span>
                  <span v-else>●</span>
                </span>
                <span class="item-name">{{ item.name }}</span>
              </div>
              <div class="item-meta">
                <span v-if="item.summary" class="item-summary">{{ item.summary }}</span>
                <el-icon v-if="item.hasDetail" :size="12" :class="{ rotated: item.expanded }">
                  <ArrowDown />
                </el-icon>
              </div>
            </div>
            <div class="item-detail" v-show="item.expanded && item.detail">
              <pre>{{ item.detail }}</pre>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div v-if="generating" class="loading-indicator">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- 完成统计 -->
        <div v-if="!generating && completed && stats.created > 0" class="stats-bar">
          <div class="stat-item">
            <span class="stat-value success">{{ stats.created }}</span>
            <span class="stat-label">成功生成</span>
          </div>
          <div class="stat-item">
            <span class="stat-value error">{{ stats.errors }}</span>
            <span class="stat-label">生成失败</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.elapsed }}</span>
            <span class="stat-label">耗时</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <span v-if="generating" class="footer-hint generating">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在生成中...
          </span>
          <span v-else-if="completed" class="footer-hint done">
            <el-icon><CircleCheck /></el-icon>
            生成完成
          </span>
        </div>
        <div class="footer-actions">
          <template v-if="step === 1">
            <el-button @click="handleClose">取消</el-button>
            <el-button
              type="primary"
              :disabled="!canGenerate"
              @click="handleStartGenerate"
            >
              开始生成
            </el-button>
          </template>
          <template v-else-if="generating">
            <el-button disabled>生成中...</el-button>
          </template>
          <template v-else>
            <el-button @click="handleReset">重新生成</el-button>
            <el-button type="primary" @click="handleClose">完成</el-button>
          </template>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive } from 'vue'
import {
  Loading, CircleCheck, FolderOpened, WarningFilled, ArrowDown
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { listKnowledge } from '@/api/modules/knowledge'
import { apiTestCaseApi } from '@/api/modules/apitest'

const props = defineProps({
  visible: { type: Boolean, default: false },
  projectKnowledgeBase: { type: Object, default: null },
  projectId: { type: [String, Number], default: null }
})

const emit = defineEmits(['update:visible', 'generated'])

const step = ref(1)
const generating = ref(false)
const completed = ref(false)
const kbLoading = ref(false)
const fileLoading = ref(false)
const knowledgeFiles = ref([])
const selectedFile = ref(null)

// 思考/流式内容
const thinkingText = ref('')
const thinkFold = ref(false)
const thinkRef = ref(null)
const resultListRef = ref(null)

// 结果项
const itemStates = reactive({})
const resultItems = ref([])

// 统计
const stats = ref({ created: 0, errors: 0, elapsed: '0s' })

// 计时
const startTime = ref(null)

const hasThinking = computed(() => {
  return thinkingText.value.length > 0 || generating.value
})

const canGenerate = computed(() => {
  return props.projectKnowledgeBase && selectedFile.value
})

const dialogTitle = computed(() => {
  if (generating.value) return 'AI生成中...'
  if (completed.value) return '生成完成'
  return 'AI生成接口测试用例'
})

const toggleThinking = () => {
  if (!generating.value) {
    thinkFold.value = !thinkFold.value
  }
}

const toggleItem = (idx) => {
  itemStates[idx] = !itemStates[idx]
  if (resultItems.value[idx]) {
    resultItems.value[idx].expanded = itemStates[idx]
  }
}

const scrollToBottom = (refEl) => {
  nextTick(() => {
    if (refEl) {
      refEl.scrollTop = refEl.scrollHeight
    }
  })
}

// 获取知识库文件
const fetchFiles = async () => {
  if (!props.projectKnowledgeBase?.id) return
  fileLoading.value = true
  try {
    const res = await listKnowledge(props.projectKnowledgeBase.id, { page_size: 100 })
    knowledgeFiles.value = res?.data || res?.results || res || []
  } catch {
    ElMessage.error('获取知识库文件失败')
  } finally {
    fileLoading.value = false
  }
}

const handleStartGenerate = () => {
  if (!canGenerate.value) return

  step.value = 2
  generating.value = true
  completed.value = false
  thinkingText.value = ''
  resultItems.value = []
  stats.value = { created: 0, errors: 0, elapsed: '0s' }
  thinkFold.value = false
  startTime.value = Date.now()

  apiTestCaseApi.generateFromKbStream(
    props.projectId,
    props.projectKnowledgeBase.id,
    selectedFile.value,
    (event) => {
      if (event.type === 'thinking') {
        const content = event.data?.content || ''
        if (content) {
          thinkingText.value += content
          scrollToBottom(thinkRef.value)
        }
      } else if (event.type === 'chunk') {
        const content = event.data?.content || ''
        if (content) {
          thinkingText.value += content
          scrollToBottom(thinkRef.value)
        }
      } else if (event.type === 'saved') {
        const count = event.data?.count || 0
        stats.value.created = count
        generating.value = false
        completed.value = true

        // 计算耗时
        if (startTime.value) {
          const ms = Date.now() - startTime.value
          stats.value.elapsed = ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
        }

        // 添加完成结果项
        resultItems.value.push({
          type: 'success',
          name: '生成完成',
          summary: `成功生成 ${count} 个测试用例`,
          detail: null,
          hasDetail: false,
          expanded: false
        })

        thinkFold.value = true
        ElMessage.success(`成功生成 ${count} 个测试用例`)
        emit('generated', event.data)
      } else if (event.type === 'error') {
        generating.value = false
        completed.value = true

        if (startTime.value) {
          const ms = Date.now() - startTime.value
          stats.value.elapsed = ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
        }

        resultItems.value.push({
          type: 'error',
          name: '生成失败',
          summary: event.data?.message || '未知错误',
          detail: event.data?.detail || null,
          hasDetail: !!event.data?.detail,
          expanded: false
        })

        ElMessage.error(event.data?.message || '生成失败')
      }
    },
    (error) => {
      generating.value = false
      completed.value = true

      if (startTime.value) {
        const ms = Date.now() - startTime.value
        stats.value.elapsed = ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
      }

      resultItems.value.push({
        type: 'error',
        name: '生成失败',
        summary: error.message,
        detail: null,
        hasDetail: false,
        expanded: false
      })

      ElMessage.error('生成失败: ' + error.message)
    },
    () => {
      if (generating.value) {
        generating.value = false
        completed.value = true

        // 流结束但未收到 saved/error 事件，说明生成或存库失败
        if (stats.value.created === 0) {
          resultItems.value.push({
            type: 'error',
            name: '存库失败',
            summary: 'AI 已返回内容但未能成功写入数据库，请检查后端日志',
            detail: null,
            hasDetail: false,
            expanded: false
          })
          ElMessage.warning('生成完成但未能写入数据库')
        }
      }
    }
  )
}

const handleReset = () => {
  step.value = 1
  completed.value = false
  generating.value = false
  thinkingText.value = ''
  resultItems.value = []
  stats.value = { created: 0, errors: 0, elapsed: '0s' }
}

const handleClose = () => {
  if (generating.value) {
    ElMessage.warning('正在生成中，请稍候...')
    return
  }
  emit('update:visible', false)
}

const handleVisibleUpdate = (val) => {
  if (generating.value && !val) {
    ElMessage.warning('正在生成中，请稍候...')
    return
  }
  emit('update:visible', val)
}

// 打开时加载数据
watch(() => props.visible, (val) => {
  if (val) {
    if (!generating.value && !completed.value) {
      step.value = 1
      selectedFile.value = null
    }
    fetchFiles()
  }
})

// 自动滚动思考内容
watch(thinkingText, () => {
  if (generating.value) {
    scrollToBottom(thinkRef.value)
  }
})

// 完成后自动折叠思考
watch(generating, (val, oldVal) => {
  if (oldVal === true && val === false) {
    thinkFold.value = true
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

/* 主体 */
.dialog-body {
  min-height: 200px;
  max-height: 520px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 表单区域 */
.form-section {
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

.form-label .required {
  color: var(--color-danger);
}

.kb-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.kb-status.linked .el-icon {
  color: var(--color-warning);
  font-size: 18px;
}

.kb-status.linked .kb-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.kb-status.empty {
  background: rgba(255, 77, 79, 0.05);
  border: 1px solid rgba(255, 77, 79, 0.2);
  color: var(--color-danger);
}

/* 生成过程区域 */
.process-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px;
  overflow: hidden;
}

/* 思考卡片 */
.think-card {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  flex-shrink: 0;
}

.think-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  color: #303133;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
}

.think-header:hover {
  background-color: rgba(64, 158, 255, 0.04);
}

.think-title {
  display: flex;
  align-items: center;
}

.think-status {
  display: flex;
  align-items: center;
}

.think-indicator {
  position: relative;
  width: 16px;
  height: 16px;
  margin-right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #409eff;
  animation: pulse-dot 1.8s ease-in-out infinite;
}

.indicator-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.5px solid #409eff;
  opacity: 0;
  animation: pulse-ring 1.8s ease-out infinite;
}

.think-text {
  font-size: 12px;
  color: #409eff;
}

.think-done {
  display: flex;
  align-items: center;
}

.done-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #67c23a;
}

.done-text {
  font-size: 12px;
  color: #67c23a;
}

.think-header .el-icon {
  color: #409eff;
  transition: transform 0.2s;
}

.think-header .el-icon.rotated {
  transform: rotate(180deg);
}

.think-content {
  border-top: 1px solid #ebeef5;
}

.content-inner {
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.6;
  color: #606266;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}

.content-inner::-webkit-scrollbar {
  width: 4px;
}

.content-inner::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(0.85); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 1; }
}

@keyframes pulse-ring {
  0% { transform: scale(0.5); opacity: 0.6; }
  100% { transform: scale(1.2); opacity: 0; }
}

/* 结果列表 */
.result-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 80px;
}

.result-list::-webkit-scrollbar {
  width: 4px;
}

.result-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.result-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.2s ease;
}

.result-item:hover {
  border-color: #c0c4cc;
}

.result-item.success {
  border-left: 3px solid #67c23a;
}

.result-item.error {
  border-left: 3px solid #f56c6c;
}

.result-item.generating {
  border-left: 3px solid #409eff;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-icon {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.result-item.success .item-icon {
  color: #67c23a;
}

.result-item.error .item-icon {
  color: #f56c6c;
}

.mini-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #409eff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.item-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.item-summary {
  font-size: 12px;
  color: #606266;
}

.item-meta .el-icon {
  color: #c0c4cc;
  transition: transform 0.2s;
}

.item-meta .el-icon.rotated {
  transform: rotate(180deg);
}

.item-detail {
  padding: 0 12px 8px;
}

.item-detail pre {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  font-size: 11px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.result-item.error .item-detail pre {
  color: #f56c6c;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  padding: 12px 0;
}

.loading-dots {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* 统计栏 */
.stats-bar {
  display: flex;
  justify-content: space-around;
  padding: 12px 16px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.error {
  color: #f56c6c;
}

.stat-label {
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

.footer-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.footer-hint.generating {
  color: var(--color-text-secondary);
}

.footer-hint.done {
  color: #67c23a;
}

.footer-actions {
  display: flex;
  gap: 8px;
}
</style>
