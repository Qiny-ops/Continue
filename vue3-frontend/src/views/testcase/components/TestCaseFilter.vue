<template>
  <div class="test-case-filter">
    <div class="filter-row">
      <el-input
        v-model="localSearchQuery"
        placeholder="搜索用例名称"
        clearable
        class="search-input"
        @input="handleSearchChange"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="localFilterStatus"
        placeholder="执行状态"
        clearable
        class="filter-select"
        @change="handleStatusChange"
      >
        <el-option label="通过" value="pass" />
        <el-option label="失败" value="fail" />
        <el-option label="阻塞" value="block" />
        <el-option label="跳过" value="skip" />
      </el-select>

      <el-select
        v-model="localFilterPriority"
        placeholder="优先级"
        clearable
        class="filter-select"
        @change="handlePriorityChange"
      >
        <el-option label="P0 - 紧急" value="p0" />
        <el-option label="P1 - 高" value="p1" />
        <el-option label="P2 - 中" value="p2" />
        <el-option label="P3 - 低" value="p3" />
      </el-select>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  filterStatus: {
    type: String,
    default: ''
  },
  filterPriority: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:searchQuery',
  'update:filterStatus',
  'update:filterPriority',
  'clearSearch'
])

const localSearchQuery = ref(props.searchQuery)
const localFilterStatus = ref(props.filterStatus)
const localFilterPriority = ref(props.filterPriority)

watch(() => props.searchQuery, (val) => {
  localSearchQuery.value = val
})

watch(() => props.filterStatus, (val) => {
  localFilterStatus.value = val
})

watch(() => props.filterPriority, (val) => {
  localFilterPriority.value = val
})

const handleSearchChange = (val) => {
  emit('update:searchQuery', val)
}

const handleStatusChange = (val) => {
  emit('update:filterStatus', val)
}

const handlePriorityChange = (val) => {
  emit('update:filterPriority', val)
}
</script>

<style scoped>
.test-case-filter {
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid var(--color-bg-tertiary);
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: 260px;
}

.filter-select {
  width: 140px;
}

.search-input :deep(.el-input__wrapper),
.filter-select :deep(.el-input__wrapper) {
  border: 1px solid var(--color-border-light);
  box-shadow: none;
}

.search-input :deep(.el-input__wrapper:focus-within),
.filter-select :deep(.el-input__wrapper:focus-within) {
  border-color: var(--color-primary);
}
</style>
