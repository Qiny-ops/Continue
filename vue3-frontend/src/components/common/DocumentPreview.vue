<template>
  <div class="document-preview">
    <!-- 加载状态 -->
    <div v-if="loading || docLoading" class="preview-loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>{{ docLoading ? '文档加载中...' : '加载中...' }}</span>
    </div>

    <!-- PDF 预览 -->
    <component
      :is="VueOfficePdf"
      v-else-if="fileType === 'pdf'"
      :src="fileUrl"
      class="preview-container"
      @rendered="handleRendered"
      @error="handleError"
    />

    <!-- Word 预览 -->
    <component
      :is="VueOfficeDocx"
      v-else-if="fileType === 'docx' || fileType === 'doc'"
      :src="fileUrl"
      class="preview-container"
      @rendered="handleRendered"
      @error="handleError"
    />

    <!-- Excel 预览 -->
    <component
      :is="VueOfficeExcel"
      v-else-if="fileType === 'xlsx' || fileType === 'xls'"
      :src="fileUrl"
      class="preview-container"
      @rendered="handleRendered"
      @error="handleError"
    />

    <!-- 文本/Markdown 预览 -->
    <div v-else-if="isTextFile" class="text-preview-container">
      <pre v-if="fileType === 'md'" class="markdown-content">{{ textContent }}</pre>
      <pre v-else class="text-content">{{ textContent }}</pre>
    </div>

    <!-- 不支持的文件类型 -->
    <div v-else-if="fileType" class="unsupported-preview">
      <el-icon :size="48"><Document /></el-icon>
      <p>该文件类型暂不支持在线预览</p>
      <el-button type="primary" @click="$emit('download')">
        <el-icon><Download /></el-icon>
        下载文件
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, defineAsyncComponent } from 'vue'
import { Loading, Document, Download } from '@element-plus/icons-vue'

// 懒加载文档预览组件，避免 PDF.js 等 ~4.7MB 库影响首屏
const VueOfficePdf = defineAsyncComponent(() => import('@vue-office/pdf'))
const VueOfficeDocx = defineAsyncComponent(() => import('@vue-office/docx'))
const VueOfficeExcel = defineAsyncComponent(() => import('@vue-office/excel'))

const props = defineProps({
  fileUrl: { type: String, default: '' },
  fileType: { type: String, default: '' },
  textContent: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['rendered', 'error', 'download'])

const docLoading = ref(false)

const isTextFile = computed(() => {
  const textTypes = ['txt', 'md', 'json', 'xml', 'html', 'css', 'js', 'ts', 'py', 'java', 'go', 'sql', 'yaml', 'yml']
  return textTypes.includes(props.fileType?.toLowerCase())
})

// 文档类型变化时显示加载状态
watch(() => props.fileUrl, () => {
  if (['pdf', 'docx', 'doc', 'xlsx', 'xls'].includes(props.fileType)) {
    docLoading.value = true
  }
})

const handleRendered = () => {
  docLoading.value = false
  emit('rendered')
}

const handleError = (error) => {
  docLoading.value = false
  emit('error', error)
}
</script>

<style scoped>
.document-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-tertiary);
}

.preview-container {
  flex: 1;
  overflow: auto;
  height: calc(60vh - 32px);
  width: 100%;
}

.preview-container :deep(.vue-office-pdf) {
  height: 100%;
  width: 100%;
}

.preview-container :deep(.vue-office-docx) {
  height: 100%;
  width: 100%;
}

.preview-container :deep(.vue-office-excel) {
  height: 100%;
  width: 100%;
}

.preview-container :deep(.docx-wrapper) {
  background: #f5f5f5;
  padding: 20px;
  min-width: max-content;
}

.preview-container :deep(.docx-wrapper > section.docx) {
  min-width: 816px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-container :deep(.excel-wrapper) {
  min-width: max-content;
}

.text-preview-container {
  flex: 1;
  overflow: auto;
  height: calc(60vh - 32px);
  width: 100%;
  background: var(--color-bg-secondary);
  border-radius: 4px;
}

.text-content,
.markdown-content {
  margin: 0;
  padding: 16px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  min-width: max-content;
}

.unsupported-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--color-text-tertiary);
}

.unsupported-preview p {
  margin: 0;
  font-size: 14px;
}
</style>
