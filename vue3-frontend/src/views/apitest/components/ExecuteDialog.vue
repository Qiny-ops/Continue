<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    width="760px"
    :close-on-click-modal="!executing"
    :close-on-press-escape="!executing"
    :show-close="!executing"
    destroy-on-close
  >
    <div class="exec-content">
      <!-- 用例信息卡片 -->
      <div class="case-info-card">
        <div class="case-title-wrap">
          <span class="case-name">{{ caseName || '测试用例' }}</span>
          <span class="case-divider" v-if="testpoint"></span>
          <span class="case-testpoint" v-if="testpoint">{{ testpoint }}</span>
        </div>
        <span class="case-status" :class="statusClass">{{ statusLabel }}</span>
      </div>
      <!-- 思考过程卡片 -->
      <div v-if="hasThinking" class="deep-think">
        <div class="think-header" @click="toggleThink">
          <div class="think-title">
            <span v-if="executing" class="thinking-status">
              <span class="thinking-indicator">
                <span class="indicator-dot"></span>
                <span class="indicator-ring"></span>
              </span>
              <span class="thinking-text">{{ statusText }}</span>
            </span>
            <span v-else class="done-status">
              <span class="done-icon">{{ status === 'pass' ? '✓' : '✗' }}</span>
              <span class="done-text">{{ status === 'pass' ? '执行完成' : '执行失败' }}</span>
            </span>
          </div>
          <div class="toggle-icon-wrapper">
            <el-icon :size="14" :class="{ rotated: !thinkFold }">
              <ArrowDown />
            </el-icon>
          </div>
        </div>
        <div class="think-content" v-show="!thinkFold || executing">
          <div class="content-inner" ref="thinkRef">{{ thinkContent }}</div>
        </div>
      </div>

      <!-- 执行步骤列表 -->
      <div class="step-list">
        <template v-for="(step, idx) in steps" :key="idx">
          <div class="step-item" :class="step.status">
            <div class="step-header" @click="toggleStep(idx)">
              <div class="step-main">
                <span class="step-icon">
                  <span v-if="step.status === 'running'" class="mini-spinner"></span>
                  <span v-else>{{ step.icon }}</span>
                </span>
                <span class="step-name">{{ step.name }}</span>
              </div>
              <div class="step-meta">
                <span v-if="step.summary" class="step-summary">{{ step.summary }}</span>
                <span v-if="step.duration" class="step-duration">{{ step.duration }}ms</span>
                <el-icon v-if="step.hasDetail" :size="12" :class="{ rotated: step.expanded }">
                  <ArrowDown />
                </el-icon>
              </div>
            </div>
            <div class="step-detail" v-show="step.expanded && step.detail">
              <pre>{{ step.detail }}</pre>
            </div>
          </div>
        </template>

        <!-- 加载指示器 -->
        <div v-if="executing" class="loading-indicator">
          <div class="loading-typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- 执行结果 -->
      <div v-if="!executing && status !== 'idle'" class="result-bar">
        <span class="stat-title">执行完成</span>
        <div class="result-right">
          <div class="result-stats">
            <span class="stat-item">
              <span class="stat-icon success">✓ 成功</span>
              <span class="stat-num">{{ successCount }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-icon fail">✗ 失败</span>
              <span class="stat-num">{{ failCount }}</span>
            </span>
          </div>
          <span class="result-duration">耗时 {{ durationSeconds ?? 0 }}s</span>
        </div>
      </div>

      <!-- 分析中提示 -->
      <div v-if="validating" class="analysis-loading-item">
        <div class="loading-header">
          <div class="loading-main">
            <span class="loading-icon">
              <span class="mini-spinner"></span>
            </span>
            <span class="loading-name">分析失败原因</span>
          </div>
          <div class="loading-meta">
            <span class="loading-status">正在分析...</span>
          </div>
        </div>
      </div>

      <!-- 失败分析结果 -->
      <div v-if="showFailureAnalysis" class="failure-analysis-item">
        <div class="analysis-header" @click="toggleAnalysis">
          <div class="analysis-main">
            <span class="analysis-icon">⚠</span>
            <span class="analysis-name warning-text">警告：失败原因</span>
          </div>
          <div class="analysis-meta">
            <span v-if="failureAnalysis.rootCause" class="analysis-summary warning-summary">{{ failureAnalysis.rootCause.substring(0, 30) }}...</span>
            <el-icon :size="12" :class="{ rotated: analysisExpanded }">
              <ArrowDown />
            </el-icon>
          </div>
        </div>
        <div class="analysis-detail" v-show="analysisExpanded">
          <div v-if="failureAnalysis.rootCause" class="detail-item root-cause-item">
            <span class="detail-label">根本原因</span>
            <span class="detail-value root-cause-value">{{ failureAnalysis.rootCause }}</span>
          </div>
          <div v-if="failureAnalysis.affectedInterfaces?.length" class="detail-item">
            <span class="detail-label">影响接口</span>
            <span class="detail-value">{{ failureAnalysis.affectedInterfaces.join(', ') }}</span>
          </div>
          <div v-if="failureAnalysis.debugSteps?.length" class="detail-section">
            <span class="detail-section-title">排查步骤</span>
            <div class="detail-steps">
              <div v-for="(step, i) in failureAnalysis.debugSteps" :key="i" class="step-row">
                <span class="step-num">{{ i + 1 }}</span>
                <span class="step-text">{{ step }}</span>
              </div>
            </div>
          </div>
          <div v-if="failureAnalysis.suggestions?.length" class="detail-section">
            <span class="detail-section-title">修改建议（仅供参考实际修改需要根据排查结果）</span>
            <div class="detail-suggestions">
              <div v-for="(s, i) in failureAnalysis.suggestions" :key="i" class="suggestion-row">
                <span class="suggestion-badge">{{ s.type || '建议' }}</span>
                <span class="suggestion-text">{{ s.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)" :disabled="executing">
        关闭
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  visible: Boolean,
  executing: Boolean,
  validating: Boolean,
  status: String,
  caseName: String,
  testpoint: String,
  duration: Number,
  logs: String,
  keyDecisions: Array,
  thinkingContent: String,
  failureAnalysis: Object
})

