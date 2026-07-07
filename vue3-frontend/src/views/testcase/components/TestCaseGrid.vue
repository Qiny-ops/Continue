<template>
  <div class="test-cases-card" v-loading="loading">
    <el-row :gutter="16">
      <el-col
        v-for="item in data"
        :key="item.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card class="case-card" shadow="hover" @click="$emit('cardClick', item)">
          <div class="card-header">
            <el-checkbox
              :model-value="item.selected"
              @click.stop
              @change="(val) => $emit('selectionChange', val, item)"
            />
            <el-tag :type="getPriorityType(item.priority)" size="small">
              {{ getPriorityLabel(item.priority) }}
            </el-tag>
          </div>
          <div class="card-title" :title="item.title">{{ item.title }}</div>
          <div class="card-info">
            <span class="info-item">
              <el-icon><Folder /></el-icon>
              {{ item.module_name || '-' }}
            </span>
            <span class="info-item">
              <el-icon><User /></el-icon>
              {{ item.created_by_name || '-' }}
            </span>
          </div>
          <div class="card-footer">
            <el-tag :type="getAutomationStatusType(item.automation_status)" size="small">
              {{ getAutomationStatusLabel(item.automation_status) }}
            </el-tag>
            <el-button-group>
              <el-button size="small" @click.stop="$emit('execute', item)">
                <el-icon><VideoPlay /></el-icon>
              </el-button>
              <el-button size="small" @click.stop="$emit('edit', item)">
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Folder, User, VideoPlay, Edit } from '@element-plus/icons-vue'
import { useTestCaseFormatters } from '@/composables/testcase/useTestCaseFormatters'

defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['cardClick', 'selectionChange', 'execute', 'edit'])

const {
  getPriorityLabel,
  getPriorityType,
  getAutomationStatusLabel,
  getAutomationStatusType
} = useTestCaseFormatters()
</script>

<style scoped>
.test-cases-card {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  background: var(--color-bg-tertiary);
}

.case-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--color-bg-tertiary);
}

.case-card :deep(.el-card__body) {
  padding: 16px;
}

.case-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-primary);
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-secondary);
}

.card-footer .el-button-group .el-button {
  border: 1px solid var(--color-border-light);
}
</style>
