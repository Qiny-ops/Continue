<template>
  <el-dialog
    :model-value="visible"
    :title="isEditing ? '编辑测试用例' : '新建测试用例'"
    width="960px"
    destroy-on-close
    :close-on-click-modal="false"
    class="test-case-dialog"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="dialog-content">
      <div class="form-main">
        <div class="form-item">
          <div class="form-label">
            <span>用例标题</span>
            <span class="required">*</span>
          </div>
          <el-input
            v-model="localForm.title"
            placeholder="请输入用例标题，不超过 128 个字符"
            maxlength="128"
            size="large"
            show-word-limit
          />
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>所在目录</span>
            <span class="required">*</span>
          </div>
          <el-tree-select
            v-model="localForm.module"
            :data="moduleTree"
            :props="{ label: 'name', children: 'children', value: 'id' }"
            placeholder="请选择模块目录"
            clearable
            check-strictly
            :render-after-expand="false"
            size="large"
            style="width: 100%"
          />
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>前置条件</span>
            <span class="optional">（可选）</span>
          </div>
          <el-input
            v-model="localForm.precondition"
            type="textarea"
            :rows="2"
            placeholder="请输入前置条件，支持 Markdown 格式"
            resize="none"
          />
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>测试步骤</span>
          </div>
          <el-input
            v-model="localForm.steps"
            type="textarea"
            :rows="4"
            placeholder="请输入测试步骤，如：&#10;1. 登录系统&#10;2. 进入个人中心页面&#10;3. 点击下拉菜单"
            resize="none"
          />
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>预期结果</span>
          </div>
          <el-input
            v-model="localForm.expected_result"
            type="textarea"
            :rows="3"
            placeholder="请输入预期结果，如：&#10;1. 登录成功，跳转至首页&#10;2. 个人中心页面正常展示&#10;3. 下拉菜单包含'我要请假'选项"
            resize="none"
          />
        </div>

        <div class="form-item">
          <div class="form-label">
            <span>附件</span>
            <span class="optional">（可选）</span>
          </div>
          <el-upload
            class="attachment-upload"
            drag
            action="#"
            :auto-upload="false"
            accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.xls,.xlsx"
            :show-file-list="false"
          >
            <div class="upload-content">
              <el-icon class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">
                <span>将文件拖到此处，或</span>
                <em>点击上传</em>
              </div>
              <div class="upload-tip">支持 jpg、png、gif、pdf、doc、xls 等格式</div>
            </div>
          </el-upload>
        </div>
      </div>

      <div class="info-sidebar">
        <div class="sidebar-title">用例属性</div>

        <div class="info-item">
          <div class="form-label">
            <span>优先级</span>
            <span class="required">*</span>
          </div>
          <el-select v-model="localForm.priority" placeholder="请选择优先级" size="large" style="width: 100%">
            <el-option label="P0" value="p0">
              <div class="priority-option">
                <span class="priority-badge p0">P0</span>
                <span class="priority-text">最高</span>
              </div>
            </el-option>
            <el-option label="P1" value="p1">
              <div class="priority-option">
                <span class="priority-badge p1">P1</span>
                <span class="priority-text">高</span>
              </div>
            </el-option>
            <el-option label="P2" value="p2">
              <div class="priority-option">
                <span class="priority-badge p2">P2</span>
                <span class="priority-text">中</span>
              </div>
            </el-option>
            <el-option label="P3" value="p3">
              <div class="priority-option">
                <span class="priority-badge p3">P3</span>
                <span class="priority-text">低</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <div class="info-item">
          <div class="form-label">
            <span>评估工时</span>
          </div>
          <el-input-number
            v-model="localForm.estimated_hours"
            :min="0"
            :max="999.99"
            :precision="2"
            placeholder="请输入"
            size="large"
            style="width: 100%"
            controls-position="right"
          >
            <template #suffix>小时</template>
          </el-input-number>
        </div>

        <div class="info-item">
          <div class="form-label">
            <span>标签</span>
          </div>
          <div class="tags-wrapper">
            <el-tag
              v-for="(tag, index) in localForm.tags"
              :key="index"
              closable
              size="large"
              class="tag-item"
              @close="removeTag(index)"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputTagVisible"
              ref="tagInputRef"
              v-model="inputTagValue"
              size="small"
              class="tag-input"
              @keyup.enter="confirmTag"
              @blur="confirmTag"
            />
            <el-button v-else size="small" class="add-tag-btn" @click="showTagInput">
              <el-icon><Plus /></el-icon>
              <span>添加标签</span>
            </el-button>
          </div>
        </div>

        <div class="info-item">
          <div class="form-label">
            <span>自动化状态</span>
          </div>
          <el-select v-model="localForm.automation_status" placeholder="请选择" size="large" style="width: 100%">
            <el-option label="未分析" value="not_analyzed" />
            <el-option label="未自动化" value="not_automated" />
            <el-option label="已自动化" value="automated" />
          </el-select>
        </div>

        <div class="info-item">
          <div class="form-label">
            <span>关联需求</span>
          </div>
          <el-input
            v-model="localForm.requirement"
            placeholder="请输入关联需求"
            size="large"
          />
        </div>

        <div class="info-item">
          <div class="form-label">
            <span>执行状态</span>
          </div>
          <el-select v-model="localForm.pass_status" placeholder="请选择" size="large" style="width: 100%">
            <el-option label="未执行" value="not_executed">
              <div class="status-option">
                <span class="status-dot not-executed"></span>
                <span>未执行</span>
              </div>
            </el-option>
            <el-option label="通过" value="passed">
              <div class="status-option">
                <span class="status-dot passed"></span>
                <span>通过</span>
              </div>
            </el-option>
            <el-option label="未通过" value="failed">
              <div class="status-option">
                <span class="status-dot failed"></span>
                <span>未通过</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-checkbox v-model="continueCreate">保存后继续创建下一个</el-checkbox>
        </div>
        <div class="footer-right">
          <el-button size="large" @click="$emit('update:visible', false)">取消</el-button>
          <el-button type="primary" size="large" @click="handleSave">
            {{ isEditing ? '保存修改' : '创建用例' }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, watch, reactive } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'

