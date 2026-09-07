<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    width="860px"
    top="5vh"
    :close-on-click-modal="!running"
    :close-on-press-escape="!running"
    :show-close="!running"
    destroy-on-close
    @open="onOpen"
  >
    <div class="batch-exec">
      <!-- 统计条 -->
      <div class="stat-strip">
        <div class="stat-block total">
          <span class="stat-num">{{ results.length }}</span>
          <span class="stat-cap">用例总数</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-block running">
          <span class="stat-num">{{ runningCount }}</span>
          <span class="stat-cap">执行中</span>
        </div>
        <div class="stat-block success">
          <span class="stat-num">{{ passCount }}</span>
          <span class="stat-cap">通过</span>
        </div>
        <div class="stat-block danger">
          <span class="stat-num">{{ failCount }}</span>
          <span class="stat-cap">失败</span>
        </div>
        <div class="stat-block warn">
          <span class="stat-num">{{ errorCount }}</span>
          <span class="stat-cap">错误</span>
        </div>
        <div class="stat-spacer"></div>
        <div class="stat-block duration">
          <span class="stat-num">{{ totalDurationSec }}<i>s</i></span>
          <span class="stat-cap">总耗时</span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar">
        <div
          class="progress-fill"
          :class="running ? '' : (hasFail ? 'fail' : 'ok')"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>

      <!-- 筛选 + 工具栏 -->
      <div class="tool-bar">
        <div class="filter-tabs">
          <span class="filter-tab" :class="{ active: activeFilter === 'all' }" @click="activeFilter = 'all'">全部 ({{ results.length }})</span>
          <span class="filter-tab" :class="{ active: activeFilter === 'running' }" @click="activeFilter = 'running'">执行中 ({{ runningCount }})</span>
          <span class="filter-tab" :class="{ active: activeFilter === 'pass' }" @click="activeFilter = 'pass'">通过 ({{ passCount }})</span>
          <span class="filter-tab" :class="{ active: activeFilter === 'fail' }" @click="activeFilter = 'fail'">失败 ({{ failCount }})</span>
          <span class="filter-tab" :class="{ active: activeFilter === 'error' }" @click="activeFilter = 'error'">错误 ({{ errorCount }})</span>
        </div>
        <div class="tool-right">
          <span class="list-count">显示 {{ filteredResults.length }} / {{ results.length }}</span>
          <el-button link type="primary" size="small" @click="expandAll">全部展开</el-button>
          <el-button link type="primary" size="small" @click="collapseAll">全部收起</el-button>
        </div>
      </div>

      <!-- 用例列表 -->
      <div class="case-list" ref="listRef">
        <div
          v-for="(r, idx) in filteredResults"
          :key="r.id"
          class="case-card"
          :class="[r.status, { 'is-expanded': r.expanded }]"
        >
          <div class="case-card-header" @click="r.expanded = !r.expanded">
            <span class="case-index">{{ idx + 1 }}</span>
            <div class="case-title">
              <span class="case-name" :title="r.name">{{ r.name }}<template v-if="r.testpoint"> - {{ r.testpoint }}</template></span>
            </div>
            <span class="case-status" :class="r.status">{{ statusLabel(r.status) }}</span>
            <span v-if="r.status === 'running' || r.status === 'analyzing'" class="case-mini-spinner"></span>
            <span v-else-if="r.total > 0" class="case-steps">{{ r.success }}/{{ r.total }}</span>
            <span v-if="r.duration" class="case-duration">{{ (r.duration / 1000).toFixed(1) }}s</span>
            <el-icon class="case-toggle" :class="{ rotated: r.expanded }"><ArrowDown /></el-icon>
          </div>
          <div v-show="r.expanded" class="case-report">
            <ExecuteReport
              :executing="r.status === 'running'"
              :validating="r.analyzing"
              :status="r.status"
              :case-name="r.name"
              :testpoint="r.testpoint"
              :duration="r.duration"
              :logs="r.logs"
              :key-decisions="toKeyDecisions(r)"
              :thinking-content="r.thinking"
              :failure-analysis="r.failureAnalysis"
              :show-case-info="false"
            />
          </div>
        </div>

        <div v-if="filteredResults.length === 0" class="empty-hint">
          当前筛选条件下没有用例
        </div>
      </div>
    </div>

    <template #footer>
      <div class="batch-footer">
        <div class="footer-left">
          <span class="concurrency-label">并发数</span>
          <el-select v-model="concurrency" :disabled="running" size="small" style="width: 88px">
            <el-option v-for="n in [1, 2, 3, 5, 8]" :key="n" :label="String(n)" :value="n" />
          </el-select>
        </div>
        <div class="footer-right">
          <el-button v-if="running" type="danger" plain @click="cancel">取消执行</el-button>
          <el-dropdown @command="handleExport" :disabled="results.length === 0">
            <el-button size="small" :disabled="results.length === 0">
              导出报告<el-icon style="margin-left: 4px"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="markdown">Markdown</el-dropdown-item>
                <el-dropdown-item command="json">JSON</el-dropdown-item>
                <el-dropdown-item command="html">HTML</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button @click="$emit('update:visible', false)" :disabled="running">
            {{ running ? '执行中…' : '关闭' }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiTestCaseApi } from '@/api/modules/apitest'
