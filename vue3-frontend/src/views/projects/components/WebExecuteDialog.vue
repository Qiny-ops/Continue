<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="dialogTitle"
    width="820px"
    :close-on-click-modal="!executing"
    :close-on-press-escape="!executing"
    :show-close="!executing"
    destroy-on-close
    class="web-exec-dialog"
  >
    <div class="web-exec-content">
      <!-- 配置区（执行前填写，执行中禁用） -->
      <div class="config-card" :class="{ collapsed: executing }">
        <div class="config-row">
          <label class="config-label">选择环境</label>
          <el-select
            v-model="config.environmentId"
            placeholder="从「环境管理」中选择"
            :disabled="executing"
            :loading="envLoading"
            filterable
            clearable
            style="width: 100%"
            @change="onEnvChange"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="`${env.name}（${env.base_url}）`"
              :value="env.id"
            />
          </el-select>
          <div v-if="!envLoading && environments.length === 0" class="env-hint">
            本项目暂无「Web 自动化」用途的环境，请先到左侧「环境管理」新建一个用途为 <b>Web 自动化</b> 的环境。
          </div>
        </div>
        <div class="config-row">
          <label class="config-label">
            起始 URL <span class="req">*</span>
          </label>
          <el-input
            v-model="config.startUrl"
            placeholder="选择环境后自动填入，也可手动修改"
            :disabled="executing"
            size="default"
          />
        </div>
        <div class="config-row">
          <div class="config-item">
            <label class="config-label">站点提示</label>
            <el-input
              v-model="config.siteHint"
              placeholder="可选，如：首页搜索框在顶部"
              :disabled="executing"
              size="default"
            />
          </div>
        </div>
        <div v-if="batchMode" class="config-batch-tip">
          批量模式：以下配置将应用到选中的 <strong>{{ cases.length }}</strong> 个用例，按顺序依次执行。
        </div>
      </div>

      <!-- 进度信息 -->
      <div v-if="executing || status !== 'idle'" class="progress-bar">
        <span class="case-name">{{ currentCaseName || 'Web 自动化用例' }}</span>
        <span v-if="batchMode" class="batch-progress">
          用例 {{ Math.min(executingIndex + 1, cases.length) }}/{{ cases.length }}
        </span>
        <span class="status-tag" :class="statusClass">{{ statusLabel }}</span>
        <span v-if="report && !executing" class="result-stats">
          <span class="ok"><span class="dot ok"></span>成功 {{ report.success ?? 0 }}</span>
          <span class="bad"><span class="dot bad"></span>失败 {{ (report.total ?? 0) - (report.success ?? 0) }}</span>
        </span>
      </div>

      <!-- 规划思考 -->
      <div v-if="hasThinking" class="deep-think">
        <div class="think-header" @click="thinkFold = !thinkFold">
          <div class="think-title">
            <span class="think-dot" :class="{ active: executing }"></span>
            <span class="think-label">{{ executing ? '正在编排与执行…' : '规划过程' }}</span>
          </div>
          <el-icon :size="14" class="think-caret" :class="{ rotated: !thinkFold }"><ArrowDown /></el-icon>
        </div>
        <div class="think-content" v-show="!thinkFold || executing">
          <div class="content-inner" ref="thinkRef">{{ thinking }}</div>
        </div>
      </div>

      <!-- 步骤时间线 -->
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
                  <el-icon v-if="step.hasDetail" :size="12" class="step-caret" :class="{ rotated: step.expanded }"><ArrowDown /></el-icon>
                </div>
              </div>
              <div class="step-detail" v-show="step.expanded && step.detail">
                <pre>{{ step.detail }}</pre>
              </div>
            </div>
          </div>
        </template>

        <div v-if="executing" class="loading-indicator">
          <div class="loading-typing"><span></span><span></span><span></span></div>
        </div>
      </div>

      <!-- 最终报告 -->
      <div v-if="!executing && report" class="result-card" :class="report.passed ? 'pass' : 'fail'">
        <div class="result-head">
          <span class="result-icon">{{ report.passed ? '✓' : '✗' }}</span>
          <span class="result-title">执行{{ report.passed ? '通过' : '失败' }}</span>
          <span class="result-duration">耗时 {{ durationSeconds }}s</span>
        </div>
        <div class="result-body">
          <span>成功 {{ report.success ?? 0 }} / 共 {{ report.total ?? 0 }} 步</span>
          <span v-if="report.step_count">步骤数 {{ report.step_count }}</span>
          <span v-if="report.stopped_url">终止于 {{ report.stopped_url }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button
        v-if="!executing"
        type="primary"
        :disabled="!config.startUrl"
        @click="start"
      >
        开始执行
      </el-button>
      <el-button v-if="executing" type="danger" plain @click="stop">停止</el-button>
      <el-button @click="$emit('update:visible', false)" :disabled="executing">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import webAutoApi from '@/api/modules/webauto.js'
import { environmentApi } from '@/api/modules/apitest'

const props = defineProps({
  visible: Boolean,
  // 用例数组（单条执行传 [row]，批量传多行）；行需含 id / title
  cases: { type: Array, default: () => [] },
  // 项目 ID（用于拉取「环境管理」中维护的环境）
  projectId: { type: [Number, String], default: null }
})
const emit = defineEmits(['update:visible'])

const batchMode = computed(() => props.cases.length > 1)

const config = reactive({ startUrl: '', siteHint: '', environmentId: '' })
const environments = ref([])
const envLoading = ref(false)
const executing = ref(false)
const executingIndex = ref(0)
const currentCaseName = ref('')
const status = ref('idle') // idle | running | pass | fail | error
const thinking = ref('')
const steps = ref([])
const report = ref(null)
const thinkFold = ref(false)
const thinkRef = ref(null)
const stepStates = reactive({})
const aborted = ref(false)
let streamHandle = null

const dialogTitle = computed(() => batchMode.value ? 'Web 自动化批量执行' : 'Web 自动化执行')

const hasThinking = computed(() => thinking.value.length > 0 || executing.value)
const statusClass = computed(() => {
  if (executing.value) return 'running'
  if (status.value === 'pass') return 'success'
  if (status.value === 'fail' || status.value === 'error') return 'error'
  return 'idle'
})
const statusLabel = computed(() => {
  if (executing.value) return '执行中'
  if (status.value === 'pass') return '通过'
  if (status.value === 'fail') return '失败'
  if (status.value === 'error') return '错误'
  return '待执行'
})
const durationSeconds = computed(() => {
  const ms = report.value?.duration_ms ?? 0
  return (ms / 1000).toFixed(1)
})

function describeAction(a) {
  if (!a) return '未知动作'
  const step = a.step != null ? `[${a.step}] ` : ''
  const act = a.action || ''
  const target = a.target || a.check || ''
  const value = a.value ? `「${a.value}」` : ''
  return `${step}${act} ${target} ${value}`.trim()
}

function pushStep(item) {
  steps.value.push({
    name: item.name,
    status: item.status || 'success',
    icon: item.status === 'error' ? '✗' : (item.status === 'repair' ? '↻' : (item.status === 'info' ? '•' : '✓')),
    summary: item.summary || null,
    duration: item.duration || null,
    detail: item.detail || null,
    hasDetail: !!item.detail,
    expanded: stepStates[steps.value.length] || false
  })
}

function handleEvent(event) {
  const type = event.type
  const data = event.data || {}
  if (type === 'start') {
    thinking.value += `▶ 开始${data.mode === 'plan' ? '规划' : '执行'}，起始页：${data.start_url || ''}\n`
    if (data.agentic) thinking.value += `（agentic 看页面闭环模式）\n`
  } else if (type === 'snapshot') {
    thinking.value += `\n📸 已抓取页面快照：${data.url || ''}\n`
  } else if (type === 'plan_chunk') {
    const actions = data.actions || []
    thinking.value += `\n— 第 ${data.iteration ?? '?'} 轮规划 —\n`
    for (const a of actions) {
      thinking.value += `  · ${describeAction(a)}\n`
    }
  } else if (type === 'step') {
    const a = data.action || {}
    const ok = !!data.success
    const summary = data.url ? data.url : (a.action || '')
    let detail = null
    if (!ok && data.error) detail = `错误：${data.error}`
    else if (data.extracted) detail = `提取：${JSON.stringify(data.extracted)}`
    else if (data.value) detail = `输入值：${data.value}`
    if (data.screenshot) detail = (detail ? detail + '\n' : '') + `截图：${data.screenshot}`
    pushStep({
      name: describeAction(a),
      status: ok ? 'success' : 'error',
      summary,
      duration: data.duration_ms || null,
      detail
    })
  } else if (type === 'repair') {
    pushStep({
      name: '自愈重规划',
      status: 'repair',
      summary: `第 ${data.failed_step ?? '?'} 步失败`,
      detail: data.error ? `原因：${data.error}` : null
    })
  } else if (type === 'report') {
    report.value = data
    status.value = data.passed ? 'pass' : 'fail'
    thinking.value += `\n━━━━━━━━━━━━━━━━━━━━━━\n执行完成：成功 ${data.success ?? 0} / 共 ${data.total ?? 0} 步\n`
  } else if (type === 'error') {
    status.value = 'error'
    pushStep({ name: '执行失败', status: 'error', summary: data.message || '发生错误' })
    thinking.value += `\n❌ ${data.message || '执行失败'}\n`
  }
}

function onEnvChange(id) {
  if (!id) return
  const env = environments.value.find((e) => e.id === id)
  if (env) config.startUrl = env.base_url || ''
}

async function fetchEnvironments() {
  if (!props.projectId) return
  envLoading.value = true
  try {
    // 只拉取「Web 自动化」用途的环境
    const res = await environmentApi.getEnvironments({ project: props.projectId, target_type: 'web' })
    environments.value = res?.results || res || []
  } catch (e) {
    environments.value = []
  } finally {
    envLoading.value = false
  }
}

function start() {
  if (!config.startUrl || !config.startUrl.trim()) {
    ElMessage.warning('请选择环境或填写起始 URL')
    return
  }
  if (!props.cases || props.cases.length === 0) {
    ElMessage.warning('没有可执行的用例')
    return
  }
  aborted.value = false
  executing.value = true
  status.value = 'running'
  thinking.value = ''
  steps.value = []
  report.value = null
  executingIndex.value = 0
  runAll()
}

async function runAll() {
  const list = props.cases
  for (let i = 0; i < list.length; i++) {
    if (aborted.value) break
    executingIndex.value = i
    const c = list[i]
    currentCaseName.value = c.title || c.name || `用例 ${c.id}`
    await runCase(c)
  }
  executing.value = false
}

function runCase(caseRow) {
  return new Promise((resolve) => {
    streamHandle = webAutoApi.executeCaseStream(
      {
        case_id: caseRow.id,
        start_url: config.startUrl.trim(),
        environment_id: config.environmentId || '',
        site_hint: config.siteHint || ''
      },
      (event) => handleEvent(event),
      (error) => {
        status.value = 'error'
        pushStep({ name: '执行失败', status: 'error', summary: error.message })
        thinking.value += `\n❌ ${error.message}\n`
        resolve()
      },
      () => resolve()
    )
  })
}

function stop() {
  aborted.value = true
  streamHandle?.abort?.()
  executing.value = false
  ElMessage.info('已停止执行')
}

function toggleStep(idx) {
  stepStates[idx] = !stepStates[idx]
}

// 自动滚动规划内容
watch(() => thinking.value, () => {
  if (executing.value) {
    nextTick(() => {
      if (thinkRef.value) thinkRef.value.scrollTop = thinkRef.value.scrollHeight
    })
  }
})

// 关闭时复位；打开时拉取本项目环境
watch(() => props.visible, (v) => {
  if (v) {
    fetchEnvironments()
  } else {
    aborted.value = true
    streamHandle?.abort?.()
    executing.value = false
  }
})
</script>

<style scoped>
.web-exec-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
}

