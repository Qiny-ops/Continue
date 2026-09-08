<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import codeCheckApi from '@/api/modules/codecheck.js'

const route = useRoute()
const router = useRouter()
const projectCode = computed(() => route.params.code)

const loading = ref(false)
const tasks = ref([])

const triggerVisible = ref(false)
const triggerForm = ref({
  repository_url: '',
  branch: '',
  commit_sha: '',
  case_source: 'platform',
  gate_enabled: false,
  gate: { provider: 'github', repo_ref: '', commit_sha: '', token: '' }
})

let cancelled = false
let pollTimer = null

async function fetchList() {
  if (cancelled) return
  loading.value = true
  try {
    const data = await codeCheckApi.getTasks()
    if (cancelled) return
    tasks.value = data || []
  } catch (e) {
    /* handled */
  } finally {
    if (!cancelled) loading.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    if (cancelled) return
    if (tasks.value.some(t => ['pending', 'running'].includes(t.status))) {
      fetchList()
    }
  }, 5000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

function statusType(s) {
  return ({ pending: 'info', running: 'warning', completed: 'success', failed: 'danger' })[s] || ''
}
function conclusionLabel(c) {
  return ({ passed: '通过', blocked: '风险阻断', failed: '未通过' })[c] || '-'
}
function conclusionType(c) {
  return ({ passed: 'success', blocked: 'warning', failed: 'danger' })[c] || 'info'
}

function openTrigger() {
  triggerForm.value = {
    repository_url: '', branch: '', commit_sha: '',
    case_source: 'platform', gate_enabled: false,
    gate: { provider: 'github', repo_ref: '', commit_sha: '', token: '' }
  }
  triggerVisible.value = true
}

async function doTrigger() {
  if (!triggerForm.value.repository_url) {
    ElMessage.warning('请填写仓库地址')
    return
  }
  const payload = {
    project_code: projectCode.value,
    repository_url: triggerForm.value.repository_url,
    branch: triggerForm.value.branch,
    commit_sha: triggerForm.value.commit_sha,
    case_source: triggerForm.value.case_source,
  }
  if (triggerForm.value.gate_enabled) {
    payload.gate = { ...triggerForm.value.gate, commit_sha: triggerForm.value.gate.commit_sha || triggerForm.value.commit_sha }
  }
  try {
    await codeCheckApi.triggerCheck(payload)
    ElMessage.success('已触发')
    triggerVisible.value = false
    fetchList()
  } catch (e) { /* */ }
}

function goDetail(row) {
  router.push({ name: 'project-codecheck-detail', params: { code: projectCode.value, id: row.id } })
}

onMounted(() => {
  fetchList()
  startPolling()
})
onBeforeUnmount(() => {
  cancelled = true
  stopPolling()
})
</script>

<template>
  <div class="codecheck-index">
    <div class="page-header">
      <h2>代码变更检查</h2>
      <el-button type="primary" @click="openTrigger">触发检查</el-button>
    </div>

    <el-table v-loading="loading" :data="tasks" stripe @row-click="goDetail" row-class-name="clickable">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="project_name" label="项目" />
      <el-table-column prop="repository_url" label="仓库" show-overflow-tooltip />
      <el-table-column prop="branch" label="分支" width="140" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="风险" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.risk_level" :type="row.risk_level === '高' ? 'danger' : row.risk_level === '中' ? 'warning' : 'info'">
            {{ row.risk_level }} ({{ row.risk_score }})
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="结论" width="100">
        <template #default="{ row }">
          <el-tag :type="conclusionType(row.conclusion)">{{ conclusionLabel(row.conclusion) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
    </el-table>

    <el-dialog v-model="triggerVisible" title="触发代码检查" width="600px">
      <el-form :model="triggerForm" label-width="100px">
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
          <el-form-item label="仓库标识">
            <el-input v-model="triggerForm.gate.repo_ref" :placeholder="triggerForm.gate.provider === 'github' ? 'owner/repo' : 'project id'" />
          </el-form-item>
          <el-form-item label="Token (可选)">
            <el-input v-model="triggerForm.gate.token" type="password" show-password />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="triggerVisible = false">取消</el-button>
        <el-button type="primary" @click="doTrigger">触发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.codecheck-index { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
:deep(.clickable) { cursor: pointer; }
</style>