const props = defineProps({
  visible: Boolean,
  isEditing: Boolean,
  form: Object,
  moduleTree: Array
})

const emit = defineEmits(['update:visible', 'save', 'update:form'])

const localForm = reactive({
  title: '',
  module: null,
  precondition: '',
  steps: '',
  expected_result: '',
  priority: '',
  estimated_hours: null,
  tags: [],
  automation_status: 'not_analyzed',
  automation_case_id: '',
  requirement: '',
  pass_status: 'not_executed'
})

const inputTagVisible = ref(false)
const inputTagValue = ref('')
const tagInputRef = ref(null)
const continueCreate = ref(false)

watch(() => props.form, (newForm) => {
  if (newForm) {
    Object.assign(localForm, {
      title: newForm.title || '',
      module: newForm.module || null,
      precondition: newForm.precondition || '',
      steps: newForm.steps || '',
      expected_result: newForm.expected_result || '',
      priority: newForm.priority || '',
      estimated_hours: newForm.estimated_hours ?? null,
      tags: newForm.tags ? [...newForm.tags] : [],
      automation_status: newForm.automation_status || 'not_analyzed',
      automation_case_id: newForm.automation_case_id || '',
      requirement: newForm.requirement || '',
      pass_status: newForm.pass_status || 'not_executed'
    })
  }
}, { immediate: true, deep: true })

const showTagInput = () => {
  inputTagVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const confirmTag = () => {
  if (inputTagValue.value) {
    if (!localForm.tags) {
      localForm.tags = []
    }
    localForm.tags.push(inputTagValue.value)
  }
  inputTagVisible.value = false
  inputTagValue.value = ''
}

const removeTag = (index) => {
  localForm.tags.splice(index, 1)
}

const handleSave = () => {
  emit('update:form', JSON.parse(JSON.stringify(localForm)))
  emit('save', continueCreate.value)
}
</script>

<style scoped>
.test-case-dialog :deep(.el-dialog__header) {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-bg-tertiary);
  margin-right: 0;
}

.test-case-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.test-case-dialog :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

.test-case-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.test-case-dialog :deep(.el-dialog__footer) {
  padding: 0;
}

.dialog-content {
  display: flex;
  min-height: 400px;
  max-height: 520px;
}

.form-main {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-label .required {
  color: var(--color-danger);
}

.form-label .optional {
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.attachment-upload :deep(.el-upload-dragger) {
  border: 1px dashed var(--color-border-light);
  border-radius: 2px;
  background: var(--color-bg-secondary);
  padding: 16px;
  transition: all 0.2s;
}

.attachment-upload :deep(.el-upload-dragger:hover) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.upload-content {
  text-align: center;
}

.upload-icon {
  font-size: 24px;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.upload-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.upload-text em {
  color: var(--color-primary);
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

.info-sidebar {
  width: 220px;
  background: var(--color-bg-secondary);
  padding: 16px 12px;
  border-left: 1px solid var(--color-bg-tertiary);
  overflow-y: auto;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-bg-tertiary);
}

.info-item {
  margin-bottom: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item .form-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.info-item :deep(.el-input__wrapper),
.info-item :deep(.el-select__wrapper) {
  min-height: 32px;
}

.info-item :deep(.el-input-number) {
  width: 100%;
}

.info-item :deep(.el-input-number .el-input__wrapper) {
  padding-left: 8px;
  padding-right: 32px;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.priority-badge {
  width: 24px;
  height: 18px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
}

.priority-badge.p0 {
  background: var(--color-danger);
}

.priority-badge.p1 {
  background: var(--color-warning);
}

.priority-badge.p2 {
  background: var(--color-primary);
}

.priority-badge.p3 {
  background: var(--color-text-tertiary);
}

.priority-text {
  font-size: 13px;
  color: var(--color-text-primary);
}

.status-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.not-executed {
  background: var(--color-text-tertiary);
}

.status-dot.passed {
  background: var(--color-success);
}

.status-dot.failed {
  background: var(--color-danger);
}

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.tag-item {
  margin: 0;
}

.tag-input {
  width: 80px;
}

.add-tag-btn {
  border: 1px dashed var(--color-border-light);
  color: var(--color-text-tertiary);
}

.add-tag-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-top: 1px solid var(--color-bg-tertiary);
  background: var(--color-bg-secondary);
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-right {
  display: flex;
  gap: 8px;
}
</style>
