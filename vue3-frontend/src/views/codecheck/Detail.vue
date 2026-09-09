<template>
  <div class="cc-detail">
    <!-- 顶部条 -->
    <header class="topbar">
      <span class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </span>
      <div class="topbar-title">
        <span class="doc-title">代码检查</span>
        <span class="doc-no mono">ACR-{{ reportNo }}</span>
      </div>
      <div class="topbar-right">
        <el-button :loading="loading" @click="fetchDetail">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="handleSync">
          <el-icon><RefreshRight /></el-icon>
          同步结果
        </el-button>
        <el-button type="primary" plain :disabled="!task" :loading="exporting" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出 HTML
        </el-button>
      </div>
    </header>

    <!-- 内容区 -->
    <div class="cc-body" v-loading="loading">
      <template v-if="task">
        <!-- 进度条（执行中） -->
        <div v-if="['pending', 'running'].includes(task.status) && task.progress" class="progress-bar">
          <el-icon class="progress-icon"><Loading /></el-icon>
          <span class="progress-text">{{ task.progress }}</span>
        </div>

        <!-- 结论条（最顶部、最醒目） -->
        <section class="verdict-bar" :class="verdictClass">
          <div class="verdict-main">
            <span class="verdict-concl">{{ conclusionLabel(task.conclusion) }}</span>
            <span v-if="task.risk_level" class="verdict-risk">风险 {{ task.risk_level }} · {{ task.risk_score }}</span>
          </div>
          <div class="verdict-meta">
            <span>通过率 <b>{{ passRateText }}</b></span>
            <span>{{ passCount }} / {{ totalCount }} 通过</span>
            <span class="verdict-status" :class="task.status">{{ statusLabel(task.status) }}</span>
          </div>
        </section>

        <!-- 关键指标卡带 -->
        <section class="stat-grid">
          <div v-for="(s, i) in stats" :key="i" class="stat" :class="s.cls">
            <span class="l">{{ s.l }}</span>
            <span class="v">{{ s.v }}</span>
            <span v-if="s.sub" class="sub">{{ s.sub }}</span>
          </div>
        </section>

        <!-- 风险与建议（紧凑） -->
        <section class="risk-advice">
          <p class="ra-text">{{ verdictText }}</p>
          <div v-if="task.risk_reason" class="ra-risk" :class="{ high: task.risk_level === '高' }">{{ task.risk_reason }}</div>
          <div v-if="riskFiles.length" class="ra-files">
            <span class="ra-files-label">高风险文件</span>
            <div class="ra-file-list">
              <span v-for="f in riskFiles" :key="f" class="file-tag">{{ f }}</span>
            </div>
          </div>
          <ul v-if="topSuggestions.length" class="ra-list">
            <li v-for="(s, i) in topSuggestions" :key="i">{{ s }}</li>
          </ul>
          <div v-if="suggestions.length > topSuggestions.length" class="ra-more">另有 {{ suggestions.length - topSuggestions.length }} 条改进建议，见「导出 HTML」完整报告。</div>
        </section>

        <!-- 审计发现：可展开紧凑卡片 -->
        <section class="findings">
          <div class="findings-h">
            审计发现
            <span class="note">未通过 / 异常 {{ findings.length }} 条</span>
          </div>

          <article
            v-for="(item, idx) in findings"
            :key="item.case_no + '-' + idx"
            class="finding"
            :class="{ bad: item.result !== PASS_RESULT }"
          >
            <div class="f-head" @click="toggle(item, idx)">
              <span class="f-caret" :class="{ open: isOpen(item, idx) }"><el-icon :size="12"><ArrowDown /></el-icon></span>
              <span class="f-no">{{ pad(idx + 1) }}</span>
              <span class="f-title">
                <span class="mono f-case">{{ item.case_no }}</span>{{ item.testpoint || '未命名用例' }}
              </span>
              <span v-if="failureTypeOf(item)" class="type-badge">{{ failureTypeOf(item) }}</span>
              <span class="result-badge" :class="resultClass(item.result)">{{ item.result }}</span>
            </div>
            <div v-show="isOpen(item, idx)" class="f-body">
              <!-- 失败原因：整段强调，是审计发现的核心结论 -->
              <div class="f-reason" :class="{ fail: item.result !== PASS_RESULT }">
                <span class="rl">失败原因</span>
                <div class="rt">{{ failureReasonOf(item) }}</div>
              </div>
              <div v-if="evidenceOf(item)" class="f-item">
                <span class="fl">证据位置</span>
                <div class="ft">
                  <span v-for="(ev, i) in evidenceList(item)" :key="i" class="ev mono">{{ ev }}</span>
                </div>
              </div>
              <div v-if="item.expectation" class="f-item">
                <span class="fl">预期结果</span>
                <div class="ft">{{ item.expectation }}</div>
              </div>
              <div class="f-item">
                <span class="fl">校验证据</span>
                <div class="ft ev">{{ item.reason || '无校验理由' }}</div>
              </div>
            </div>
          </article>

          <div v-if="!findings.length" class="muted">本次检查未发现与预期不符的项。</div>

          <!-- 已通过项折叠 -->
          <div v-if="passedItems.length" class="passed-fold">
            <button class="fold-toggle" @click="passedFold = !passedFold">
              {{ passedFold ? '展开' : '收起' }} 已通过 {{ passedItems.length }} 条
              <el-icon :size="12"><ArrowDown :class="{ rot: !passedFold }" /></el-icon>
            </button>
            <div v-show="!passedFold" class="passed-list">
              <div v-for="r in passedItems" :key="r.id || r.case_no" class="passed-row">
                <span class="mono p-case">{{ r.case_no }}</span>
                <span class="p-title">{{ r.testpoint || '-' }}</span>
                <span class="result-badge pass">{{ r.result }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 检查信息 + 附件（折叠） -->
        <section class="attachments">
          <div class="att">
            <div class="att-h" @click="metaFold = !metaFold">
              <span>检查信息</span>
              <span class="ln">{{ metaFold ? '展开' : '收起' }}<el-icon :size="12"><ArrowDown :class="{ rot: !metaFold }" /></el-icon></span>
            </div>
            <table v-show="!metaFold" class="kv sm">
              <tbody>
                <tr>
                  <th>所属项目</th><td>{{ task.project_name || '-' }}</td>
                  <th>代码仓库</th><td class="mono brk">{{ task.repository_url || '-' }}</td>
                </tr>
                <tr>
                  <th>分支</th><td class="mono">{{ task.branch || '-' }}</td>
                  <th>Commit</th><td class="mono brk">{{ commitShort }}</td>
                </tr>
                <tr>
                  <th>变更文件</th><td>{{ changedFileCount }} 个</td>
                  <th>变更规模</th><td>+{{ additions }} / -{{ deletions }} 行</td>
                </tr>
                <tr>
                  <th>触发方式</th><td>{{ triggerLabel(task.trigger_source) }}</td>
                  <th>用例来源</th><td>{{ caseSourceLabel(task.case_source) }}</td>
                </tr>
                <tr>
                  <th>提交人</th><td>{{ task.commit_author || task.created_by_name || task.created_by || '-' }}</td>
                  <th>检查时间</th><td>{{ formatTime(task.created_at) }}</td>
                </tr>
                <tr>
                  <th>任务编号</th><td class="mono">#{{ task.id }}</td>
                  <th>服务任务</th><td class="mono brk">{{ task.service_task_id || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 代码变更 -->
          <div v-if="diffText" class="att">
            <div class="att-h" @click="diffFold = !diffFold">
              <span>代码变更</span>
              <span class="ln">{{ diffFold ? '展开' : '收起' }}<el-icon :size="12"><ArrowDown :class="{ rot: !diffFold }" /></el-icon></span>
            </div>
            <pre v-show="!diffFold" class="diff mono">{{ diffText }}</pre>
          </div>

          <!-- 门禁状态 -->
          <div class="att">
            <div class="att-h">门禁状态</div>
            <table class="kv sm">
              <tbody>
                <tr>
                  <th>门禁平台</th><td>{{ task.gate_provider || '未启用' }}</td>
                  <th>门禁状态</th>
                  <td>
                    <el-tag v-if="task.gate_state" size="small" :type="gateType(task.gate_state)">{{ task.gate_state }}</el-tag>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- 脚注 -->
        <footer class="cc-foot">
          本报告由代码检查平台自动生成，结论基于检查当次仓库快照（{{ commitShort }}）与用例版本，用例内容如有变更需重新检查。AI 校验结论可能存在偏差，重要变更请结合人工复核。
        </footer>
      </template>

      <!-- 空态 -->
      <div v-else-if="!loading" class="empty">
        <el-icon class="ei"><Document /></el-icon>
        <p>未找到该检查任务</p>
        <el-button size="small" @click="goBack">返回列表</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowDown, Refresh, RefreshRight, Loading, Document, Download } from '@element-plus/icons-vue'
import codeCheckApi from '@/api/modules/codecheck.js'

const PASS_RESULT = '通过'
const EVIDENCE_RE = /[\w./\\-]+\.(?:vue|js|ts|jsx|tsx|py|java|go|html|css|scss):\d+/g

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id)
const projectCode = computed(() => route.params.code || '')

const loading = ref(false)
const task = ref(null)
const diffFold = ref(true)
const metaFold = ref(true)
const passedFold = ref(true)
const openSet = ref(new Set())
const exporting = ref(false)

let pollTimer = null
let cancelled = false

/* ---------- 数据获取 ---------- */
async function fetchDetail() {
  const id = taskId.value
  if (cancelled || !id) return
  loading.value = true
  try {
    const data = await codeCheckApi.getTaskDetail(id)
    // 竞态保护：请求期间若已切换到其它任务，丢弃本次结果
    if (cancelled || taskId.value !== id) return
    task.value = data
    // 失败 / 异常用例默认展开，通过用例默认折叠
    openSet.value = new Set(findings.value.map((r, i) => `${r.case_no}-${i}`))
  } catch { /* 错误已统一处理 */ }
  finally {
    if (!cancelled && taskId.value === id) loading.value = false
  }
}

// 切换任务时重置状态并重新加载，避免显示上一个详情的缓存
watch(taskId, (nid, oid) => {
  if (nid === oid) return
  task.value = null
  openSet.value = new Set()
  diffFold.value = true
  metaFold.value = true
  passedFold.value = true
  stopPolling()
  fetchDetail()
  startPolling()
})

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    if (cancelled) return
    if (task.value && ['pending', 'running'].includes(task.value.status)) {
      fetchDetail()
    } else {
      stopPolling()
    }
  }, 3000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function handleSync() {
  if (!taskId.value) return
  try {
    await codeCheckApi.syncTask(taskId.value)
    ElMessage.success('已同步最新结果')
    await fetchDetail()
  } catch { /* 错误已统一处理 */ }
}