import ExecuteReport from './ExecuteReport.vue'

const props = defineProps({
  visible: Boolean,
  cases: { type: Array, default: () => [] },
  environmentId: { type: [Number, String], default: null }
})

const emit = defineEmits(['update:visible', 'refresh'])

const results = ref([])
const running = ref(false)
const cancelled = ref(false)
const concurrency = ref(3)
const activeFilter = ref('all')
const activeControllers = []
const startTime = ref(0)
const elapsedMs = ref(0)
const listRef = ref(null)

const executedCount = computed(() =>
  results.value.filter(r => ['pass', 'fail', 'error'].includes(r.status)).length
)
const passCount = computed(() => results.value.filter(r => r.status === 'pass').length)
const failCount = computed(() => results.value.filter(r => r.status === 'fail').length)
const errorCount = computed(() => results.value.filter(r => r.status === 'error').length)
const runningCount = computed(() =>
  results.value.filter(r => r.status === 'running' || r.status === 'analyzing').length
)
const hasFail = computed(() => failCount.value > 0 || errorCount.value > 0)
const progressPercent = computed(() =>
  results.value.length ? Math.round((executedCount.value / results.value.length) * 100) : 0
)
const totalDurationSec = computed(() => (elapsedMs.value / 1000).toFixed(1))

const filteredResults = computed(() => {
  if (activeFilter.value === 'all') return results.value
  if (activeFilter.value === 'running') {
    return results.value.filter(r => r.status === 'running' || r.status === 'analyzing')
  }
  return results.value.filter(r => r.status === activeFilter.value)
})

const statusLabel = (status) => {
  return (
    {
      pending: '待执行',
      running: '执行中',
      analyzing: '分析中',
      pass: '通过',
      fail: '失败',
      error: '错误',
      cancelled: '已取消'
    }[status] || '未知'
  )
}

const expandAll = () => results.value.forEach(r => (r.expanded = true))
const collapseAll = () => results.value.forEach(r => (r.expanded = false))

// 将单用例执行结果映射为与单执行对话框一致的 keyDecisions 步骤格式
const toKeyDecisions = (r) => {
  const steps = []
  if (r.depCount > 0) {
    steps.push({
      type: 'success',
      text: '依赖分析完成',
      summary: `发现 ${r.depCount} 个接口需要执行`,
      detail: null
    })
  }
  r.results.forEach((d) => {
    const details = []
    if (d.method && d.url) details.push(`请求: ${d.method} ${d.url}`)
    if (d.request) {
      try {
        const reqData = typeof d.request === 'string' ? JSON.parse(d.request) : d.request
        if (reqData && Object.keys(reqData).length > 0) {
          details.push(`参数: ${JSON.stringify(reqData, null, 2)}`)
        }
      } catch {
        if (d.request) details.push(`参数: ${d.request}`)
      }
    }
    if (d.response) {
      try {
        const respData = typeof d.response === 'string' ? JSON.parse(d.response) : d.response
        details.push(`响应: ${JSON.stringify(respData, null, 2)}`)
      } catch {
        if (d.response) details.push(`响应: ${d.response}`)
      }
    }
    if (!d.success && d.error) details.push(`错误: ${d.error}`)
    steps.push({
      type: d.success ? 'success' : 'warning',
      text: d.api_name || '接口调用',
      summary: `${d.method || ''} ${d.status_code ? '→ ' + d.status_code : ''} ${d.duration_ms ? '(' + d.duration_ms + 'ms)' : ''}`.trim(),
      detail: details.length ? details.join('\n') : null
    })
  })
  return steps
}