const emit = defineEmits(['update:visible'])

const thinkFold = ref(false)
const thinkRef = ref(null)
const stepStates = reactive({})
const analysisExpanded = ref(true)

// 思考内容
const hasThinking = computed(() => {
  return (props.thinkingContent && props.thinkingContent.length > 0) || props.executing
})

const thinkContent = computed(() => {
  return props.thinkingContent || ''
})

const statusText = computed(() => {
  if (props.executing) return '正在执行...'
  return ''
})

const statusClass = computed(() => {
  if (props.executing) return 'running'
  if (props.status === 'pass') return 'success'
  if (props.status === 'fail' || props.status === 'error') return 'error'
  return 'idle'
})

const statusLabel = computed(() => {
  if (props.executing) return '执行中'
  if (props.status === 'pass') return '通过'
  if (props.status === 'fail') return '失败'
  if (props.status === 'error') return '错误'
  return '待执行'
})

// 解析步骤 - 从传入的 logs 和 keyDecisions 提取完整信息
const steps = computed(() => {
  // 直接使用 keyDecisions 作为步骤数据源，它包含更丰富的信息
  if (props.keyDecisions && props.keyDecisions.length > 0) {
    return props.keyDecisions.map((decision, idx) => {
      // 从 decision 提取状态
      let status = 'success'
      let icon = '✓'
      if (decision.type === 'warning') {
        status = 'error'
        icon = '✗'
      } else if (decision.type === 'running') {
        status = 'running'
        icon = ''
      }

      // 提取耗时信息（如果有）
      let duration = null
      const durMatch = decision.text?.match(/(\d+)ms/)
      if (durMatch) {
        duration = parseInt(durMatch[1])
      }

      // 构建详情内容
      let detail = decision.detail || null

      return {
        name: decision.text?.substring(0, 50) || '执行步骤',
        status,
        icon,
        summary: decision.summary || null,
        duration,
        detail,
        hasDetail: !!detail,
        expanded: stepStates[idx] || false
      }
    })
  }

  // 备用：从日志解析
  if (!props.logs) return []
  const result = []
  const lines = props.logs.split('\n')

  for (const line of lines) {
    const t = line.trim()
    if (!t) continue

    // 依赖分析
    if (t.includes('依赖分析完成')) {
      const match = t.match(/共 (\d+) 个/)
      result.push({
        name: '依赖分析',
        status: 'success',
        icon: '✓',
        summary: match ? `发现 ${match[1]} 个接口` : null,
        duration: null,
        detail: null,
        hasDetail: false,
        expanded: false
      })
    }

    // 执行结果
    if (t.includes('✓') || t.includes('✗')) {
      let name = t.replace(/[✓✗]/g, '').trim()
      let duration = null
      let status = t.includes('✓') ? 'success' : 'error'
      let icon = t.includes('✓') ? '✓' : '✗'

      const durMatch = name.match(/(\d+)ms/)
      if (durMatch) {
        duration = parseInt(durMatch[1])
        name = name.replace(durMatch[0], '').trim()
      }

      // 查找下一行的错误详情
      let detail = null
      if (status === 'error') {
        const nextLine = lines[lines.indexOf(line) + 1]
        if (nextLine && (nextLine.includes('错误') || nextLine.includes('Error'))) {
          detail = nextLine.trim()
        }
      }

      result.push({
        name: name.substring(0, 40),
        status,
        icon,
        summary: null,
        duration,
        detail,
        hasDetail: !!detail,
        expanded: stepStates[result.length] || false
      })
    }

    // 执行完成
    if (t.includes('执行完成')) {
      result.push({
        name: '执行完成',
        status: props.status === 'pass' ? 'success' : 'error',
        icon: props.status === 'pass' ? '✓' : '✗',
        summary: `总耗时 ${props.duration || 0}ms`,
        duration: props.duration,
        detail: null,
        hasDetail: false,
        expanded: false
      })
    }
  }

  return result
})

