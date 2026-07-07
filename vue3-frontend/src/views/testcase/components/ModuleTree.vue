<template>
  <div class="module-sidebar">
    <!-- 全部用例 -->
    <div class="sidebar-header">
      <div
        class="nav-item all-cases"
        :class="{ active: !selectedNodeId }"
        @click="$emit('showAllCases')"
      >
        <div class="nav-item-content">
          <el-icon class="nav-icon"><FolderOpened /></el-icon>
          <span class="nav-label">全部用例</span>
          <span v-if="totalCount !== undefined" class="nav-count">{{ totalCount }}</span>
        </div>
      </div>
    </div>

    <!-- 模块列表 -->
    <div class="sidebar-body">
      <div class="module-header">
        <span class="module-title">模块目录</span>
        <div class="module-actions">
          <el-tooltip :content="isBatchMode ? '退出批量操作' : '批量操作'" placement="top">
            <span class="action-btn" :class="{ active: isBatchMode }" @click="toggleBatchMode">
              <el-icon><Operation /></el-icon>
            </span>
          </el-tooltip>
          <el-tooltip :content="isAllExpanded ? '收起全部' : '展开全部'" placement="top">
            <span class="action-btn" @click="toggleExpandAll">
              <el-icon><Sort /></el-icon>
            </span>
          </el-tooltip>
          <el-tooltip content="添加模块" placement="top">
            <span class="action-btn" @click="$emit('addModule')">
              <el-icon><Plus /></el-icon>
            </span>
          </el-tooltip>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="isBatchMode" class="batch-actions">
        <div class="batch-info">
          <el-checkbox
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="handleSelectAll"
          >
            全选
          </el-checkbox>
          <span v-if="selectedModuleIds.length > 0" class="selected-count">
            已选 {{ selectedModuleIds.length }} 项
          </span>
        </div>
        <el-button
          type="danger"
          size="small"
          :disabled="selectedModuleIds.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>

      <el-tree
        v-if="treeData?.length"
        ref="treeRef"
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        highlight-current
        :expand-on-click-node="false"
        :default-expand-all="false"
        @node-click="handleNodeClick"
        @check="handleCheck"
        :show-checkbox="isBatchMode"
        class="module-tree"
      >
        <template #default="{ node, data }">
          <div
            class="tree-node"
            @mouseenter="hoverNodeId = data.id"
            @mouseleave="hoverNodeId = null"
          >
            <div class="node-content">
              <el-icon class="node-icon">
                <Folder v-if="data.children?.length" />
                <Document v-else />
              </el-icon>
              <span class="node-label">{{ node.label }}</span>
              <span v-if="data.count !== undefined" class="node-count">{{ data.count }}</span>
            </div>
            <div
              v-show="hoverNodeId === data.id && !isBatchMode"
              class="node-actions"
              @click.stop
            >
              <span class="node-action" title="添加子模块" @click="$emit('addSubModule', data)">
                <el-icon><Plus /></el-icon>
              </span>
              <span class="node-action" title="编辑" @click="$emit('editModule', data)">
                <el-icon><Edit /></el-icon>
              </span>
              <span class="node-action danger" title="删除" @click="$emit('deleteModule', data)">
                <el-icon><Delete /></el-icon>
              </span>
            </div>
          </div>
        </template>
      </el-tree>

      <div v-if="!treeData?.length && !loading" class="empty-state">
        <el-icon class="empty-icon"><FolderOpened /></el-icon>
        <p class="empty-text">暂无模块</p>
        <el-button type="primary" size="small" @click="$emit('addModule')">
          <el-icon><Plus /></el-icon>
          添加模块
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Folder, FolderOpened, Document, Edit, Delete, Sort, Operation } from '@element-plus/icons-vue'
import { moduleApi } from '@/api/modules/testcase'

const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  totalCount: {
    type: Number,
    default: undefined
  },
  currentVersion: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['addModule', 'addSubModule', 'editModule', 'deleteModule', 'nodeClick', 'showAllCases', 'refresh'])

const hoverNodeId = ref(null)
const treeRef = ref(null)
const isAllExpanded = ref(false)
const selectedNodeId = ref(null)
const isBatchMode = ref(false)
const selectedModuleIds = ref([])

const isAllSelected = computed(() => {
  if (!props.treeData?.length) return false
  return selectedModuleIds.value.length === getAllModuleIds(props.treeData).length
})

const isIndeterminate = computed(() => {
  const total = getAllModuleIds(props.treeData).length
  return selectedModuleIds.value.length > 0 && selectedModuleIds.value.length < total
})

function getAllModuleIds(modules) {
  const ids = []
  function collect(items) {
    for (const item of items) {
      ids.push(item.id)
      if (item.children?.length) {
        collect(item.children)
      }
    }
  }
  collect(modules)
  return ids
}

const toggleBatchMode = () => {
  isBatchMode.value = !isBatchMode.value
  if (!isBatchMode.value) {
    selectedModuleIds.value = []
    if (treeRef.value) {
      treeRef.value.setCheckedKeys([])
    }
  }
}

const handleSelectAll = (val) => {
  if (val) {
    selectedModuleIds.value = getAllModuleIds(props.treeData)
    if (treeRef.value) {
      treeRef.value.setCheckedKeys(selectedModuleIds.value)
    }
  } else {
    selectedModuleIds.value = []
    if (treeRef.value) {
      treeRef.value.setCheckedKeys([])
    }
  }
}

