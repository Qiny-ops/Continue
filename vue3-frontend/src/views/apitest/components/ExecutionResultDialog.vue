<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="执行结果"
    width="800px"
    destroy-on-close
  >
    <div class="result-content">
      <div v-if="resultData?.error" class="error-section">
        <el-alert type="error" :title="resultData.error.message || '执行出错'" show-icon />
      </div>

      <div v-if="resultData?.report" class="report-section">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="执行结果">
            <el-tag :type="resultData.report.success ? 'success' : 'danger'">
              {{ resultData.report.success ? '通过' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总耗时">
            {{ resultData.report.total ? `${resultData.report.total}ms` : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="步骤数">
            {{ resultData.steps?.length || 0 }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="steps-section">
        <h4>执行步骤</h4>
        <el-table :data="resultData?.steps || []" border size="small">
          <el-table-column prop="run_num" label="序号" width="80" />
          <el-table-column prop="api_name" label="接口" min-width="150" />
          <el-table-column label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                {{ row.success ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="duration_ms" label="耗时" width="100">
            <template #default="{ row }">
              {{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="状态码" width="100">
            <template #default="{ row }">
              {{ row.status_code || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewStepDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="resultData?.logs?.length" class="logs-section">
        <h4>执行日志</h4>
        <div class="log-content">
          <pre>{{ resultData.logs.join('\n') }}</pre>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="stepDetailVisible"
      title="步骤详情"
      width="600px"
      append-to-body
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="接口名称">{{ stepDetail?.api_name }}</el-descriptions-item>
        <el-descriptions-item label="URL">{{ stepDetail?.api_url }}</el-descriptions-item>
        <el-descriptions-item label="方法">{{ stepDetail?.method }}</el-descriptions-item>
        <el-descriptions-item label="状态码">{{ stepDetail?.status_code }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ stepDetail?.duration_ms }}ms</el-descriptions-item>
      </el-descriptions>

      <div class="detail-section">
        <h5>请求参数</h5>
        <pre class="code-block">{{ JSON.stringify(stepDetail?.request || {}, null, 2) }}</pre>
      </div>

      <div class="detail-section">
        <h5>响应数据</h5>
        <pre class="code-block">{{ JSON.stringify(stepDetail?.response || {}, null, 2) }}</pre>
      </div>
    </el-dialog>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: Boolean,
  resultData: Object
})

defineEmits(['update:modelValue'])

const stepDetailVisible = ref(false)
const stepDetail = ref(null)

const viewStepDetail = (row) => {
  stepDetail.value = row
  stepDetailVisible.value = true
}
</script>

<style scoped>
.result-content {
  max-height: 60vh;
  overflow: auto;
}

.error-section {
  margin-bottom: 16px;
}

.report-section {
  margin-bottom: 16px;
}

.steps-section h4,
.logs-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
}

.steps-section {
  margin-bottom: 16px;
}

.log-content {
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  padding: 12px;
  max-height: 200px;
  overflow: auto;
}

.log-content pre {
  margin: 0;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-section {
  margin-top: 16px;
}

.detail-section h5 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
}

.code-block {
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  padding: 12px;
  margin: 0;
  font-size: 12px;
  font-family: 'SF Mono', Monaco, monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow: auto;
}
</style>