const onOpen = () => {
  results.value = props.cases.map(c => ({
    id: c.id,
    name: c.name || '用例#' + c.id,
    testpoint: c.testpoint || null,
    status: 'pending',
    logs: '',
    thinking: '',
    results: [],
    depCount: 0,
    success: 0,
    total: 0,
    duration: 0,
    startTime: 0,
    expanded: false,
    analyzing: false,
    failureAnalysis: null
  }))
  cancelled.value = false
  running.value = false
  elapsedMs.value = 0
  activeFilter.value = 'all'
  activeControllers.length = 0
  nextTick(() => start())
}

const start = async () => {
  if (running.value) return
  if (!props.cases.length) return
  running.value = true
  cancelled.value = false
  startTime.value = Date.now()
  const items = results.value

  let cursor = 0
  // 工作池：同时最多 concurrency 个用例在跑
  const worker = async () => {
    while (cursor < items.length) {
      const idx = cursor++
      if (cancelled.value) break
      await runOne(items[idx])
      elapsedMs.value = Date.now() - startTime.value
    }
  }
  const limit = Math.max(1, Math.min(concurrency.value || 1, items.length))
  const pool = []
  for (let w = 0; w < limit; w++) pool.push(worker())
  await Promise.all(pool)
  running.value = false
  if (!cancelled.value) {
    emit('refresh')
    // 执行完成提示
    ElMessage.success(`批量执行完成：通过 ${passCount.value} 个，失败 ${failCount.value} 个${errorCount.value ? `，错误 ${errorCount.value} 个` : ''}`)
  }
}

const runOne = (r) =>
  new Promise((resolve) => {
    r.status = 'running'
    r.logs = ''
    r.thinking = ''
    r.results = []
    r.depCount = 0
    r.success = 0
    r.total = 0
    r.duration = 0
    r.startTime = Date.now()
    r.expanded = true

    const onMessage = (event) => {
      const t = event.type
      const d = event.data || {}
      if (t === 'step') {
        const msg = d.message || ''
        r.logs += `▶ ${msg}\n`
        r.thinking += msg + '\n'
      } else if (t === 'dependency') {
        const runList = d.run_list || []
        r.depCount = runList.length
        r.logs += `\n📋 依赖分析完成，共 ${runList.length} 个接口待执行\n\n`
      } else if (t === 'result') {
        const icon = d.success ? '✓' : '✗'
        r.logs += `  ${icon} ${d.api_name || '接口'}\n`
        r.results.push(d)
        if (!d.success && d.error) r.logs += `    错误: ${d.error}\n`
      } else if (t === 'report') {
        const rep = d || {}
        const isPass = rep.success === rep.total && rep.total > 0
        r.success = rep.success || 0
        r.total = rep.total || 0
        r.duration = Date.now() - r.startTime
        r.logs += `\n━━━━━━━━━━━━━━━━━━━━━━\n`
        r.logs += `执行完成，成功: ${r.success}/${r.total}，耗时 ${r.duration}ms\n`
        if (isPass) {
          r.status = 'pass'
          r.expanded = false
          finish()
        } else if (r.results.length > 0) {
          // 失败：触发失败原因分析（第二个 SSE 流），分析完成后再收尾
          r.status = 'analyzing'
          r.analyzing = true
          startFailureAnalysis(r)
        } else {
          r.status = 'fail'
          r.expanded = true
          finish()
        }
      } else if (t === 'error') {
        r.status = 'error'
        r.logs += `\n❌ 错误: ${d.message || '执行失败'}\n`
      } else if (t === 'chunk') {
        r.thinking += d.content || ''
      }
    }

    let ctrl = null
    let done = false
    const finish = () => {
      if (done) return
      done = true
      const i = activeControllers.indexOf(ctrl)
      if (i >= 0) activeControllers.splice(i, 1)
      resolve()
    }

    const onError = (err) => {
      r.status = 'error'
      r.logs += `\n❌ 执行失败: ${err?.error || err?.message || '未知错误'}\n`
      finish()
    }

    const onComplete = () => {
      if (r.status === 'running') {
        r.status = r.total > 0 ? (r.success === r.total ? 'pass' : 'fail') : 'error'
        r.duration = Date.now() - r.startTime
      }
      // 通过的用例执行后自动收起，失败/错误保持展开便于排查
      if (r.status === 'pass') r.expanded = false
      // 失败分析中(analyzing)由分析流结束后再 finish，避免提前收尾
      if (r.status !== 'analyzing') finish()
    }

    // 失败用例：调用校验接口获取 AI 失败原因分析（与单执行对话框一致的第二个 SSE 流）
    const startFailureAnalysis = (r) => {
      r.logs += '\n🔍 正在进行失败原因分析...\n'
      const vctrl = apiTestCaseApi.validateCaseStream(
        r.id,
        r.results,
        (ev) => {
          const ed = ev.data || {}
          if (ev.type === 'chunk') {
            r.thinking += ed.content || ''
          } else if (ev.type === 'result') {
            if (ed.failure_analysis) {
              r.failureAnalysis = ed.failure_analysis
              r.logs += `📌 失败原因: ${ed.failure_analysis.root_cause || ''}\n`
            }
          }
        },
        (err) => {
          r.logs += `\n⚠️ 失败分析失败: ${err?.message || '未知错误'}\n`
        },
        () => {
          r.analyzing = false
          r.status = 'fail'
          r.expanded = true
          const i = activeControllers.indexOf(vctrl)
          if (i >= 0) activeControllers.splice(i, 1)
          finish()
        }
      )
      activeControllers.push(vctrl)
    }

    ctrl = apiTestCaseApi.executeCaseStream(
      r.id,
      props.environmentId,
      onMessage,
      onError,
      onComplete
    )
    activeControllers.push(ctrl)
  })

