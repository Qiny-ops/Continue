<template>
  <el-dialog
    :model-value="visible"
    title="导入测试用例"
    width="500px"
    destroy-on-close
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-upload
      class="upload-area"
      drag
      action="#"
      :auto-upload="false"
      accept=".xlsx,.xls,.csv"
    >
      <el-icon class="el-icon--upload"><Upload /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 .xlsx, .xls, .csv 格式文件，
          <el-link type="primary" @click="$emit('downloadTemplate')">下载模板</el-link>
        </div>
      </template>
    </el-upload>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('update:visible', false)">取消</el-button>
        <el-button type="primary" @click="$emit('import')">确认导入</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { Upload } from '@element-plus/icons-vue'

defineProps({
  visible: Boolean
})

defineEmits(['update:visible', 'import', 'downloadTemplate'])
</script>

<style scoped>
.upload-area :deep(.el-upload-dragger) {
  border: 1px dashed var(--color-border-light);
  border-radius: 0;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary);
}

.upload-area :deep(.el-icon--upload) {
  color: var(--color-text-tertiary);
}

.upload-area :deep(.el-upload__text) {
  color: var(--color-text-secondary);
}

.upload-area :deep(.el-upload__text em) {
  color: var(--color-primary);
}

.upload-area :deep(.el-upload__tip) {
  color: var(--color-text-tertiary);
}
</style>
