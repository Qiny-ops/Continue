<template>
  <div class="exec-content" :class="{ nested: !showCaseInfo }">
    <!-- 用例信息卡片（单执行展示；批量嵌套时由外层行头承载测试点，报告内不再重复） -->
    <div class="case-info-card" v-if="showCaseInfo">
      <div class="case-title-wrap">
        <span class="case-name">{{ caseName || '测试用例' }}</span>
        <span class="case-divider" v-if="testpoint"></span>
        <span class="case-testpoint" v-if="testpoint">{{ testpoint }}</span>
      </div>
      <span class="case-status" :class="statusClass">{{ statusLabel }}</span>
    </div>

    <!-- 思考过程 -->
    <div v-if="hasThinking" class="deep-think">
      <div class="think-header" @click="toggleThink">
        <div class="think-title">
          <span class="think-dot" :class="{ active: executing }"></span>
          <span class="think-label">{{ executing ? '正在思考…' : '思考过程' }}</span>
        </div>
        <el-icon :size="14" class="think-caret" :class="{ rotated: !thinkFold }">
          <ArrowDown />
        </el-icon>
      </div>
      <div class="think-content" v-show="!thinkFold || executing">
        <div class="content-inner" ref="thinkRef">{{ thinkContent }}</div>
      </div>
    </div>

    <!-- 执行步骤时间线 -->
    <div class="step-list">
      <template v-for="(step, idx) in steps" :key="idx">
        <div class="step-item" :class="step.status">
          <div class="step-rail">
            <span class="step-dot"></span>
            <span class="step-line" v-if="idx < steps.length - 1"></span>
          </div>
          <div class="step-body">
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
                <el-icon v-if="step.hasDetail" :size="12" class="step-caret" :class="{ rotated: step.expanded }">
                  <ArrowDown />
                </el-icon>
              </div>
            </div>
            <div class="step-detail" v-show="step.expanded && step.detail">
              <pre>{{ step.detail }}</pre>
            </div>
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
      <span class="result-label">执行完成</span>
      <div class="result-right">
        <div class="result-stats">
          <span class="stat-item ok"><span class="stat-dot ok"></span>成功 {{ successCount }}</span>
          <span class="stat-item bad"><span class="stat-dot bad"></span>失败 {{ failCount }}</span>
        </div>
        <span class="result-duration">耗时 {{ durationSeconds ?? 0 }}s</span>
      </div>
    </div>

    <!-- 分析中提示 -->
    <div v-if="validating" class="analysis-loading-item">
      <span class="al-dot"></span>
      <span class="al-name">分析失败原因</span>
      <span class="al-status">正在分析…</span>
    </div>

    <!-- 失败分析结果 -->
    <div v-if="showFailureAnalysis" class="failure-analysis-item">
      <div class="analysis-header" @click="toggleAnalysis">
        <span class="fa-icon">!</span>
        <span class="fa-name">失败原因分析</span>
        <span v-if="failureAnalysis.rootCause" class="fa-summary">{{ failureAnalysis.rootCause }}</span>
        <el-icon :size="12" class="fa-caret" :class="{ rotated: analysisExpanded }">
          <ArrowDown />
        </el-icon>
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
          <span class="detail-section-title">修改建议（仅供参考，实际修改需根据排查结果）</span>
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
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  executing: Boolean,
  validating: Boolean,
  status: String,
  caseName: String,
  testpoint: String,
  duration: Number,
  logs: String,
  keyDecisions: Array,
  thinkingContent: String,
  failureAnalysis: Object,
  showCaseInfo: { type: Boolean, default: true }
})

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
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-radius: 8px;
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
  font-weight: 500;
  color: #1f2329;
}

.case-divider {
  width: 1px;
  height: 14px;
  background: #e5e6eb;
  flex-shrink: 0;
}

.case-testpoint {
  font-size: 13px;
  color: #646a73;
}

.case-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  flex-shrink: 0;
}

