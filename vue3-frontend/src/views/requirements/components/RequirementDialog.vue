<template>
  <el-dialog
    :model-value="visible"
    :title="isEditing ? '编辑需求' : '新建需求'"
    width="640px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form :model="localForm" label-position="top">
      <el-form-item label="需求标题" required>
        <el-input v-model="localForm.title" placeholder="请输入需求标题" maxlength="255" show-word-limit />
      </el-form-item>

      <el-form-item label="功能点">
        <el-input v-model="localForm.func_point" placeholder="请输入功能点描述" />
      </el-form-item>

      <el-form-item label="需求描述">
        <el-input v-model="localForm.description" type="textarea" :rows="3" placeholder="请输入需求描述" />
      </el-form-item>

      <div style="display: flex; gap: 16px;">
        <el-form-item label="优先级" style="flex: 1;">
          <el-select v-model="localForm.priority" style="width: 100%">
            <el-option label="P0" value="p0" />
            <el-option label="P1" value="p1" />
            <el-option label="P2" value="p2" />
            <el-option label="P3" value="p3" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态" style="flex: 1;">
          <el-select v-model="localForm.status" style="width: 100%">
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  isEditing: { type: Boolean, default: false },
  form: { type: Object, default: () => ({}) },
  projectId: { type: [String, Number], default: null },
  versionId: { type: [String, Number], default: null },
})

const emit = defineEmits(['update:visible', 'save'])

const saving = ref(false)
const localForm = reactive({
  title: '',
  description: '',
  func_point: '',
  priority: 'p2',
  status: 'draft',
})

watch(() => props.visible, (val) => {
  if (val) {
    Object.assign(localForm, {
      title: props.form.title || '',
      description: props.form.description || '',
      func_point: props.form.func_point || '',
      priority: props.form.priority || 'p2',
      status: props.form.status || 'draft',
    })
  }
})

const handleSave = () => {
  if (!localForm.title.trim()) return
  emit('save', { ...localForm })
}
</script>