/* 配置区 */
.config-card {
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.config-card.collapsed {
  opacity: 0.7;
}
.config-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.config-row.two {
  gap: 12px;
}
.config-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.config-label {
  font-size: 12px;
  color: #646a73;
  flex-shrink: 0;
  width: 72px;
}
.config-row.two .config-label {
  width: auto;
}
.env-hint {
  flex-basis: 100%;
  font-size: 12px;
  color: #d48806;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 4px;
  padding: 6px 8px;
  line-height: 1.5;
}
.env-hint b {
  color: #ad6800;
}
.req {
  color: #e5484d;
  margin-left: 2px;
}
.config-batch-tip {
  font-size: 12px;
  color: #185fa5;
  background: #e6f1fb;
  border-radius: 4px;
  padding: 6px 10px;
}

/* 进度信息 */
.progress-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.case-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2329;
}
.batch-progress {
  font-size: 12px;
  color: #646a73;
  background: #f4f4f5;
  border-radius: 10px;
  padding: 2px 10px;
}
.status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
}
.status-tag.idle { background: #f4f4f5; color: #8f959e; }
.status-tag.running { background: #e6f1fb; color: #185fa5; }
.status-tag.success { background: #eaf6ee; color: #2ba471; }
.status-tag.error { background: #fdeced; color: #e5484d; }
.result-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #646a73;
}
.result-stats .ok, .result-stats .bad {
  display: flex;
  align-items: center;
  gap: 5px;
}
.result-stats .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.result-stats .dot.ok { background: #2ba471; }
.result-stats .dot.bad { background: #e5484d; }

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
.think-header:hover { background: #f7f8fa; }
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
.think-dot.active { animation: pulse-dot 1.6s ease-in-out infinite; }
.think-label { font-size: 12px; color: #646a73; }
.think-caret { color: #c0c4cc; transition: transform 0.2s; }
.think-caret.rotated { transform: rotate(180deg); }
.think-content { border-top: 0.5px solid #e5e6eb; }
.content-inner {
  padding: 10px 12px;
  font-family: Consolas, Menlo, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #646a73;
  background: #f7f8fa;
  max-height: 220px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
}
.content-inner::-webkit-scrollbar { width: 4px; }
.content-inner::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }
@keyframes pulse-dot {
  0%, 100% { transform: scale(0.85); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* 步骤时间线 */
.step-list { display: flex; flex-direction: column; }
.step-item { display: flex; gap: 10px; }
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
.step-item.repair .step-dot { background: #f59e0b; }
.step-item.info .step-dot { background: #8f959e; }
.step-line {
  flex: 1;
  width: 0.5px;
  background: #e5e6eb;
  margin: 2px 0;
}
.step-body { flex: 1; min-width: 0; padding-bottom: 14px; }
.step-item:last-child .step-body { padding-bottom: 0; }
.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  cursor: pointer;
}
.step-main { display: flex; align-items: center; gap: 8px; min-width: 0; }
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
.step-item.repair .step-icon { color: #f59e0b; }
.step-item.info .step-icon { color: #8f959e; }
.step-item.running .step-icon { color: #185fa5; }
.mini-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #185fa5;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.step-name { font-size: 13px; color: #1f2329; font-weight: 500; }
.step-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.step-summary { font-size: 12px; color: #646a73; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.step-duration { font-size: 11px; color: #8f959e; }
.step-caret { color: #c0c4cc; transition: transform 0.2s; }
.step-caret.rotated { transform: rotate(180deg); }
.step-detail { padding: 0 0 4px; }
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
  max-height: 300px;
  overflow-y: auto;
}

/* 加载指示器 */
.loading-indicator { display: flex; align-items: center; padding: 8px 0 8px 20px; }
.loading-typing { display: flex; align-items: center; gap: 4px; }
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

/* 结果卡 */
.result-card {
  border-radius: 8px;
  padding: 12px 14px;
  border: 0.5px solid #e5e6eb;
}
.result-card.pass { background: #eaf6ee; border-color: #bfe3cb; }
.result-card.fail { background: #fdeced; border-color: #f7c4c4; }
.result-head { display: flex; align-items: center; gap: 10px; }
.result-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
}
.result-card.pass .result-icon { background: #2ba471; }
.result-card.fail .result-icon { background: #e5484d; }
.result-title { font-size: 14px; font-weight: 600; color: #1f2329; }
.result-duration { font-size: 12px; color: #8f959e; margin-left: auto; }
.result-body {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 12px;
  color: #646a73;
}

.web-exec-content::-webkit-scrollbar { width: 4px; }
.web-exec-content::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 2px; }
</style>