const successCount = computed(() => steps.value.filter(s => s.status === 'success').length)
const failCount = computed(() => steps.value.filter(s => s.status === 'error').length)

// 耗时转换为秒（确保始终返回有效值）
const durationSeconds = computed(() => {
  const ms = props.duration ?? 0
  return (ms / 1000).toFixed(1)
})

// 是否展示失败分析结果
const showFailureAnalysis = computed(() => {
  return !props.executing && !props.validating && (props.status === 'fail' || props.status === 'error') && props.failureAnalysis
})

// 格式化后的失败分析（转换为 camelCase）
const failureAnalysis = computed(() => {
  const fa = props.failureAnalysis
  if (!fa) return null
  return {
    rootCause: fa.root_cause || fa.rootCause || '',
    affectedInterfaces: fa.affected_interfaces || fa.affectedInterfaces || [],
    suggestions: fa.suggestions || [],
    debugSteps: fa.debug_steps || fa.debugSteps || []
  }
})

// 方法
const toggleThink = () => {
  if (!props.executing) {
    thinkFold.value = !thinkFold.value
  }
}

const toggleStep = (idx) => {
  stepStates[idx] = !stepStates[idx]
}

const toggleAnalysis = () => {
  if (!props.validating) {
    analysisExpanded.value = !analysisExpanded.value
  }
}

// 自动滚动思考内容
watch(() => props.thinkingContent, () => {
  if (props.executing) {
    nextTick(() => {
      if (thinkRef.value) {
        thinkRef.value.scrollTop = thinkRef.value.scrollHeight
      }
    })
  }
})

// 完成后自动折叠思考
watch(() => props.executing, (val, oldVal) => {
  if (oldVal === true && val === false) {
    thinkFold.value = true
  }
})

// 打开时重置
watch(() => props.visible, (val) => {
  if (val) {
    thinkFold.value = false
    Object.keys(stepStates).forEach(k => stepStates[k] = false)
  }
})
</script>

<style scoped>
.exec-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

/* 用例信息卡片 */
.case-info-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
  border: 1px solid #ebeef5;
  padding: 10px 14px;
}

.case-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.case-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.case-divider {
  width: 2px;
  height: 14px;
  background: #dcdfe6;
  flex-shrink: 0;
}

.case-testpoint {
  font-size: 13px;
  color: #606266;
}

.case-status {
  font-size: 12px;
  padding: 2px 8px;
  flex-shrink: 0;
}

.case-status.idle {
  background: #f0f0f0;
  color: #909399;
}

.case-status.running {
  background: #ecf5ff;
  color: #409eff;
}

.case-status.success {
  background: #f0f9eb;
  color: #67c23a;
}

.case-status.error {
  background: #fef0f0;
  color: #f56c6c;
}

