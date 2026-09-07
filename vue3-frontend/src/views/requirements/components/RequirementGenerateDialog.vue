<template>
  <el-dialog
    :model-value="visible"
    title="从需求生成测试用例"
    width="640px"
    :close-on-click-modal="false"
    :close-on-press-escape="!generating"
    @update:model-value="handleVisibleUpdate"
  >
    <div class="generate-content">
      <el-form v-if="!generating && !completed" label-position="top">
        <el-form-item label="目标版本" required>
          <el-select v-model="targetVersion" placeholder="请选择目标版本" style="width: 100%">
            <el-option
              v-for="v in versions"
              :key="v.id"
              :label="v.name"
              :value="v.id"
            >
              <span>{{ v.name }}</span>
              <el-tag v-if="v.is_default" type="success" size="small" style="margin-left: 8px;">默认</el-tag>
            </el-option>
          </el-select>
        </el-form-item>

        <div class="info-box">
          <el-icon><InfoFilled /></el-icon>
          <span v-if="requirementIds.length > 1">
            将从选中的 {{ requirementIds.length }} 个需求批量生成测试用例
          </span>
          <span v-else>
            将从该需求生成测试用例
          </span>
        </div>
      </el-form>

      <div v-if="generating" class="generating-box">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p class="generating-text">正在生成测试用例，请稍候...</p>
      </div>

      <div v-if="completed" class="result-box">
        <el-icon class="result-icon" :class="{ success: result.created_count > 0, error: result.created_count === 0 }">
          <CircleCheck v-if="result.created_count > 0" />
          <CircleClose v-else />
        </el-icon>
        <div class="result-stats">
          <div class="stat-item">
            <span class="stat-value success">{{ result.created_count || 0 }}</span>
            <span class="stat-label">成功生成</span>
          </div>
          <div class="stat-item">
            <span class="stat-value error">{{ result.error_count || 0 }}</span>
            <span class="stat-label">失败</span>
          </div>
        </div>
        <div v-if="result.errors && result.errors.length" class="error-list">
          <div v-for="(err, i) in result.errors" :key="i" class="error-item">
            {{ err.error || err }}
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button v-if="!generating && !completed" @click="$emit('update:visible', false)">取消</el-button>
      <el-button
        v-if="!generating && !completed"
        type="primary"
        :disabled="!targetVersion"
        @click="handleGenerate"
      >
        开始生成
      </el-button>
      <el-button v-if="completed" type="primary" @click="handleClose">完成</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { requirementApi } from '@/api/modules/requirement'
import { versionApi } from '@/api/modules/testcase'

const props = defineProps({
  visible: { type: Boolean, default: false },
  requirementId: { type: [String, Number], default: null },
  requirementIds: { type: Array, default: () => [] },
  project: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:visible', 'generated'])

const targetVersion = ref(null)
const versions = ref([])
const generating = ref(false)
const completed = ref(false)
const result = ref({})

const fetchVersions = async () => {
  if (!props.project?.id) return
  try {
    const res = await versionApi.getVersions({ project: props.project.id })
    const list = res?.results || res || []
    versions.value = Array.isArray(list) ? list : []
    const def = versions.value.find(v => v.is_default)
    targetVersion.value = def?.id || versions.value[0]?.id
  } catch {
    versions.value = []
  }
}

const handleGenerate = async () => {
  if (!targetVersion.value) {
    ElMessage.warning('请选择目标版本')
    return
  }
  generating.value = true
  completed.value = false
  try {
    let res
    if (props.requirementIds.length > 1) {
      res = await requirementApi.batchGenerateTestcases({
        ids: props.requirementIds,
        version_id: targetVersion.value,
      })
    } else {
      const id = props.requirementId || props.requirementIds[0]
      res = await requirementApi.generateTestcases(id, {
        version_id: targetVersion.value,
      })
    }
    result.value = res?.data || res || {}
    completed.value = true
    ElMessage.success('生成完成')
    emit('generated', result.value)
  } catch (err) {
    ElMessage.error(err.message || '生成失败')
  } finally {
    generating.value = false
  }
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleVisibleUpdate = (val) => {
  if (generating.value && !val) return
  emit('update:visible', val)
}

watch(() => props.visible, (val) => {
  if (val) {
    generating.value = false
    completed.value = false
    result.value = {}
    fetchVersions()
  }
})
</script>

<style scoped>
.generate-content {
  min-height: 200px;
}

.info-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-primary-light);
  border-radius: 2px;
  color: var(--color-primary);
  font-size: 13px;
}

.generating-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 16px;
}

.generating-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.result-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
  gap: 16px;
}

.result-icon {
  font-size: 48px;
}

.result-icon.success {
  color: var(--color-success);
}

.result-icon.error {
  color: var(--color-danger);
}

.result-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}

.stat-value.success {
  color: var(--color-success);
}

.stat-value.error {
  color: var(--color-danger);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.error-list {
  width: 100%;
  max-height: 120px;
  overflow-y: auto;
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
}

.error-item {
  font-size: 12px;
  color: var(--color-danger);
  padding: 4px 0;
}
</style>
