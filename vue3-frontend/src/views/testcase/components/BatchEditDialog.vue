<template>
  <el-dialog
    :model-value="visible"
    :title="dialogTitle"
    width="480px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <div class="batch-edit-content">
      <div class="edit-info">
        <el-icon class="info-icon"><InfoFilled /></el-icon>
        <span>将对选中的 <strong>{{ selectedCount }}</strong> 个用例进行批量修改</span>
      </div>

      <div v-if="editType === 'priority'" class="edit-form">
        <div class="form-label">选择优先级</div>
        <el-radio-group v-model="editValue" class="priority-group">
          <el-radio-button value="p0">
            <span class="priority-option critical">P0 - 紧急</span>
          </el-radio-button>
          <el-radio-button value="p1">
            <span class="priority-option high">P1 - 高</span>
          </el-radio-button>
          <el-radio-button value="p2">
            <span class="priority-option medium">P2 - 中</span>
          </el-radio-button>
          <el-radio-button value="p3">
            <span class="priority-option low">P3 - 低</span>
          </el-radio-button>
        </el-radio-group>
      </div>

      <div v-else-if="editType === 'module'" class="edit-form">
        <div class="form-label">选择目标模块</div>
        <el-tree-select
          v-model="editValue"
          :data="moduleTree"
          :props="{ label: 'name', value: 'id', children: 'children' }"
          placeholder="请选择目标模块"
          check-strictly
          clearable
          filterable
          class="module-select"
        />
      </div>

      <div v-else-if="editType === 'tags'" class="edit-form">
        <div class="form-label">设置标签</div>
        <div class="tag-mode">
          <el-radio-group v-model="tagMode" size="small">
            <el-radio-button value="add">追加标签</el-radio-button>
            <el-radio-button value="replace">替换标签</el-radio-button>
            <el-radio-button value="remove">移除标签</el-radio-button>
          </el-radio-group>
        </div>
        <el-select
          v-model="editValue"
          multiple
          filterable
          allow-create
          default-first-option
          :reserve-keyword="false"
          placeholder="输入标签名称，按回车添加"
          class="tag-select"
        >
          <el-option
            v-for="tag in existingTags"
            :key="tag"
            :label="tag"
            :value="tag"
          />
        </el-select>
        <div class="tag-hint">
          <el-icon><InfoFilled /></el-icon>
          <span v-if="tagMode === 'add'">将新增标签到现有标签中</span>
          <span v-else-if="tagMode === 'replace'">将替换所有现有标签</span>
          <span v-else>将从现有标签中移除指定标签</span>
        </div>
      </div>

      <div v-else-if="editType === 'status'" class="edit-form">
        <div class="form-label">选择自动化状态</div>
        <el-radio-group v-model="editValue" class="status-group">
          <el-radio-button value="not_analyzed">
            <div class="status-option">
              <el-icon class="status-icon gray"><QuestionFilled /></el-icon>
              <span>未分析</span>
            </div>
          </el-radio-button>
          <el-radio-button value="not_automated">
            <div class="status-option">
              <el-icon class="status-icon orange"><WarningFilled /></el-icon>
              <span>未自动化</span>
            </div>
          </el-radio-button>
          <el-radio-button value="automated">
            <div class="status-option">
              <el-icon class="status-icon green"><CircleCheckFilled /></el-icon>
              <span>已自动化</span>
            </div>
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirm">
          确认修改
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { InfoFilled, QuestionFilled, WarningFilled, CircleCheckFilled } from '@element-plus/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  editType: {
    type: String,
    default: ''
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  moduleTree: {
    type: Array,
    default: () => []
  },
  existingTags: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'confirm'])

const editValue = ref(null)
const tagMode = ref('add')

const dialogTitle = computed(() => {
  const titles = {
    priority: '批量修改优先级',
    module: '批量移动用例',
    tags: '批量修改标签',
    status: '批量修改自动化状态'
  }
  return titles[props.editType] || '批量编辑'
})

watch(() => props.visible, (val) => {
  if (val) {
    editValue.value = null
    tagMode.value = 'add'
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleConfirm = () => {
  if (props.editType === 'tags') {
    emit('confirm', {
      type: props.editType,
      value: editValue.value,
      mode: tagMode.value
    })
  } else {
    emit('confirm', {
      type: props.editType,
      value: editValue.value
    })
  }
}
</script>

<style scoped>
.batch-edit-content {
  padding: 8px 0;
}

.edit-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-primary-light);
  border-radius: 2px;
  margin-bottom: 20px;
  color: var(--color-primary);
  font-size: 14px;
}

.edit-info strong {
  color: var(--color-primary);
  font-weight: 600;
}

.info-icon {
  font-size: 16px;
}

.edit-form {
  padding: 0 4px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.priority-group,
.status-group {
  width: 100%;
}

.priority-group :deep(.el-radio-button),
.status-group :deep(.el-radio-button) {
  width: 50%;
  margin-bottom: 8px;
}

.priority-group :deep(.el-radio-button__inner),
.status-group :deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 2px !important;
  border: 1px solid var(--color-border-light) !important;
  padding: 12px 16px;
  text-align: left;
}

.priority-group :deep(.el-radio-button.is-active .el-radio-button__inner),
.status-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 2px rgba(24, 24, 27, 0.2);
}

.priority-option {
  font-weight: 500;
}

.priority-option.critical {
  color: var(--color-danger);
}

.priority-option.high {
  color: var(--color-warning);
}

.priority-option.medium {
  color: var(--color-primary);
}

.priority-option.low {
  color: var(--color-text-tertiary);
}

.module-select {
  width: 100%;
}

.tag-mode {
  margin-bottom: 12px;
}

.tag-select {
  width: 100%;
}

.tag-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 16px;
}

.status-icon.gray {
  color: var(--color-text-tertiary);
}

.status-icon.orange {
  color: var(--color-warning);
}

.status-icon.green {
  color: var(--color-success);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