const cancel = () => {
  cancelled.value = true
  activeControllers.slice().forEach(c => c && c.abort && c.abort())
  activeControllers.length = 0
  results.value.forEach(r => {
    if (r.status === 'running' || r.status === 'pending') r.status = 'cancelled'
  })
  running.value = false
  elapsedMs.value = Date.now() - startTime.value
  emit('refresh')
}

// ============ 报告导出 ============
const pad2 = (n) => String(n).padStart(2, '0')
const nowStamp = () => {
  const d = new Date()
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
}
const fileTs = () => new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')

const buildSummary = () => ({
  total: results.value.length,
  pass: passCount.value,
  fail: failCount.value,
  error: errorCount.value,
  totalMs: results.value.reduce((s, r) => s + (r.duration || 0), 0)
})

const downloadFile = (filename, content, mime) => {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

const exportMarkdown = () => {
  const sum = buildSummary()
  const L = []
  L.push('# 接口测试批量执行报告', '')
  L.push(`- 生成时间：${nowStamp()}`)
  L.push(`- 用例总数：${sum.total}`)
  L.push(`- 通过：${sum.pass} ｜ 失败：${sum.fail} ｜ 错误：${sum.error}`)
  L.push(`- 总耗时：${(sum.totalMs / 1000).toFixed(1)}s`, '')
  L.push('## 汇总', '')
  L.push('| # | 用例 | 测试点 | 状态 | 成功/总数 | 耗时 |')
  L.push('|---|------|--------|------|-----------|------|')
  results.value.forEach((r, i) => {
    L.push(
      `| ${i + 1} | ${r.name} | ${r.testpoint || ''} | ${statusLabel(r.status)} | ${r.success}/${r.total} | ${(r.duration / 1000).toFixed(1)}s |`
    )
  })
  L.push('', '## 详细结果', '')
  results.value.forEach((r, i) => {
    L.push(`### ${i + 1}. ${r.name}${r.testpoint ? ' - ' + r.testpoint : ''}`)
    L.push(`- 状态：${statusLabel(r.status)}`)
    L.push(`- 成功/总数：${r.success}/${r.total}`)
    L.push(`- 耗时：${(r.duration / 1000).toFixed(1)}s`)
    if (r.depCount > 0) L.push(`- 依赖分析：发现 ${r.depCount} 个接口`)
    if (r.results && r.results.length) {
      L.push('', '#### 接口执行')
      r.results.forEach((d) => {
        const icon = d.success ? '✓' : '✗'
        L.push(
          `- [${icon}] ${d.method || ''} ${d.url || d.api_name || ''}${d.status_code ? ' → ' + d.status_code : ''}${d.duration_ms ? ' (' + d.duration_ms + 'ms)' : ''}`
        )
        if (!d.success && d.error) L.push(`  - 错误：${d.error}`)
      })
    }
    if (r.failureAnalysis) {
      const fa = r.failureAnalysis
      const rc = fa.root_cause || fa.rootCause || ''
      const aff = fa.affected_interfaces || fa.affectedInterfaces || []
      const stepsArr = fa.debug_steps || fa.debugSteps || []
      const sugg = fa.suggestions || []
      L.push('', '#### 失败原因分析')
      if (rc) L.push(`- 根本原因：${rc}`)
      if (aff.length) L.push(`- 影响接口：${aff.join('、')}`)
      if (stepsArr.length) {
        L.push('- 排查步骤：')
        stepsArr.forEach((s, k) => L.push(`  ${k + 1}. ${s}`))
      }
      if (sugg.length) {
        L.push('- 修改建议：')
        sugg.forEach((s) => L.push(`  - ${s.type || '建议'}：${s.description}`))
      }
    }
    L.push('')
  })
  return L.join('\n')
}

const exportJson = () => {
  const sum = buildSummary()
  return JSON.stringify(
    {
      generated_at: nowStamp(),
      summary: {
        total: sum.total,
        pass: sum.pass,
        fail: sum.fail,
        error: sum.error,
        total_duration_ms: sum.totalMs
      },
      cases: results.value.map((r, i) => ({
        index: i + 1,
        id: r.id,
        name: r.name,
        testpoint: r.testpoint,
        status: r.status,
        success: r.success,
        total: r.total,
        duration_ms: r.duration,
        dep_count: r.depCount,
        results: r.results,
        failure_analysis: r.failureAnalysis
      }))
    },
    null,
    2
  )
}

const escapeHtml = (s) =>
  String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const exportHtml = () => {
  const sum = buildSummary()
  const ts = nowStamp()
  let html =
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>接口测试批量执行报告</title>'
  html +=
    '<style>body{font-family:-apple-system,Segoe UI,Roboto,"Microsoft YaHei",sans-serif;margin:0;padding:24px;color:#1f2329;background:#f7f8fa;}'
  html +=
    '.wrap{max-width:960px;margin:0 auto;background:#fff;padding:24px;border-radius:8px;border:0.5px solid #e5e6eb;}'
  html +=
    'h1{font-size:20px;margin:0 0 16px;}h2{font-size:16px;margin:24px 0 12px;border-left:3px solid #185fa5;padding-left:8px;}h3{font-size:14px;margin:18px 0 8px;}'
  html +=
    '.meta{color:#646a73;font-size:13px;line-height:1.8;}table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0;}'
  html +=
    'th,td{border:0.5px solid #e5e6eb;padding:8px 10px;text-align:left;}th{background:#f7f8fa;font-weight:500;}'
  html +=
    '.ok{color:#2ba471;}.bad{color:#e5484d;}.case{border:0.5px solid #e5e6eb;border-left:3px solid #dcdfe6;border-radius:6px;padding:12px 14px;margin:10px 0;}'
  html +=
    '.case.pass{border-left-color:#2ba471;}.case.fail{border-left-color:#e5484d;}.case.error{border-left-color:#e5484d;}'
  html +=
    '.api{font-family:Consolas,Menlo,monospace;font-size:12px;background:#f7f8fa;padding:6px 8px;margin:4px 0;border-radius:4px;}'
  html +=
    '.fa{background:#fdf6ec;border:0.5px solid #f3d9a8;border-radius:6px;padding:10px 12px;margin-top:8px;}.rc{color:#e5484d;font-weight:600;}'
  html +=
    '.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;}.badge.pass{background:#eaf6ee;color:#2ba471;}.badge.fail{background:#fdeced;color:#e5484d;}.badge.error{background:#fdeced;color:#e5484d;}</style></head><body><div class="wrap">'
  html += '<h1>接口测试批量执行报告</h1>'
  html += `<div class="meta">生成时间：${ts}<br>用例总数：${sum.total} ｜ 通过：${sum.pass} ｜ 失败：${sum.fail} ｜ 错误：${sum.error} ｜ 总耗时：${(sum.totalMs / 1000).toFixed(1)}s</div>`
  html += '<h2>汇总</h2><table><thead><tr><th>#</th><th>用例</th><th>测试点</th><th>状态</th><th>成功/总数</th><th>耗时</th></tr></thead><tbody>'
  results.value.forEach((r, i) => {
    html += `<tr><td>${i + 1}</td><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.testpoint || '')}</td><td><span class="badge ${r.status}">${statusLabel(r.status)}</span></td><td>${r.success}/${r.total}</td><td>${(r.duration / 1000).toFixed(1)}s</td></tr>`
  })
  html += '</tbody></table><h2>详细结果</h2>'
  results.value.forEach((r, i) => {
    html += `<div class="case ${r.status}"><h3>${i + 1}. ${escapeHtml(r.name)}${r.testpoint ? ' - ' + escapeHtml(r.testpoint) : ''}</h3>`
    html += `<div class="meta">状态：${statusLabel(r.status)} ｜ 成功/总数：${r.success}/${r.total} ｜ 耗时：${(r.duration / 1000).toFixed(1)}s${r.depCount > 0 ? ' ｜ 依赖接口：' + r.depCount : ''}</div>`
    if (r.results && r.results.length) {
      html += '<div style="margin-top:8px">'
      r.results.forEach((d) => {
        const cls = d.success ? 'ok' : 'bad'
        const icon = d.success ? '✓' : '✗'
        html += `<div class="api"><span class="${cls}">${icon}</span> ${escapeHtml((d.method || '') + ' ' + (d.url || d.api_name || ''))}${d.status_code ? ' → ' + d.status_code : ''}${d.duration_ms ? ' (' + d.duration_ms + 'ms)' : ''}`
        if (!d.success && d.error) html += `<div class="bad" style="padding-left:18px">错误：${escapeHtml(d.error)}</div>`
        html += '</div>'
      })
      html += '</div>'
    }
    if (r.failureAnalysis) {
      const fa = r.failureAnalysis
      const rc = fa.root_cause || fa.rootCause || ''
      const aff = fa.affected_interfaces || fa.affectedInterfaces || []
      const stepsArr = fa.debug_steps || fa.debugSteps || []
      const sugg = fa.suggestions || []
      html += '<div class="fa"><div style="font-weight:600;color:#e6a23c;margin-bottom:6px">⚠ 失败原因分析</div>'
      if (rc) html += `<div>根本原因：<span class="rc">${escapeHtml(rc)}</span></div>`
      if (aff.length) html += `<div>影响接口：${escapeHtml(aff.join('、'))}</div>`
      if (stepsArr.length) {
        html += '<div style="margin-top:6px">排查步骤：</div><ol>'
        stepsArr.forEach((s) => (html += `<li>${escapeHtml(s)}</li>`))
        html += '</ol>'
      }
      if (sugg.length) {
        html += '<div style="margin-top:6px">修改建议：</div>'
        sugg.forEach((s) => (html += `<div>· ${escapeHtml((s.type || '建议') + '：' + (s.description || ''))}</div>`))
      }
      html += '</div>'
    }
    html += '</div>'
  })
  html += '</div></body></html>'
  return html
}

const handleExport = (format) => {
  if (!results.value.length) return
  const ts = fileTs()
  if (format === 'markdown') {
    downloadFile(`apitest-report-${ts}.md`, exportMarkdown(), 'text/markdown')
  } else if (format === 'json') {
    downloadFile(`apitest-report-${ts}.json`, exportJson(), 'application/json')
  } else if (format === 'html') {
    downloadFile(`apitest-report-${ts}.html`, exportHtml(), 'text/html')
  }
  ElMessage.success('报告已导出')
}

// 关闭时若仍在运行则中断
watch(
  () => props.visible,
  (val) => {
    if (!val && running.value) {
      cancel()
    }
  }
)
</script>

<style scoped>
.batch-exec {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 220px;
}

/* 统计条 */
.stat-strip {
  display: flex;
  align-items: stretch;
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-radius: 8px;
  overflow: hidden;
}

.stat-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-width: 64px;
  padding: 10px 6px;
}

