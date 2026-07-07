<template>
  <div class="create-project-page">
    <div class="page-content">
      <div class="content-header">
        <div class="back-button" @click="handleBack">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M10.354 1.646a.5.5 0 010 .708L5.207 7.5l5.147 5.146a.5.5 0 01-.708.708l-5.5-5.5a.5.5 0 010-.708l5.5-5.5a.5.5 0 01.708 0z"/>
          </svg>
        </div>
        <div class="header-title">创建项目</div>
      </div>
      <div class="right-content">
        <div class="create-project-form">
          <div class="form-group">
            <div class="form-label required-mark">项目名称</div>
            <div class="form-control">
              <el-input
                v-model="form.name"
                placeholder="给项目起个名称"
                @input="updateProjectIdentifier"
              />
            </div>
            <div class="form-help">请输入 1~31 位以内的项目名称</div>
          </div>

          <div class="form-group">
            <div class="form-label required-mark">项目标识</div>
            <div class="form-control">
              <el-input
                v-model="form.identifier"
                placeholder="用于唯一标记项目"
                @input="validateIdentifier"
              />
            </div>
            <div class="form-help">只能包含小写字母、数字和下划线</div>
          </div>

          <div class="form-group">
            <div class="form-label">项目描述</div>
            <div class="form-control">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="4"
                placeholder="100 字内项目描述（选填）"
                :maxlength="100"
                show-word-limit
              />
            </div>
          </div>

          <div class="action-buttons">
            <el-button type="primary" @click="handleSubmit">
              完成
            </el-button>
            <el-button @click="handleCancel">
              取消
            </el-button>
          </div>
        </div>

        <div class="upload-section">
          <div class="upload-title">项目图标</div>
          <div class="icon-preview" :style="{ background: form.iconColor }">
            <el-icon :size="32"><component :is="getIcon(form.icon)" /></el-icon>
          </div>
          <div class="icon-actions">
            <el-button size="small" @click="showIconPicker = true">更换图标</el-button>
            <div class="color-list">
              <span
                v-for="c in colorPresets"
                :key="c"
                :class="['color-dot', { active: form.iconColor === c }]"
                :style="{ background: c }"
                @click="form.iconColor = c"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图标选择器 -->
    <el-dialog v-model="showIconPicker" title="选择图标" width="480px">
      <div class="icon-grid">
        <div
          v-for="icon in availableIcons"
          :key="icon.name"
          :class="['icon-item', { selected: form.icon === icon.name }]"
          @click="form.icon = icon.name; showIconPicker = false"
        >
          <div class="icon-preview-small" :style="{ background: form.iconColor }">
            <el-icon :size="20"><component :is="icon.component" /></el-icon>
          </div>
          <span>{{ icon.label }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectIcons } from '@/utils/icons'
import { useProjectStore } from '@/stores/modules/project'

const router = useRouter()
const projectStore = useProjectStore()

// 表单数据
const form = reactive({
  name: '',
  identifier: '',
  description: '',
  type: 'web',
  visibility: 'public',
  template: 'blank',
  icon: 'Folder',
  iconColor: '#18181B'
})

// 图标选择器
const showIconPicker = ref(false)
const colorPresets = ['#18181B', '#3F3F46', '#52525B', '#71717A', '#EF4444', '#22C55E', '#EAB308', '#0EA5E9']

const availableIcons = projectIcons

import { getIconComponent as getIcon } from '@/utils/icons'

// 更新项目标识
const updateProjectIdentifier = () => {
  if (!form.identifier) {
    form.identifier = form.name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '')
  }
}

// 验证标识符
const validateIdentifier = () => {
  form.identifier = form.identifier
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
}

// 返回
const handleBack = () => {
  router.push('/projects')
}

// 取消
const handleCancel = () => {
  router.push('/projects')
}

// 提交
const handleSubmit = async () => {
  if (!form.name?.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }

  if (!form.identifier?.trim()) {
    ElMessage.warning('请输入项目标识')
    return
  }

  try {
    await projectStore.createProject({
      name: form.name,
      code: form.identifier,
      description: form.description,
      type: form.type,
      status: 'active',
      icon: form.icon,
      iconColor: form.iconColor
    })

    ElMessage.success('项目创建成功')
    router.push('/projects')
  } catch (error) {
    ElMessage.error(error?.message || '项目创建失败')
  }
}
</script>

<style scoped>
.create-project-page {
  display: flex;
  min-width: 1000px;
  flex-grow: 1;
  background: #fff;
}

.page-content {
  padding: 32px 24px;
  flex-grow: 1;
  height: 100%;
}

.content-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-right: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.back-button:hover {
  color: var(--color-text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.right-content {
  display: flex;
  gap: 32px;
}

.create-project-form {
  flex: 1;
  max-width: 552px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--color-text-primary);
  margin-bottom: 8px;
  font-weight: 600;
}

.required-mark::after {
  display: inline-block;
  content: '*';
  margin-left: 4px;
  color: var(--color-danger);
}

.form-control {
  margin-bottom: 4px;
}

.form-control :deep(.el-input__wrapper) {
  border-radius: 2px;
  box-shadow: 0 0 0 1px var(--color-border-primary) inset;
}

.form-control :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 1px var(--color-primary) inset;
}

.form-control :deep(.el-textarea__inner) {
  border-radius: 2px;
  border: 1px solid var(--color-border-primary);
  box-shadow: none;
}

.form-control :deep(.el-textarea__inner:focus) {
  border-color: var(--color-primary);
}

.form-help {
  line-height: 16px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-buttons :deep(.el-button) {
  min-width: 80px;
  border-radius: 2px;
}

.action-buttons :deep(.el-button--primary) {
  background: var(--color-primary);
  border: none;
  box-shadow: var(--shadow-sm);
}

.action-buttons :deep(.el-button--primary:hover) {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

/* 上传封面区域 */
.upload-section {
  width: 200px;
  flex-shrink: 0;
}

.upload-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.icon-preview {
  width: 80px;
  height: 80px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 12px;
}

.icon-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.color-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.color-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.color-dot:hover {
  border-color: var(--color-text-tertiary);
}

.color-dot.active {
  border-color: var(--color-text-primary);
}

/* 图标网格 */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-item:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.icon-item.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.icon-preview-small {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.icon-item span {
  font-size: 11px;
  color: var(--color-text-secondary);
}

@media (max-width: 1200px) {
  .create-project-page {
    min-width: auto;
  }

  .right-content {
    flex-direction: column;
  }

  .upload-section {
    width: 100%;
  }

  .upload-preview {
    width: 100%;
    max-width: 300px;
  }
}
</style>
