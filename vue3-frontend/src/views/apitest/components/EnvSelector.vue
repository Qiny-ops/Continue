<template>
  <div class="env-selector-bar">
    <div class="selector-group">
      <span class="page-title">接口测试</span>
      <div class="selector-divider"></div>
      <div class="selector-item">
        <span class="selector-label">执行环境</span>
        <el-select
          :model-value="selectedEnv"
          placeholder="选择环境"
          class="env-select"
          :loading="loading"
          @update:model-value="$emit('update:selectedEnv', $event)"
        >
          <el-option
            v-for="env in envList"
            :key="env.id"
            :label="env.name"
            :value="env.id"
          >
            <div class="option-content">
              <el-icon class="option-icon"><Monitor /></el-icon>
              <span class="option-name">{{ env.name }}</span>
              <el-tag v-if="env.is_default" type="success" size="small" style="margin-left: 8px">默认</el-tag>
            </div>
          </el-option>
          <template #footer>
            <div class="select-footer-actions">
              <span class="footer-action" @mousedown.prevent.stop @mouseup.prevent.stop="$emit('create')">
                <el-icon><Plus /></el-icon>
                <span>新建环境</span>
              </span>
              <span class="footer-divider"></span>
              <span class="footer-action" @mousedown.prevent.stop @mouseup.prevent.stop="$emit('manage')">
                <el-icon><Setting /></el-icon>
                <span>管理环境</span>
              </span>
            </div>
          </template>
        </el-select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Monitor, Plus, Setting } from '@element-plus/icons-vue'

defineProps({
  envList: {
    type: Array,
    default: () => []
  },
  selectedEnv: {
    type: [String, Number],
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:selectedEnv', 'create', 'manage'])
</script>

<style scoped>
.env-selector-bar {
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border-secondary);
  flex-shrink: 0;
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 0;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-right: 4px;
}

.selector-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selector-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.selector-divider {
  width: 1px;
  height: 20px;
  background: var(--color-border-primary);
  margin: 0 20px;
}

.env-select {
  width: 200px;
}

.env-select :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-light) inset;
  transition: all 0.2s ease;
}

.env-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.env-select :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.env-select :deep(.el-input__inner) {
  font-size: 13px;
  color: var(--color-text-primary);
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-icon {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.option-name {
  font-size: 13px;
  color: var(--color-text-primary);
}

.select-footer-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  margin: 8px -12px -8px;
  border-top: 1px solid var(--color-border-secondary);
}

.footer-action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  color: var(--color-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 2px;
}

.footer-action:hover {
  background-color: var(--color-primary-light);
}

.footer-action .el-icon {
  font-size: 14px;
}

.footer-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border-secondary);
}
</style>