/* 思考卡片 - 参考 WeKnora deepThink */
.deep-think {
  display: flex;
  flex-direction: column;
  font-size: 12px;
  width: 100%;
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: all 0.25s ease;
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

.thinking-status {
  display: flex;
  align-items: center;
}

.thinking-indicator {
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

.thinking-text {
  font-size: 12px;
  color: #409eff;
}

.done-status {
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

.toggle-icon-wrapper {
  color: #409eff;
}

.toggle-icon-wrapper .el-icon {
  transition: transform 0.2s;
}

.toggle-icon-wrapper .el-icon.rotated {
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

/* 步骤列表 - 参考 WeKnora action-card */
.step-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.2s ease;
}

.step-item:hover {
  border-color: #c0c4cc;
}

.step-item.success {
  border-left: 3px solid #67c23a;
}

.step-item.error {
  border-left: 3px solid #f56c6c;
}

.step-item.running {
  border-left: 3px solid #409eff;
  background: linear-gradient(120deg, rgba(64, 158, 255, 0.02), #fff);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
}

.step-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-icon {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.success .step-icon {
  color: #67c23a;
}

.step-item.error .step-icon {
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

.step-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.step-summary {
  font-size: 12px;
  color: #606266;
}

.step-duration {
  font-size: 11px;
  color: #909399;
}

.step-meta .el-icon {
  color: #c0c4cc;
  transition: transform 0.2s;
}

.step-meta .el-icon.rotated {
  transform: rotate(180deg);
}

.step-detail {
  padding: 0 12px 8px;
  margin-top: 0;
}

.step-detail pre {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  font-size: 11px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

.step-item.error .step-detail pre {
  color: #f56c6c;
}

/* 加载指示器 - 参考 WeKnora */
.loading-indicator {
  display: flex;
  align-items: center;
  padding: 12px 0;
}

.loading-typing {
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s ease-in-out infinite;
}

.loading-typing span:nth-child(1) { animation-delay: 0s; }
.loading-typing span:nth-child(2) { animation-delay: 0.2s; }
.loading-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* 结果栏 */
.result-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.stat-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.result-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.result-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 12px;
  font-weight: 600;
}

.stat-icon.success {
  color: #67c23a;
}

.stat-icon.fail {
  color: #f56c6c;
}

.stat-num {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.result-duration {
  font-size: 12px;
  color: #909399;
}

/* 分析中提示 */
.analysis-loading-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.2s ease;
  border-left: 3px solid #409eff;
  background: linear-gradient(120deg, rgba(64, 158, 255, 0.02), #fff);
}

.loading-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
}

.loading-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-icon {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.loading-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.loading-status {
  font-size: 12px;
  color: #409eff;
}

/* 失败分析结果 */
.failure-analysis-item {
  background: #fff;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  transition: all 0.2s ease;
  border-left: 3px solid #e6a23c;
}

.failure-analysis-item:hover {
  border-color: #c0c4cc;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  background: #fdf6ec;
}

.analysis-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-icon {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #e6a23c;
}

.analysis-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.warning-text {
  color: #e6a23c;
  font-weight: 600;
}

.analysis-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.analysis-status {
  font-size: 12px;
  color: #409eff;
}

.analysis-summary {
  font-size: 12px;
  color: #606266;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.warning-summary {
  color: #e6a23c;
}

.analysis-meta .el-icon {
  color: #c0c4cc;
  transition: transform 0.2s;
}

.analysis-meta .el-icon.rotated {
  transform: rotate(180deg);
}

.analysis-detail {
  padding: 0 12px 12px;
  margin-top: 0;
  max-height: 200px;
  overflow-y: auto;
}

.analysis-detail::-webkit-scrollbar {
  width: 4px;
}

.analysis-detail::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.detail-item {
  padding: 8px;
  background: #f5f7fa;
  margin-bottom: 6px;
}

.detail-item:first-of-type {
  margin-top: 10px;
}

.detail-item:last-of-type {
  margin-bottom: 0;
}

/* 根本原因 - 红色背景高亮 */
.root-cause-item {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
}

.root-cause-value {
  color: #f56c6c;
  font-weight: 500;
}

.detail-label {
  font-size: 11px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 12px;
  color: #303133;
  line-height: 1.5;
}

.detail-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e4e7ed;
}

.detail-section:first-of-type {
  margin-top: 8px;
}

.detail-section-title {
  font-size: 11px;
  color: #909399;
  display: block;
  margin-bottom: 6px;
}

.detail-suggestions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suggestion-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  background: #f5f7fa;
}

.suggestion-badge {
  font-size: 11px;
  color: #409eff;
  font-weight: 500;
  padding: 1px 4px;
  background: #ecf5ff;
  border-radius: 2px;
  flex-shrink: 0;
}

.suggestion-text {
  font-size: 12px;
  color: #303133;
  line-height: 1.4;
}

.detail-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  background: #f0f7ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
}

.step-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  background: #fff;
  border-radius: 3px;
}

.step-num {
  font-size: 11px;
  color: #fff;
  font-weight: 600;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  border-radius: 50%;
  flex-shrink: 0;
}

.step-text {
  font-size: 12px;
  color: #303133;
  line-height: 1.5;
}

/* 滚动条 */
.exec-content::-webkit-scrollbar {
  width: 4px;
}

.exec-content::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}
</style>
