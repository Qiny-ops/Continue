<template>
  <div class="repo-version-bar">
    <div class="selector-group">
      <span class="page-title">用例管理</span>
      <div class="selector-divider"></div>
      <div class="selector-item">
        <span class="selector-label">用例库</span>
        <el-select
          :model-value="selectedRepo"
          placeholder="选择用例库"
          class="repo-select"
          :loading="loading"
          @update:model-value="$emit('update:selectedRepo', $event)"
        >
          <el-option
            v-for="repo in repoList"
            :key="repo.id"
            :label="repo.name"
            :value="repo.id"
          >
            <div class="option-content">
              <el-icon class="option-icon"><FolderOpened /></el-icon>
              <span class="option-name">{{ repo.name }}</span>
            </div>
          </el-option>
          <template #footer>
            <div class="select-footer-actions">
              <span class="footer-action" @mousedown.prevent @click="$emit('createRepo')">
                <el-icon><Plus /></el-icon>
                <span>新建用例库</span>
              </span>
              <span class="footer-divider"></span>
              <span class="footer-action" @mousedown.prevent @click="$emit('manageRepo')">
                <el-icon><Setting /></el-icon>
                <span>管理用例库</span>
              </span>
            </div>
          </template>
        </el-select>
      </div>

      <div class="selector-divider"></div>

      <div class="selector-item">
        <span class="selector-label">版本</span>
        <el-select
          :model-value="selectedVersion"
          placeholder="选择版本"
          class="version-select"
          :loading="loading"
          @update:model-value="$emit('update:selectedVersion', $event)"
        >
          <el-option
            v-for="version in versionList"
            :key="version.id"
            :label="version.name"
            :value="version.id"
          >
            <div class="option-content">
              <el-icon class="option-icon"><PriceTag /></el-icon>
              <span class="option-name">{{ version.name }}</span>
            </div>
          </el-option>
          <template #footer>
            <div class="select-footer-actions">
              <span class="footer-action" @mousedown.prevent @click="$emit('createVersion')">
                <el-icon><Plus /></el-icon>
                <span>新建版本</span>
              </span>
              <span class="footer-divider"></span>
              <span class="footer-action" @mousedown.prevent @click="$emit('manageVersion')">
                <el-icon><Setting /></el-icon>
                <span>管理版本</span>
              </span>
            </div>
          </template>
        </el-select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FolderOpened, PriceTag, Plus, Setting } from '@element-plus/icons-vue'

defineProps({
  repoList: {
    type: Array,
    default: () => []
  },
  versionList: {
    type: Array,
    default: () => []
  },
  selectedRepo: {
    type: [String, Number],
    default: ''
  },
  selectedVersion: {
    type: [String, Number],
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:selectedRepo', 'update:selectedVersion', 'createRepo', 'createVersion', 'manageRepo', 'manageVersion'])
</script>

<style scoped>
.repo-version-bar {
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

.repo-select,
.version-select {
  width: 180px;
}

.repo-select :deep(.el-input__wrapper),
.version-select :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-light) inset;
  transition: all 0.2s ease;
}

.repo-select :deep(.el-input__wrapper:hover),
.version-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.repo-select :deep(.el-input__wrapper.is-focus),
.version-select :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.repo-select :deep(.el-input__inner),
.version-select :deep(.el-input__inner) {
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
  gap: 6px;
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