function goBack() {
  if (projectCode.value) {
    router.push({ name: 'project-codecheck', params: { code: projectCode.value } })
  } else {
    router.back()
  }
}

async function handleExport() {
  if (!taskId.value) return
  exporting.value = true
  try {
    const resp = await codeCheckApi.exportReport(taskId.value)
    const blob = resp instanceof Blob ? resp : resp.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ACR-${taskId.value}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('已导出 HTML 审计报告')
  } catch {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

/* ---------- 用例展开 ---------- */
function keyOf(item, idx) { return `${item.case_no}-${idx}` }
function isOpen(item, idx) { return openSet.value.has(keyOf(item, idx)) }
function toggle(item, idx) {
  const k = keyOf(item, idx)
  const s = new Set(openSet.value)
  if (s.has(k)) s.delete(k); else s.add(k)
  openSet.value = s
}

/* ---------- 统计 ---------- */
const results = computed(() => task.value?.results || [])
const totalCount = computed(() => task.value?.summary?.total ?? results.value.length)
const passCount = computed(() => task.value?.summary?.pass ?? 0)
const failCount = computed(() => task.value?.summary?.fail ?? 0)
const errorCount = computed(() => task.value?.summary?.error ?? 0)

const passRateText = computed(() => {
  const rate = task.value?.summary?.pass_rate
  if (rate === undefined || rate === null || rate === '') return '-'
  return typeof rate === 'number' ? `${rate}%` : rate
})

const findings = computed(() => results.value.filter(r => r.result !== PASS_RESULT))
const passedItems = computed(() => results.value.filter(r => r.result === PASS_RESULT))

/* ---------- 关键指标卡带 ---------- */
function dateShort(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
const stats = computed(() => {
  const t = task.value
  if (!t) return []
  return [
    { l: '通过率', v: passRateText.value, cls: '' },
    { l: '风险等级', v: t.risk_level || '未评估', sub: (t.risk_score != null && t.risk_score !== '') ? String(t.risk_score) : '', cls: t.risk_level === '高' ? 'bad' : '' },
    { l: '用例总数', v: String(totalCount.value), cls: '' },
    { l: '未通过', v: String(failCount.value), cls: failCount.value ? 'bad' : '' },
    { l: '异常', v: String(errorCount.value), cls: errorCount.value ? 'bad' : '' },
    { l: '检查时间', v: dateShort(t.created_at), cls: '' },
  ]
})

/* ---------- 失败原因 / 证据（兼容历史数据） ---------- */
function failureTypeOf(item) {
  if (item?.failure_type) return item.failure_type
  if (!item || item.result === PASS_RESULT) return ''
  return '其他'
}

function failureReasonOf(item) {
  const own = (item?.failure_reason || '').trim()
  if (own) return own
  const reason = (item?.reason || '').replace(/\s+/g, ' ').trim()
  if (!reason) return '未提供失败原因。'
  const m = reason.match(/^.{0,120}?[。；;!？?]/)
  const first = m ? m[0] : reason.slice(0, 120)
  return first.length < reason.length ? `${first}…` : first
}

function evidenceList(item) {
  const raw = (item?.evidence || '').trim()
  if (raw) return raw.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  const found = (item?.reason || '').match(EVIDENCE_RE)
  return found ? [...new Set(found)].slice(0, 6) : []
}
function evidenceOf(item) {
  return evidenceList(item).length > 0
}

/* ---------- 风险评估 ---------- */
const riskFiles = computed(() => {
  const files = task.value?.risk_files
  if (!Array.isArray(files)) return []
  return files.map(f => (typeof f === 'string' ? f : (f?.path || f?.file || ''))).filter(Boolean)
})

/* ---------- 代码变更 ---------- */
const diffInfo = computed(() => task.value?.diff_info || {})
const changedFileCount = computed(() => {
  const f = diffInfo.value.changed_files
  return Array.isArray(f) ? f.length : (diffInfo.value.changed_files_count ?? 0)
})
const additions = computed(() => diffInfo.value.additions ?? 0)
const deletions = computed(() => diffInfo.value.deletions ?? 0)
const commitAfter = computed(() => diffInfo.value.commit_after || task.value?.commit_sha || '-')
const commitShort = computed(() => String(commitAfter.value).slice(0, 8) || '-')
const diffText = computed(() => {
  const diff = task.value?.diff_info
  if (!diff) return ''
  if (typeof diff === 'string') return diff
  try { return JSON.stringify(diff, null, 2) } catch { return String(diff) }
})

/* ---------- 报告号 / 结论文案 / 改进建议 ---------- */
const reportNo = computed(() => {
  const d = new Date()
  const p = n => String(n).padStart(2, '0')
  const date = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`
  return `${date}-${String(task.value?.id ?? 0).padStart(4, '0')}`
})

const verdictClass = computed(() => task.value?.conclusion || 'none')

const failureTypeStats = computed(() => {
  const map = new Map()
  findings.value.forEach(r => {
    const t = failureTypeOf(r)
    if (t) map.set(t, (map.get(t) || 0) + 1)
  })
  return [...map.entries()].sort((a, b) => b[1] - a[1])
})
const failureTypeSummary = computed(() => {
  const stats = failureTypeStats.value
  return stats.length ? stats.map(([type, n]) => `${type} ${n} 条`).join('、') : ''
})
const verdictText = computed(() => {
  const c = task.value?.conclusion
  const cause = failureTypeSummary.value ? `未通过项按原因分布：${failureTypeSummary.value}。` : ''
  if (c === 'passed') return `本次检查共执行 ${totalCount.value} 条用例，全部通过，通过率 ${passRateText.value}，未发现功能实现与预期不符的情况。`
  if (c === 'blocked') return `本次检查因风险评估未达放行标准被阻断：共 ${totalCount.value} 条用例，未通过 ${failCount.value} 条、异常 ${errorCount.value} 条，通过率 ${passRateText.value}。${cause}`
  if (c === 'failed') return `本次检查未通过：共 ${totalCount.value} 条用例，未通过 ${failCount.value} 条、异常 ${errorCount.value} 条，通过率 ${passRateText.value}。${cause}各条失败原因详见下方「审计发现」。`
  return `本次检查共执行 ${totalCount.value} 条用例，通过 ${passCount.value} 条，通过率 ${passRateText.value}。${cause}`
})

const TYPE_ADVICE = {
  '功能未实现': '对应功能在代码中缺失，需补充实现后重新检查。',
  '实现与预期不符': '实现与用例预期存在具体差异（如跳转目标、提示文案、字段取值），需按预期逐项修正，而非仅保证主流程可用。',
  '部分实现': '仅实现了部分预期项，需对照「预期结果」补齐剩余条目。',
  '无法定位实现': '代码中未找到对应实现，需确认该功能是否已提交、是否位于本次检查的分支与仓库中。',
  '用例与代码库不匹配': '用例描述的业务与本次检查的仓库不匹配，需核对用例归属项目或重新选择正确的代码仓库。',
  '校验执行异常': 'AI 校验未获得有效结论，需确认校验服务（模型配额、鉴权）可用后重跑，避免漏判。',
}
const suggestions = computed(() => {
  const list = []
  failureTypeStats.value.forEach(([type, n]) => {
    const advice = TYPE_ADVICE[type] || '需人工复核该部分未通过项。'
    list.push(`【${type}】${n} 条 —— ${advice}`)
  })
  const failed = findings.value.filter(r => r.result === '失败')
  const errored = findings.value.filter(r => r.result !== '失败')
  if (failed.length) list.push(`共 ${failed.length} 条用例未通过，需按「审计发现」中的失败原因逐项修复，并在修复后重新提交代码检查。`)
  if (errored.length) list.push(`有 ${errored.length} 条用例未获得有效校验结论（执行异常），建议确认 AI 校验服务可用性后重跑，避免漏判。`)
  if (task.value?.risk_level === '高') list.push('本次变更风险等级为「高」，建议由资深开发人工复核后再合入主干。')
  if (riskFiles.value.length) list.push(`重点关注以下高风险文件：${riskFiles.value.slice(0, 5).join('、')}${riskFiles.value.length > 5 ? ' 等' : ''}。`)
  if (!failed.length && !errored.length) list.push('全部用例通过，未发现功能实现与预期不符的情况，可按流程合入。')
  list.push('若用例内容（步骤/预期）发生变更，需重新触发检查，历史报告结论不再适用。')
  return list
})
const topSuggestions = computed(() => suggestions.value.slice(0, 3))

/* ---------- 标签 / 文案 ---------- */
function pad(n) { return String(n).padStart(2, '0') }
function statusLabel(s) { return ({ pending: '等待执行', running: '执行中', completed: '已完成', failed: '失败' })[s] || s || '-' }
function conclusionLabel(c) { return ({ passed: '通过', blocked: '风险阻断', failed: '未通过' })[c] || '-' }
function resultClass(r) { return ({ '通过': 'pass', '失败': 'fail', '异常': 'error', '解析失败': 'warn', '解析错误': 'warn' })[r] || 'none' }
function triggerLabel(s) { return ({ manual: '手动触发', webhook: 'Webhook 自动触发' })[s] || s || '-' }
function caseSourceLabel(s) { return ({ platform: '平台用例库', file: 'Excel 文件导入', inline: '内联用例' })[s] || s || '-' }
function gateType(state) { return ({ success: 'success', error: 'danger', failure: 'danger', pending: 'info' })[state] || 'info' }
function formatTime(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

onMounted(() => {
  fetchDetail()
  startPolling()
})
onBeforeUnmount(() => {
  cancelled = true
  stopPolling()
})
</script>

<style scoped>
/* ============ MONO 语言：白底 + 黑灰阶 + 唯一失败红 ============ */
.cc-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--ink-50);
  color: var(--ink-900);
  font-size: 13px;
  line-height: 1.7;
}

/* 顶部条 */
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--ink-0);
  border-bottom: 1px solid var(--ink-200);
  flex-shrink: 0;
}
.back-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--ink-200);
  border-radius: 2px;
  cursor: pointer;
  color: var(--ink-600);
  transition: all 0.2s ease;
}
.back-btn:hover { background: var(--ink-100); color: var(--ink-900); }
.topbar-title { display: flex; flex-direction: column; gap: 1px; }
.doc-title { font-size: 15px; font-weight: 600; color: var(--ink-900); letter-spacing: 1px; }
.doc-no { font-size: 11px; color: var(--ink-400); letter-spacing: 1px; }
.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }
.topbar-right .el-button { border-radius: 2px; }

/* 内容区 */
.cc-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px;
  width: 100%;
  box-sizing: border-box;
}

/* 进度条 */
.progress-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; margin-bottom: 14px;
  background: var(--ink-100);
  border: 1px solid var(--ink-200);
  border-radius: 2px;
  color: var(--ink-800);
}
.progress-icon { color: var(--ink-600); }

/* 结论条 */
.verdict-bar {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  padding: 14px 18px;
  border: 1px solid var(--ink-200);
  border-left: 3px solid var(--ink-300);
  border-radius: 2px;
  margin-bottom: 14px;
  background: var(--ink-0);
}
.verdict-bar.failed { background: var(--fail-bg); border-left-color: var(--fail-line); }
.verdict-bar.blocked { background: var(--ink-100); border-left-color: var(--ink-800); }
.verdict-bar.passed { background: var(--ink-50); border-left-color: var(--ink-400); }
.verdict-bar.none { background: var(--ink-50); }

.verdict-main { display: flex; align-items: center; gap: 14px; }
.verdict-concl { font-size: 18px; font-weight: 600; letter-spacing: 1px; color: var(--ink-900); }
.verdict-bar.failed .verdict-concl { color: var(--fail); }
.verdict-risk {
  font-size: 12px; font-weight: 500;
  padding: 2px 10px;
  border: 1px solid var(--ink-300);
  border-radius: 2px;
  color: var(--ink-700);
}
.verdict-bar.failed .verdict-risk { border-color: var(--fail-line); color: var(--fail); }
.verdict-meta { display: flex; align-items: center; gap: 16px; font-size: 12px; color: var(--ink-600); }
.verdict-meta b { color: var(--ink-900); font-weight: 600; }
.verdict-status { padding: 1px 8px; border-radius: 2px; font-size: 12px; border: 1px solid var(--ink-300); color: var(--ink-700); }
.verdict-status.completed { border-color: var(--ink-400); color: var(--ink-800); }
.verdict-status.running { border-color: var(--ink-400); }
.verdict-status.failed { border-color: var(--fail-line); color: var(--fail); }

/* 关键指标卡带 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.stat {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 12px 6px;
  background: var(--ink-0);
  border: 1px solid var(--ink-200);
  border-radius: 2px;
}
.stat .l { font-size: 12px; color: var(--ink-500); white-space: nowrap; }
.stat .v { font-size: 22px; font-weight: 600; color: var(--ink-900); line-height: 1.1; }
.stat .sub { font-size: 11px; color: var(--ink-400); }
.stat.bad .v { color: var(--fail); }

/* 风险与建议（紧凑） */
.risk-advice {
  background: var(--ink-0);
  border: 1px solid var(--ink-200);
  border-radius: 2px;
  padding: 12px 16px;
  margin-bottom: 14px;
}
.ra-text {
  margin: 0;
  font-size: 12.5px; line-height: 1.8;
  color: var(--ink-700);
}
.ra-risk {
  margin-top: 8px;
  padding: 8px 10px;
  background: var(--ink-50);
  border-left: 2px solid var(--ink-900);
  border-radius: 2px;
  font-size: 12.5px; line-height: 1.6;
  color: var(--ink-800);
  white-space: pre-wrap;
}
.ra-risk.high { background: var(--fail-bg); border-left-color: var(--fail-line); color: var(--fail-ink); }
.ra-files { margin-top: 8px; display: flex; align-items: flex-start; flex-wrap: wrap; gap: 6px; }
.ra-files-label { font-size: 12px; color: var(--ink-400); line-height: 1.7; }
.ra-file-list { display: flex; flex-wrap: wrap; gap: 6px; }
.file-tag { padding: 2px 8px; background: var(--fail-bg); color: var(--fail); border: 1px solid var(--fail-line); border-radius: 2px; font-size: 12px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; word-break: break-all; }
.ra-list { margin: 8px 0 0; padding-left: 18px; font-size: 12px; line-height: 1.9; color: var(--ink-800); }
.ra-more { margin-top: 4px; font-size: 11px; color: var(--ink-400); }

/* 审计发现 */
.findings { margin-bottom: 14px; }
.findings-h {
  display: flex; align-items: center; gap: 8px;
  margin: 0 0 12px;
  font-size: 14px; font-weight: 600; color: var(--ink-900);
}
.findings-h .note { margin-left: auto; font-size: 12px; font-weight: 400; color: var(--ink-400); }

.finding {
  border: 1px solid var(--ink-200);
  border-radius: 2px;
  margin-bottom: 10px;
  background: var(--ink-0);
}
.finding.bad { border-left: 2px solid var(--fail-line); }
.f-head {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px;
  background: var(--ink-50);
  border-radius: 2px 2px 0 0;
  cursor: pointer;
}
.f-head:hover { background: var(--ink-100); }
.f-caret { color: var(--ink-500); transition: transform 0.2s ease; display: inline-flex; }
.f-caret.open { transform: rotate(180deg); }
.f-no { font-size: 12px; font-weight: 600; color: var(--ink-400); }
.f-title { flex: 1; min-width: 0; font-size: 13px; font-weight: 600; color: var(--ink-900); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.f-case { margin-right: 6px; font-weight: 400; color: var(--ink-500); }
.f-body { padding: 10px 12px; }

/* 失败原因：整段强调，失败红底 */
.f-reason {
  display: flex; gap: 12px;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: var(--ink-50);
  border-left: 2px solid var(--ink-900);
}
.f-reason.fail { background: var(--fail-bg); border-left-color: var(--fail-line); }
.f-reason.fail .rl { color: var(--fail); }
.f-reason.fail .rt { color: var(--fail-ink); }
.rl { width: 66px; flex-shrink: 0; font-size: 12px; font-weight: 600; color: var(--ink-900); }
.rt { flex: 1; min-width: 0; font-size: 12.5px; line-height: 1.75; white-space: pre-wrap; word-break: break-word; }

.type-badge {
  display: inline-block; padding: 1px 8px;
  border: 1px solid var(--ink-300); border-radius: 2px;
  font-size: 12px; line-height: 18px; white-space: nowrap; color: var(--ink-700);
}
.ev { display: inline-block; margin: 0 6px 4px 0; padding: 1px 6px; background: var(--ink-100); border-radius: 2px; font-size: 11.5px; color: var(--ink-600); }

.f-item { display: flex; gap: 12px; margin-bottom: 8px; }
.f-item:last-child { margin-bottom: 0; }
.fl { width: 66px; flex-shrink: 0; font-size: 12px; color: var(--ink-500); }
.ft { flex: 1; min-width: 0; font-size: 12px; line-height: 1.8; white-space: pre-wrap; word-break: break-word; color: var(--ink-800); }
.ft.ev { color: var(--ink-600); }

/* 结果徽标（MONO：通过=黑灰，失败/异常=红，无绿无黄） */
.result-badge {
  display: inline-block; padding: 1px 8px;
  border-radius: 2px; font-size: 12px; line-height: 18px; white-space: nowrap;
  border: 1px solid var(--ink-300); color: var(--ink-700);
}
.result-badge.pass { border-color: var(--ink-300); color: var(--ink-700); }
.result-badge.fail { background: var(--fail-bg); border-color: var(--fail-line); color: var(--fail); }
.result-badge.error { background: var(--fail-bg); border-color: var(--fail-line); color: var(--fail); }
.result-badge.warn { border-color: var(--ink-300); color: var(--ink-600); }
.result-badge.none { border-color: var(--ink-200); color: var(--ink-400); }

/* 已通过折叠 */
.passed-fold { margin-top: 10px; border-top: 1px dashed var(--ink-200); padding-top: 10px; }
.fold-toggle {
  display: inline-flex; align-items: center; gap: 4px;
  background: none; border: none; cursor: pointer;
  font-size: 12px; color: var(--ink-500);
}
.fold-toggle:hover { color: var(--ink-900); }
.rot { transform: rotate(180deg); transition: transform 0.2s ease; }
.passed-list { margin-top: 10px; }
.passed-row { display: flex; align-items: center; gap: 10px; padding: 4px 0; font-size: 12px; }
.p-case { color: var(--ink-400); }
.p-title { flex: 1; min-width: 0; color: var(--ink-700); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 附件 / 检查信息 */
.attachments { margin-bottom: 8px; }
.att { margin-bottom: 12px; }
.att:last-child { margin-bottom: 0; }
.att-h {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; font-weight: 600; color: var(--ink-700);
  margin-bottom: 8px;
  cursor: pointer;
}
.att-h .ln { display: inline-flex; align-items: center; gap: 4px; font-weight: 400; color: var(--ink-400); }
.att-h .ln:hover { color: var(--ink-900); }

/* 键值表 */
.kv { width: 100%; border-collapse: collapse; border: 1px solid var(--ink-200); }
.kv th, .kv td {
  padding: 8px 12px;
  border: 1px solid var(--ink-200);
  font-size: 12px; text-align: left; vertical-align: top;
}
.kv th {
  width: 92px;
  background: var(--ink-50);
  color: var(--ink-500);
  font-weight: 500; white-space: nowrap;
}
.kv.sm th { width: 80px; }
.kv td { color: var(--ink-800); }
.mono { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }
.brk { word-break: break-all; }
.muted { color: var(--ink-400); font-size: 12px; }

/* 代码变更 */
.diff {
  margin: 0; padding: 12px;
  background: var(--ink-50);
  border: 1px solid var(--ink-200);
  border-radius: 2px;
  font-size: 12px; line-height: 1.6; color: var(--ink-700);
  white-space: pre-wrap; word-break: break-all;
  max-height: 320px; overflow: auto;
}

/* 状态徽标（元数据用） */
.status-badge { display: inline-block; padding: 1px 8px; border-radius: 2px; font-size: 12px; border: 1px solid var(--ink-300); color: var(--ink-700); }
.status-badge.completed { border-color: var(--ink-400); color: var(--ink-800); }
.status-badge.failed { border-color: var(--fail-line); color: var(--fail); }
.status-badge.running { border-color: var(--ink-400); }

/* 脚注 */
.cc-foot {
  margin-top: 8px; padding-top: 16px;
  border-top: 1px solid var(--ink-200);
  font-size: 11px; line-height: 1.8; color: var(--ink-400);
}

/* 空态 */
.empty { padding: 80px 0; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.ei { font-size: 40px; color: var(--ink-400); }
.empty p { margin: 0; font-size: 13px; color: var(--ink-400); }

@media (max-width: 720px) {
  .stat-grid { grid-template-columns: repeat(3, 1fr); }
  .verdict-meta { width: 100%; }
}
</style>