const handleCheck = (data, { checkedKeys }) => {
  selectedModuleIds.value = checkedKeys
}

const handleBatchDelete = async () => {
  if (selectedModuleIds.value.length === 0) {
    ElMessage.warning('请选择要删除的模块')
    return
  }

  try {
    // 先尝试不删除用例
    const response = await moduleApi.batchDeleteModules(
      selectedModuleIds.value,
      props.currentVersion,
      false
    )
    // 删除成功（没有用例）
    ElMessage.success(response.data.message || '删除成功')
    selectedModuleIds.value = []
    isBatchMode.value = false
    emit('refresh')
  } catch (error) {
    // 获取错误信息
    const errorMsg = error?.response?.data?.message || error?.message || '删除失败'

    // 如果有用例，显示确认对话框
    if (errorMsg.includes('测试用例')) {
      try {
        await ElMessageBox.confirm(
          errorMsg,
          '批量删除确认',
          {
            confirmButtonText: '同时删除用例',
            cancelButtonText: '取消',
            distinguishCancelAndClose: true,
            type: 'warning'
          }
        )

        // 用户确认同时删除用例
        const response = await moduleApi.batchDeleteModules(
          selectedModuleIds.value,
          props.currentVersion,
          true
        )
        ElMessage.success(response.data.message || '删除成功')
        selectedModuleIds.value = []
        isBatchMode.value = false
        emit('refresh')
      } catch (e) {
        // 用户取消
        if (e !== 'cancel' && e !== 'close') {

        }
      }
    } else {
      ElMessage.error(errorMsg)
    }
  }
}

const handleNodeClick = (data) => {
  if (!isBatchMode.value) {
    selectedNodeId.value = data.id
    emit('nodeClick', data)
  }
}

const toggleExpandAll = () => {
  if (!treeRef.value) return

  const nodes = treeRef.value.store._getAllNodes()
  if (isAllExpanded.value) {
    nodes.forEach(node => {
      node.expanded = false
    })
    isAllExpanded.value = false
  } else {
    nodes.forEach(node => {
      node.expanded = true
    })
    isAllExpanded.value = true
  }
}

watch(() => props.treeData, () => {
  if (isBatchMode.value) {
    selectedModuleIds.value = []
    if (treeRef.value) {
      treeRef.value.setCheckedKeys([])
    }
  }
})
</script>

<style scoped>
.module-sidebar {
  width: 260px;
  height: 100%;
  background: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部 - 全部用例 */
.sidebar-header {
  padding: 16px 0 8px;
  flex-shrink: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 0 8px;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.nav-item:hover {
  background: var(--color-primary-light);
}

.nav-item.active {
  background: var(--color-primary-light);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

.nav-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.nav-icon {
  color: var(--color-text-secondary);
  font-size: 18px;
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.nav-item:hover .nav-icon,
.nav-item.active .nav-icon {
  color: var(--color-primary);
}

.nav-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item.active .nav-label {
  color: var(--color-primary);
  font-weight: 500;
}

.nav-count {
  color: var(--color-text-tertiary);
  font-size: 12px;
  background: var(--color-bg-tertiary);
  padding: 2px 8px;
  border-radius: 2px;
  font-weight: 500;
  flex-shrink: 0;
}

/* 模块列表区域 */
.sidebar-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-bottom: 8px;
}

.sidebar-body::-webkit-scrollbar {
  width: 6px;
}

.sidebar-body::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-body::-webkit-scrollbar-thumb {
  background: var(--color-border-primary);
  border-radius: 2px;
}

.sidebar-body::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-light);
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
}

.module-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  letter-spacing: 0;
}

.module-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.action-btn.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* 批量操作栏 */
.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-count {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 树形结构 */
.module-tree {
  background: transparent;
}

.module-tree :deep(.el-tree-node__content) {
  height: 36px;
  margin: 1px 8px;
  padding: 0 12px;
  border-radius: 2px;
  transition: all 0.15s ease;
}

.module-tree :deep(.el-tree-node__content:hover) {
  background-color: var(--color-primary-light);
}

.module-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--color-primary-light);
}

.module-tree :deep(.el-tree-node.is-current > .el-tree-node__content .node-icon) {
  color: var(--color-primary);
}

.module-tree :deep(.el-tree-node.is-current > .el-tree-node__content .node-label) {
  color: var(--color-primary);
  font-weight: 500;
}

.module-tree :deep(.el-tree-node__expand-icon) {
  color: var(--color-text-placeholder);
  font-size: 12px;
  padding: 6px;
}

.module-tree :deep(.el-tree-node__expand-icon.is-leaf) {
  color: transparent;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  overflow: hidden;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.node-icon {
  color: var(--color-warning);
  font-size: 16px;
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.node-label {
  flex: 1;
  font-size: 14px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-count {
  color: var(--color-text-tertiary);
  font-size: 12px;
  background: var(--color-bg-tertiary);
  padding: 1px 6px;
  border-radius: 2px;
  flex-shrink: 0;
  min-width: 20px;
  text-align: center;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.node-action {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.node-action:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.node-action.danger:hover {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: var(--color-border-light);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin: 0 0 16px;
}
</style>