.case-status.idle { background: #f4f4f5; color: #8f959e; }
.case-status.running { background: #e6f1fb; color: #185fa5; }
.case-status.success { background: #eaf6ee; color: #2ba471; }
.case-status.error { background: #fdeced; color: #e5484d; }

/* 思考卡片 */
.deep-think {
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
}

.think-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
}

.think-header:hover {
  background: #f7f8fa;
}

.think-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.think-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #185fa5;
  flex-shrink: 0;
}

.think-dot.active {
  animation: pulse-dot 1.6s ease-in-out infinite;
}

.think-label {
  font-size: 12px;
  color: #646a73;
}

.think-caret {
  color: #c0c4cc;
  transition: transform 0.2s;
}

.think-caret.rotated {
  transform: rotate(180deg);
}

.think-content {
  border-top: 0.5px solid #e5e6eb;
}

.content-inner {
  padding: 10px 12px;
  font-family: Consolas, Menlo, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #646a73;
  background: #f7f8fa;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}

.content-inner::-webkit-scrollbar { width: 4px; }
.content-inner::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.1); border-radius: 2px; }

@keyframes pulse-dot {
  0%, 100% { transform: scale(0.85); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* 步骤时间线 */
.step-list {
  display: flex;
  flex-direction: column;
}

.step-item {
  display: flex;
  gap: 10px;
}

.step-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 10px;
  flex-shrink: 0;
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 13px;
  flex-shrink: 0;
  background: #c0c4cc;
}

.step-item.success .step-dot { background: #2ba471; }
.step-item.error .step-dot { background: #e5484d; }
.step-item.running .step-dot { background: #185fa5; }

.step-line {
  flex: 1;
  width: 0.5px;
  background: #e5e6eb;
  margin: 2px 0;
}

.step-body {
  flex: 1;
  min-width: 0;
  padding-bottom: 14px;
}

.step-item:last-child .step-body {
  padding-bottom: 0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  cursor: pointer;
}

.step-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.step-icon {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.step-item.success .step-icon { color: #2ba471; }
.step-item.error .step-icon { color: #e5484d; }
.step-item.running .step-icon { color: #185fa5; }

.mini-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #185fa5;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.step-name {
  font-size: 13px;
  color: #1f2329;
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
  color: #646a73;
}

.step-duration {
  font-size: 11px;
  color: #8f959e;
}

.step-caret {
  color: #c0c4cc;
  transition: transform 0.2s;
}

.step-caret.rotated {
  transform: rotate(180deg);
}

.step-detail {
  padding: 0 0 4px;
}

.step-detail pre {
  margin: 0;
  padding: 8px 10px;
  background: #f7f8fa;
  border: 0.5px solid #e5e6eb;
  border-radius: 6px;
  font-size: 11px;
  color: #646a73;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  padding: 8px 0 8px 20px;
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
  background: #185fa5;
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
  padding: 10px 12px;
  background: #f7f8fa;
  border: 0.5px solid #e5e6eb;
  border-radius: 8px;
}

.result-label {
  font-size: 14px;
  font-weight: 500;
  color: #1f2329;
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
  gap: 5px;
  font-size: 13px;
  color: #646a73;
}

.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.stat-dot.ok { background: #2ba471; }
.stat-dot.bad { background: #e5484d; }

.result-duration {
  font-size: 12px;
  color: #8f959e;
}

/* 分析中提示 */
.analysis-loading-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-left: 3px solid #185fa5;
  border-radius: 6px;
}

.al-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #185fa5;
  animation: pulse-dot 1.6s ease-in-out infinite;
}

.al-name {
  font-size: 13px;
  color: #1f2329;
  font-weight: 500;
}

.al-status {
  font-size: 12px;
  color: #185fa5;
  margin-left: auto;
}

/* 失败分析结果 callout */
.failure-analysis-item {
  background: #fdf6ec;
  border: 0.5px solid #f3d9a8;
  border-radius: 8px;
  overflow: hidden;
}

.analysis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
}

.fa-icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #b9760a;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.fa-name {
  font-size: 13px;
  color: #b9760a;
  font-weight: 500;
}

.fa-summary {
  font-size: 12px;
  color: #8a6d3b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.fa-caret {
  color: #c0a06a;
  transition: transform 0.2s;
  margin-left: auto;
}

.fa-caret.rotated {
  transform: rotate(180deg);
}

.analysis-detail {
  padding: 0 12px 12px;
  max-height: 240px;
  overflow-y: auto;
}

.analysis-detail::-webkit-scrollbar { width: 4px; }
.analysis-detail::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 2px; }

.detail-item {
  padding: 8px 10px;
  background: #fff;
  border: 0.5px solid #f3e3c4;
  border-radius: 6px;
  margin-bottom: 6px;
}

.detail-item:first-child {
  margin-top: 10px;
}

.detail-label {
  font-size: 11px;
  color: #8f959e;
  display: block;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 12px;
  color: #1f2329;
  line-height: 1.5;
}

/* 根本原因 - 红色背景高亮 */
.root-cause-item {
  background: #fdeced;
  border-color: #f7c4c4;
}

.root-cause-value {
  color: #e5484d;
  font-weight: 500;
}

.detail-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 0.5px dashed #ecd9b8;
}

.detail-section-title {
  font-size: 11px;
  color: #8f959e;
  display: block;
  margin-bottom: 6px;
}

.detail-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  background: #fff;
  border: 0.5px solid #f3e3c4;
  border-radius: 6px;
}

.step-num {
  font-size: 11px;
  color: #fff;
  font-weight: 500;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #185fa5;
  border-radius: 50%;
  flex-shrink: 0;
}

.step-text {
  font-size: 12px;
  color: #1f2329;
  line-height: 1.5;
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
  background: #fff;
  border: 0.5px solid #f3e3c4;
  border-radius: 6px;
}

.suggestion-badge {
  font-size: 11px;
  color: #185fa5;
  font-weight: 500;
  padding: 1px 6px;
  background: #e6f1fb;
  border-radius: 3px;
  flex-shrink: 0;
}

.suggestion-text {
  font-size: 12px;
  color: #1f2329;
  line-height: 1.4;
}

/* 滚动条 */
.exec-content::-webkit-scrollbar { width: 4px; }
.exec-content::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 2px; }

/* 批量嵌套：外层 .case-report 已统一滚动，内层块不再各自限高，避免双重滚动条 */
.exec-content.nested .content-inner { max-height: none; }
.exec-content.nested .analysis-detail { max-height: none; }
.exec-content.nested .step-detail pre { max-height: none; }
</style>
