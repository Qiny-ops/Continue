<template>
  <div class="codecheck-page">
    <div class="codecheck-container">
      <!-- 标题栏 -->
      <div class="header-bar">
        <span class="page-title">代码检查</span>
        <div class="header-divider"></div>
        <span class="header-meta">共 <strong>{{ total }}</strong> 次检查</span>
        <div class="header-right">
          <span class="auto-refresh">
            <el-switch v-model="autoRefresh" size="small" />
            <span class="auto-refresh-label">自动刷新</span>
          </span>
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar-section">
        <div class="toolbar-left">
          <div class="search-box">
            <el-input
              v-model="searchQuery"
              placeholder="搜索仓库、分支、Commit..."
              clearable
              :prefix-icon="Search"
            />
          </div>
          <div class="filter-group">
            <el-select v-model="filterStatus" placeholder="状态" clearable class="filter-item">
              <el-option label="等待执行" value="pending" />
              <el-option label="执行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
            </el-select>
            <el-select v-model="filterRisk" placeholder="风险" clearable class="filter-item">
              <el-option label="高" value="高" />
              <el-option label="中" value="中" />
              <el-option label="低" value="低" />
            </el-select>
            <el-select v-model="filterConclusion" placeholder="结论" clearable class="filter-item">
              <el-option label="通过" value="passed" />
              <el-option label="风险阻断" value="blocked" />
              <el-option label="未通过" value="failed" />
            </el-select>
          </div>
        </div>
        <div class="toolbar-right">
          <el-button :loading="loading" @click="loadTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="openTrigger">
            <el-icon><Plus /></el-icon>
            触发检查
          </el-button>
        </div>
      </div>

      <!-- 表格区域 -->
      <div class="table-section">
        <el-table
          v-loading="loading"
          :data="tasks"
          style="width: 100%; height: 100%"
          empty-text="暂无代码检查记录"
          row-key="id"
          row-class-name="codecheck-row"
          @row-click="goDetail"
        >
          <el-table-column prop="id" label="ID" width="80" align="center">
            <template #default="{ row }">
              <span class="task-id">#{{ row.id }}</span>
            </template>
          </el-table-column>

          <el-table-column label="仓库" min-width="240">
            <template #default="{ row }">
              <div class="repo-cell">
                <el-icon class="repo-icon"><Connection /></el-icon>
                <span class="repo-name">{{ repoLabel(row.repository_url) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="分支" width="140">
            <template #default="{ row }">
              <span class="cell-text">{{ row.branch || '-' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="触发来源" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.trigger_source === 'webhook' ? 'warning' : 'info'">
                {{ triggerLabel(row.trigger_source) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <span class="status-badge" :class="row.status">{{ statusLabel(row.status) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="风险" width="130" align="center">
            <template #default="{ row }">
              <span v-if="row.risk_level" class="risk-badge" :class="riskClass(row.risk_level)">
                {{ row.risk_level }} · {{ row.risk_score }}
              </span>
              <span v-else class="cell-text">-</span>
            </template>
          </el-table-column>

          <el-table-column label="结论" width="110" align="center">
            <template #default="{ row }">
              <span class="conclusion-badge" :class="row.conclusion || 'none'">
                {{ conclusionLabel(row.conclusion) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="门禁" width="110" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.gate_provider" size="small" :type="gateType(row.gate_state)">
                {{ row.gate_provider }}
              </el-tag>
              <span v-else class="cell-text">-</span>
            </template>
          </el-table-column>

          <el-table-column label="创建时间" width="170">
            <template #default="{ row }">
              <span class="cell-text">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="90" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-cell">
                <el-tooltip content="查看详情" placement="top">
                  <span class="action-btn" @click.stop="goDetail(row)">
                    <el-icon><View /></el-icon>
                  </span>
                </el-tooltip>
                <el-tooltip content="同步结果" placement="top">
                  <span class="action-btn" @click.stop="handleSync(row)">
                    <el-icon><RefreshRight /></el-icon>
                  </span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>

          <template #empty>
            <div class="empty-state">
              <el-icon class="empty-icon"><Document /></el-icon>
              <p class="empty-text">暂无代码检查记录</p>
              <el-button type="primary" plain size="small" @click="openTrigger">触发检查</el-button>
            </div>
          </template>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-section">
        <div class="pagination-info">
          共 <strong>{{ total }}</strong> 次检查
          <span v-if="isFiltering" class="filter-hint">（已筛选）</span>
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

    <!-- 触发检查弹窗 -->
    <el-dialog v-model="triggerVisible" title="触发代码检查" width="600px" class="codecheck-dialog">
      <el-form :model="triggerForm" label-width="104px">
        <el-form-item label="仓库地址" required>
          <el-input v-model="triggerForm.repository_url" placeholder="https://github.com/owner/repo.git" />
        </el-form-item>
        <el-form-item label="分支">
          <el-input v-model="triggerForm.branch" placeholder="留空则拉取默认分支" />
        </el-form-item>
        <el-form-item label="Commit SHA">
          <el-input v-model="triggerForm.commit_sha" placeholder="可选" />
        </el-form-item>
        <el-form-item label="用例来源">
          <el-radio-group v-model="triggerForm.case_source">
            <el-radio value="platform">平台用例</el-radio>
            <el-radio value="file">Excel 文件</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="triggerForm.case_source === 'file'" label="用例文件名">
          <el-input v-model="triggerForm.test_case_file" placeholder="如 cases/login.xlsx" />
        </el-form-item>
        <el-form-item label="启用门禁">
          <el-switch v-model="triggerForm.gate_enabled" />
        </el-form-item>
        <template v-if="triggerForm.gate_enabled">
          <el-form-item label="门禁平台">
            <el-radio-group v-model="triggerForm.gate.provider">
              <el-radio value="github">GitHub</el-radio>
              <el-radio value="gitlab">GitLab</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="仓库标识" required>
            <el-input
              v-model="triggerForm.gate.repo_ref"
              :placeholder="triggerForm.gate.provider === 'github' ? 'owner/repo' : 'project id'"
            />
          </el-form-item>
          <el-form-item label="Token (可选)">
            <el-input v-model="triggerForm.gate.token" type="password" show-password />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="triggerVisible = false">取消</el-button>
        <el-button type="primary" :loading="triggering" @click="doTrigger">触发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, Plus, Refresh, RefreshRight, View, Connection, Document
} from '@element-plus/icons-vue'
import codeCheckApi from '@/api/modules/codecheck.js'

const props = defineProps({
  project: {
    type: Object,
    default: null
  }
})

const route = useRoute()
const router = useRouter()

const projectCode = computed(() => props.project?.code || route.params.code || '')

const loading = ref(false)
const tasks = ref([])
const total = ref(0)

const searchQuery = ref('')
const filterStatus = ref('')
const filterRisk = ref('')
const filterConclusion = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const autoRefresh = ref(true)

const triggerVisible = ref(false)
const triggering = ref(false)
const triggerForm = ref({
  repository_url: '',
  branch: '',
  commit_sha: '',
  case_source: 'platform',
  test_case_file: '',
  gate_enabled: false,
  gate: { provider: 'github', repo_ref: '', commit_sha: '', token: '' }
})

let cancelled = false
let pollTimer = null

const isFiltering = computed(() =>
  Boolean(searchQuery.value.trim() || filterStatus.value || filterRisk.value || filterConclusion.value)
)

async function loadTasks() {
  if (cancelled) return
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize.value }
    if (projectCode.value) params.project_code = projectCode.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRisk.value) params.risk_level = filterRisk.value
    if (filterConclusion.value) params.conclusion = filterConclusion.value

    const res = await codeCheckApi.getTasks(params)
    if (cancelled) return
    const list = Array.isArray(res) ? res : (res?.results || [])
    tasks.value = list
    total.value = Array.isArray(res) ? list.length : (res?.count ?? list.length)
  } catch {
    if (!cancelled) {
      tasks.value = []
      total.value = 0
    }
  } finally {
    if (!cancelled) loading.value = false
  }
}

function handlePageChange() {
  loadTasks()
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    if (cancelled || !autoRefresh.value) return
    if (tasks.value.some(t => ['pending', 'running'].includes(t.status))) {
      loadTasks()
    }
  }, 5000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

function repoLabel(url) {
  if (!url) return '-'
  return url.replace(/\.git$/, '').replace(/^https?:\/\//, '')
}

function triggerLabel(s) {
  return ({ manual: '手动', webhook: 'Webhook' })[s] || s || '-'
}

function statusLabel(s) {
  return ({ pending: '等待执行', running: '执行中', completed: '已完成', failed: '失败' })[s] || s || '-'
}

function conclusionLabel(c) {
  return ({ passed: '通过', blocked: '风险阻断', failed: '未通过' })[c] || '-'
}

function riskClass(level) {
  return ({ '高': 'high', '中': 'medium', '低': 'low' })[level] || ''
}

function gateType(state) {
  return ({ success: 'success', error: 'danger', failure: 'danger', pending: 'warning' })[state] || 'info'
}

function formatTime(v) {
  if (!v) return '-'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

function goDetail(row) {
  if (!row?.id) return
  router.push({ name: 'project-codecheck-detail', params: { code: projectCode.value, id: row.id } })
}

async function handleSync(row) {
  try {
    await codeCheckApi.syncTask(row.id)
    ElMessage.success('已同步最新结果')
    loadTasks()
  } catch { /* 错误已统一处理 */ }
}

function openTrigger() {
  triggerForm.value = {
    repository_url: '',
    branch: '',
    commit_sha: '',
    case_source: 'platform',
    test_case_file: '',
    gate_enabled: false,
    gate: { provider: 'github', repo_ref: '', commit_sha: '', token: '' }
  }
  triggerVisible.value = true
}

async function doTrigger() {
  if (!triggerForm.value.repository_url.trim()) {
    ElMessage.warning('请填写仓库地址')
    return
  }
  if (triggerForm.value.gate_enabled && !triggerForm.value.gate.repo_ref.trim()) {
    ElMessage.warning('启用门禁时仓库标识必填')
    return
  }
  if (triggerForm.value.case_source === 'file' && !triggerForm.value.test_case_file.trim()) {
    ElMessage.warning('请填写用例文件名')
    return
  }

  const payload = {
    project_code: projectCode.value,
    repository_url: triggerForm.value.repository_url.trim(),
    branch: triggerForm.value.branch.trim(),
    commit_sha: triggerForm.value.commit_sha.trim(),
    case_source: triggerForm.value.case_source,
  }
  if (triggerForm.value.case_source === 'file') {
    payload.test_case_file = triggerForm.value.test_case_file.trim()
  }
  if (triggerForm.value.gate_enabled) {
    payload.gate = {
      ...triggerForm.value.gate,
      commit_sha: triggerForm.value.gate.commit_sha || triggerForm.value.commit_sha
    }
  }

  triggering.value = true
  try {
    await codeCheckApi.triggerCheck(payload)
    ElMessage.success('已触发检查')
    triggerVisible.value = false
    currentPage.value = 1
    await loadTasks()
  } catch { /* 错误已统一处理 */ }
  finally {
    triggering.value = false
  }
}

let searchDebounceTimer = null
watch([searchQuery, filterStatus, filterRisk, filterConclusion], () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    currentPage.value = 1
    loadTasks()
  }, 300)
})

watch(autoRefresh, (val) => {
  if (val) startPolling()
  else stopPolling()
})

watch(() => projectCode.value, () => {
  currentPage.value = 1
  loadTasks()
})

onMounted(() => {
  loadTasks()
  startPolling()
})
onBeforeUnmount(() => {
  cancelled = true
  stopPolling()
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})
</script>

<style scoped>
.codecheck-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
}

.codecheck-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 标题栏 */
.header-bar {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-secondary);
  flex-shrink: 0;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-right: 4px;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border-primary);
  margin: 0 20px;
}

.header-meta {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.header-meta strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

.header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auto-refresh-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 工具栏 */
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

/* 表格 */
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

.table-section :deep(.el-table) {
  --el-table-border-color: var(--color-border-secondary);
  --el-table-header-bg-color: var(--color-bg-secondary);
}

.table-section :deep(.el-table__header-wrapper th) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 13px;
}

.table-section :deep(.codecheck-row) {
  cursor: pointer;
}

.task-id {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.repo-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.repo-icon {
  color: var(--color-text-tertiary);
  font-size: 14px;
  flex-shrink: 0;
}

.repo-name {
  font-size: 13px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 状态徽标 */
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  line-height: 18px;
  border: 1px solid transparent;
}

.status-badge.pending {
  background: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
  border-color: var(--color-border-primary);
}

.status-badge.running {
  background: var(--color-warning-light, #fdf6ec);
  color: var(--color-warning, #e6a23c);
  border-color: var(--color-warning-light, #fdf6ec);
}

.status-badge.completed {
  background: var(--color-success-light, #f0f9eb);
  color: var(--color-success, #67c23a);
  border-color: var(--color-success-light, #f0f9eb);
}

.status-badge.failed {
  background: var(--color-danger-light, #fef0f0);
  color: var(--color-danger, #f56c6c);
  border-color: var(--color-danger-light, #fef0f0);
}

/* 风险徽标 */
.risk-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  line-height: 18px;
}

.risk-badge.high {
  background: var(--color-danger-light, #fef0f0);
  color: var(--color-danger, #f56c6c);
}

.risk-badge.medium {
  background: var(--color-warning-light, #fdf6ec);
  color: var(--color-warning, #e6a23c);
}

.risk-badge.low {
  background: var(--color-success-light, #f0f9eb);
  color: var(--color-success, #67c23a);
}

/* 结论徽标 */
.conclusion-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  line-height: 18px;
}

.conclusion-badge.passed {
  background: var(--color-success-light, #f0f9eb);
  color: var(--color-success, #67c23a);
}

.conclusion-badge.blocked {
  background: var(--color-warning-light, #fdf6ec);
  color: var(--color-warning, #e6a23c);
}

.conclusion-badge.failed {
  background: var(--color-danger-light, #fef0f0);
  color: var(--color-danger, #f56c6c);
}

.conclusion-badge.none {
  color: var(--color-text-tertiary);
}

/* 操作列 */
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
  color: var(--color-primary);
}

/* 空状态 */
.empty-state {
  padding: 40px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-icon {
  font-size: 40px;
  color: var(--color-text-tertiary);
}

.empty-text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 分页 */
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
  color: var(--color-text-secondary);
}

.pagination-info strong {
  color: var(--color-text-primary);
}

.filter-hint {
  color: var(--color-primary);
}
</style>
