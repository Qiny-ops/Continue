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
    <ExecuteReport
      :executing="executing"
      :validating="validating"
      :status="status"
      :case-name="caseName"
      :testpoint="testpoint"
      :duration="duration"
      :logs="logs"
      :key-decisions="keyDecisions"
      :thinking-content="thinkingContent"
      :failure-analysis="failureAnalysis"
    />

    <template #footer>
      <el-button @click="$emit('update:visible', false)" :disabled="executing">
        关闭
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import ExecuteReport from './ExecuteReport.vue'

defineProps({
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

defineEmits(['update:visible'])
</script>
