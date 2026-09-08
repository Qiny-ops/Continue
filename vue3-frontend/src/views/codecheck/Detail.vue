<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import codeCheckApi from '@/api/modules/codecheck.js'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id)

const loading = ref(false)
const task = ref(null)
let pollTimer = null
let cancelled = false

async function fetchDetail() {
  if (cancelled || !taskId.value) return
  loading.value = true
  try {
    const data = await codeCheckApi.getTaskDetail(taskId.value)
    if (cancelled) return
    task.value = data
  } catch (e) { /* */ }
  finally {
    if (!cancelled) loading.value = false
  }
}

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

function statusType(s) {
  return ({ pending: 'info', running: 'warning', completed: 'success', failed: 'danger' })[s] || ''
}
function resultType(s) {
  return ({ '通过': 'success', '失败': 'danger', '异常': 'danger', '解析失败': 'warning' })[s] || 'info'
}
function conclusionLabel(c) {
  return ({ passed: '通过', blocked: '风险阻断', failed: '未通过' })[c] || '-'
}
function conclusionType(c) {
  return ({ passed: 'success', blocked: 'warning', failed: 'danger' })[c] || 'info'
}
function riskType(l) {
  return ({ '高': 'danger', '中': 'warning', '低': 'success' })[l] || 'info'
}

function goBack() { router.back() }

onMounted(() => { fetchDetail(); startPolling() })
onBeforeUnmount(() => {
  cancelled = true
  stopPolling()
})
</script>

<template>
  <div class="codecheck-detail" v-loading="loading">
    <div class="header">
      <el-button @click="goBack">返回</el-button>
      <h2>代码检查详情 #{{ taskId }}</h2>
      <el-tag v-if="task" :type="statusType(task.status)">{{ task.status }}</el-tag>
    </div>

    <template v-if="task">
      <el-descriptions :column="2" border class="section">
        <el-descriptions-item label="项目">{{ task.project_name }}</el-descriptions-item>
        <el-descriptions-item label="仓库">{{ task.repository_url }}</el-descriptions-item>
        <el-descriptions-item label="分支">{{ task.branch || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Commit">{{ task.commit_sha || '-' }}</el-descriptions-item>
        <el-descriptions-item label="触发来源">{{ task.trigger_source }}</el-descriptions-item>
        <el-descriptions-item label="用例来源">{{ task.case_source }}</el-descriptions-item>
        <el-descriptions-item label="进度" :span="2">{{ task.progress || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结论">
          <el-tag :type="conclusionType(task.conclusion)">{{ conclusionLabel(task.conclusion) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="门禁">
          <el-tag v-if="task.gate_provider">{{ task.gate_provider }}: {{ task.gate_state || '-' }}</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="task.error" label="错误" :span="2">
          <span style="color:#f56c6c">{{ task.error }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <el-card class="section" header="风险评估">
        <template v-if="task.risk_level">
          <el-tag :type="riskType(task.risk_level)" size="large">{{ task.risk_level }} ({{ task.risk_score }})</el-tag>
          <div class="reason">{{ task.risk_reason }}</div>
          <div v-if="task.risk_files && task.risk_files.length" class="files">
            <strong>高风险文件：</strong>
            <el-tag v-for="f in task.risk_files" :key="f" type="danger" style="margin: 2px;">{{ f }}</el-tag>
          </div>
        </template>
        <el-empty v-else description="暂无风险评估" />
      </el-card>

      <el-card v-if="task.summary && task.summary.total" class="section" header="执行汇总">
        <div class="summary-grid">
          <div class="summary-item">
            <div class="label">总数</div>
            <div class="value">{{ task.summary.total }}</div>
          </div>
          <div class="summary-item pass">
            <div class="label">通过</div>
            <div class="value">{{ task.summary.pass }}</div>
          </div>
          <div class="summary-item fail">
            <div class="label">失败</div>
            <div class="value">{{ task.summary.fail }}</div>
          </div>
          <div class="summary-item error">
            <div class="label">异常</div>
            <div class="value">{{ task.summary.error }}</div>
          </div>
        </div>
        <div class="pass-rate">通过率：{{ task.summary.pass_rate }}</div>
      </el-card>

      <el-card v-if="task.results && task.results.length" class="section" header="用例结果">
        <el-table :data="task.results" stripe>
          <el-table-column prop="case_no" label="编号" width="100" />
          <el-table-column prop="testpoint" label="测试点" show-overflow-tooltip />
          <el-table-column label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="resultType(row.result)">{{ row.result }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="校验理由" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.codecheck-detail { padding: 16px; }
.header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section { margin-bottom: 16px; }
.reason { margin-top: 8px; color: #606266; white-space: pre-wrap; }
.files { margin-top: 8px; }
.pass-rate { margin-top: 12px; font-weight: 600; color: #67c23a; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.summary-item { padding: 12px; border: 1px solid #ebeef5; border-radius: 4px; text-align: center; }
.summary-item .label { font-size: 12px; color: #909399; }
.summary-item .value { font-size: 24px; font-weight: 600; margin-top: 4px; }
.summary-item.pass .value { color: #67c23a; }
.summary-item.fail .value { color: #f56c6c; }
.summary-item.error .value { color: #e6a23c; }
</style>
