<template>
  <div class="base-dialog">
    <el-dialog
      :model-value="visible"
      :title="title"
      :width="width"
      :destroy-on-close="destroyOnClose"
      :close-on-click-modal="closeOnClickModal"
      :close-on-press-escape="closeOnPressEscape"
      class="base-dialog-wrapper"
      @update:model-value="$emit('update:visible', $event)"
      @close="handleClose"
    >
      <slot />

      <template v-if="$slots.footer" #footer>
        <slot name="footer" />
      </template>

      <template v-else-if="showDefaultFooter" #footer>
        <div class="dialog-footer">
          <el-button size="large" @click="handleCancel">
            {{ cancelText }}
          </el-button>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * BaseDialog - 统一的对话框基础组件
 * @property {boolean} visible - 是否显示对话框
 * @property {string} title - 对话框标题
 * @property {string} width - 对话框宽度
 * @property {boolean} destroyOnClose - 关闭时销毁内容
 * @property {boolean} closeOnClickModal - 点击遮罩关闭
 * @property {boolean} showDefaultFooter - 显示默认底部
 * @property {string} cancelText - 取消按钮文字
 * @property {string} confirmText - 确认按钮文字
 * @property {boolean} loading - 加载状态
 */
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '600px'
  },
  destroyOnClose: {
    type: Boolean,
    default: true
  },
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  closeOnPressEscape: {
    type: Boolean,
    default: true
  },
  showDefaultFooter: {
    type: Boolean,
    default: false
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'close', 'cancel', 'confirm'])

const handleClose = () => {
  emit('close')
}

const handleCancel = () => {
  emit('update:visible', false)
  emit('cancel')
}

const handleConfirm = () => {
  emit('confirm')
}
</script>

<style scoped>
.base-dialog-wrapper :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-primary, var(--color-bg-tertiary));
  margin-right: 0;
}

.base-dialog-wrapper :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary, var(--color-text-primary));
}

.base-dialog-wrapper :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

.base-dialog-wrapper :deep(.el-dialog__body) {
  padding: 16px;
}

.base-dialog-wrapper :deep(.el-dialog__footer) {
  padding: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--color-border-primary, var(--color-bg-tertiary));
  background: var(--color-bg-secondary, var(--color-bg-secondary));
}
</style>