.stat-num {
  font-size: 22px;
  font-weight: 500;
  line-height: 1.1;
  color: #1f2329;
}

.stat-num i {
  font-size: 12px;
  font-style: normal;
  font-weight: 400;
  margin-left: 1px;
  color: #8f959e;
}

.stat-cap {
  font-size: 12px;
  color: #8f959e;
  margin-top: 2px;
}

.stat-divider {
  width: 0.5px;
  background: #e5e6eb;
  margin: 8px 0;
}

.stat-spacer {
  flex: 0 0 8px;
}

.stat-block.running .stat-num { color: #185fa5; }
.stat-block.success .stat-num { color: #2ba471; }
.stat-block.danger .stat-num { color: #e5484d; }
.stat-block.warn .stat-num { color: #b9760a; }

/* 进度条 */
.progress-bar {
  height: 4px;
  background: #e5e6eb;
  border-radius: 2px;
  overflow: hidden;
  margin: 12px 0;
}

.progress-fill {
  height: 100%;
  background: #2ba471;
  transition: width 0.3s ease;
}

.progress-fill.fail {
  background: #e5484d;
}

/* 工具栏 */
.tool-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-tabs {
  display: flex;
  gap: 20px;
  border-bottom: 0.5px solid #e5e6eb;
  flex: 1;
  min-width: 0;
}

.filter-tab {
  padding: 8px 0;
  font-size: 13px;
  color: #646a73;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -0.5px;
  white-space: nowrap;
}

.filter-tab:hover {
  color: #1f2329;
}

.filter-tab.active {
  color: #1f2329;
  border-bottom-color: #185fa5;
}

.tool-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.list-count {
  font-size: 12px;
  color: #8f959e;
  white-space: nowrap;
}

/* 用例列表 */
.case-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100vh - 260px);
  min-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}

.case-card {
  background: #fff;
  border: 0.5px solid #e5e6eb;
  border-left: 3px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.case-card.is-expanded {
  border-color: #d0d3d9;
}

.case-card.pass { border-left-color: #2ba471; }
.case-card.fail { border-left-color: #e5484d; }
.case-card.error { border-left-color: #e5484d; }
.case-card.running { border-left-color: #185fa5; }
.case-card.analyzing { border-left-color: #185fa5; }
.case-card.cancelled {
  border-left-color: #c0c4cc;
  opacity: 0.7;
}

.case-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
}

.case-index {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef0f3;
  color: #646a73;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 500;
}

.case-title {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.case-name {
  font-size: 13px;
  color: #1f2329;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  flex-shrink: 0;
}

.case-status.pending { background: #f4f4f5; color: #8f959e; }
.case-status.running,
.case-status.analyzing { background: #e6f1fb; color: #185fa5; }
.case-status.pass { background: #eaf6ee; color: #2ba471; }
.case-status.fail,
.case-status.error { background: #fdeced; color: #e5484d; }
.case-status.cancelled { background: #f4f4f5; color: #8f959e; }

.case-mini-spinner {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border: 2px solid #185fa5;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.case-steps,
.case-duration {
  font-size: 12px;
  color: #8f959e;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.case-toggle {
  color: #c0c4cc;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.case-toggle.rotated {
  transform: rotate(180deg);
}

.case-report {
  border-top: 0.5px solid #e5e6eb;
  padding: 12px 14px;
  max-height: 48vh;
  overflow-y: auto;
}

.empty-hint {
  text-align: center;
  color: #8f959e;
  font-size: 13px;
  padding: 24px 0;
}

/* 底部栏 */
.batch-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.concurrency-label {
  font-size: 13px;
  color: #646a73;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-list::-webkit-scrollbar {
  width: 4px;
}

.case-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}

.case-report::-webkit-scrollbar {
  width: 4px;
}

.case-report::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 2px;
}
</style>
