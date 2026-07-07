<template>
  <div class="base-tree">
    <div class="tree-header">
      <div class="header-title" @click="handleShowAll">
        <el-icon class="title-icon"><FolderOpened /></el-icon>
        <span class="title-text">{{ rootTitle }}</span>
        <span v-if="totalCount !== undefined" class="title-count">{{ totalCount }}</span>
      </div>
      <div class="header-actions">
        <el-tooltip :content="isAllExpanded ? '收起全部' : '展开全部'" placement="top">
          <span class="action-btn" @click="toggleExpandAll">
            <el-icon><Sort /></el-icon>
          </span>
        </el-tooltip>
        <el-tooltip v-if="showAddButton" content="添加" placement="top">
          <span class="action-btn primary" @click="$emit('addRoot')">
            <el-icon><Plus /></el-icon>
          </span>
        </el-tooltip>
      </div>
    </div>

    <div class="tree-body">
      <el-tree
        v-if="treeData?.length"
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :node-key="nodeKey"
        :highlight-current="highlightCurrent"
        :expand-on-click-node="expandOnClickNode"
        :default-expand-all="defaultExpandAll"
        class="module-tree"
        @node-click="handleNodeClick"
      >
        <template #default="{ data }">
          <div
            class="tree-node"
            @mouseenter="hoverNodeId = data[nodeKey]"
            @mouseleave="hoverNodeId = null"
          >
            <div class="node-content">
              <el-icon class="node-icon" :class="{ 'is-folder': hasChildren(data) }">
                <Folder v-if="hasChildren(data)" />
                <Document v-else />
              </el-icon>
              <span class="node-label">{{ getNodeLabel(data) }}</span>
              <span v-if="showCount && data.count !== undefined" class="node-count">
                {{ data.count }}
              </span>
            </div>
            <div
              v-show="hoverNodeId === data[nodeKey] && showActions"
              class="node-actions"
              @click.stop
            >
              <span
                v-if="showAddChild"
                class="node-action"
                title="添加子项"
                @click="$emit('addChild', data)"
              >
                <el-icon><Plus /></el-icon>
              </span>
              <span
                v-if="showEdit"
                class="node-action"
                title="编辑"
                @click="$emit('edit', data)"
              >
                <el-icon><Edit /></el-icon>
              </span>
              <span
                v-if="showDelete"
                class="node-action danger"
                title="删除"
                @click="$emit('delete', data)"
              >
                <el-icon><Delete /></el-icon>
              </span>
            </div>
          </div>
        </template>
      </el-tree>

      <div v-if="!treeData?.length && !loading" class="empty-state">
        <el-icon class="empty-icon"><FolderOpened /></el-icon>
        <p class="empty-text">{{ emptyText }}</p>
        <el-button v-if="showAddButton" type="primary" size="small" @click="$emit('addRoot')">
          <el-icon><Plus /></el-icon>
          {{ addButtonText }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * BaseTree - 统一的树形基础组件
 * @property {Array} treeData - 树形数据
 * @property {string} rootTitle - 根节点标题
 * @property {number} totalCount - 总数量
 * @property {boolean} loading - 加载状态
 * @property {string} nodeKey - 节点唯一标识字段
 * @property {string} labelField - 标签字段名
 * @property {string} childrenField - 子节点字段名
 * @property {boolean} highlightCurrent - 高亮当前节点
 * @property {boolean} expandOnClickNode - 点击节点展开
 * @property {boolean} defaultExpandAll - 默认展开所有
 * @property {boolean} showCount - 显示数量
 * @property {boolean} showActions - 显示操作按钮
 * @property {boolean} showAddButton - 显示添加按钮
 * @property {boolean} showAddChild - 显示添加子项按钮
 * @property {boolean} showEdit - 显示编辑按钮
 * @property {boolean} showDelete - 显示删除按钮
 * @property {string} emptyText - 空状态文字
 * @property {string} addButtonText - 添加按钮文字
 */
import { ref, computed } from 'vue'
import { Plus, Folder, FolderOpened, Document, Edit, Delete, Sort } from '@element-plus/icons-vue'

const props = defineProps({
  treeData: {
    type: Array,
    default: () => []
  },
  rootTitle: {
    type: String,
    default: '全部'
  },
  totalCount: {
    type: Number,
    default: undefined
  },
  loading: {
    type: Boolean,
    default: false
  },
  nodeKey: {
    type: String,
    default: 'id'
  },
  labelField: {
    type: String,
    default: 'name'
  },
  childrenField: {
    type: String,
    default: 'children'
  },
  highlightCurrent: {
    type: Boolean,
    default: true
  },
  expandOnClickNode: {
    type: Boolean,
    default: false
  },
  defaultExpandAll: {
    type: Boolean,
    default: false
  },
  showCount: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  showAddButton: {
    type: Boolean,
    default: true
  },
  showAddChild: {
    type: Boolean,
    default: true
  },
  showEdit: {
    type: Boolean,
    default: true
  },
  showDelete: {
    type: Boolean,
    default: true
  },
  emptyText: {
    type: String,
    default: '暂无数据'
  },
  addButtonText: {
    type: String,
    default: '添加'
  }
})

const emit = defineEmits([
  'nodeClick',
  'showAll',
  'addRoot',
  'addChild',
  'edit',
  'delete'
])

const hoverNodeId = ref(null)
const treeRef = ref(null)
const isAllExpanded = ref(false)

const treeProps = computed(() => ({
  label: props.labelField,
  children: props.childrenField
}))

const hasChildren = (data) => {
  const children = data[props.childrenField]
  return children && children.length > 0
}

const getNodeLabel = (data) => data[props.labelField]

const handleShowAll = () => {
  emit('showAll')
}

const handleNodeClick = (data) => {
  emit('nodeClick', data)
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

defineExpose({
  toggleExpandAll,
  treeRef
})
</script>

<style scoped>
.base-tree {
  width: 260px;
  height: 100%;
  background: #fff;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-secondary);
  background: var(--color-bg-secondary);
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 10px;
  margin: -6px -10px;
  border-radius: 2px;
  transition: all 0.2s ease;
}

.header-title:hover {
  background: var(--color-primary-light);
}

.header-title:hover .title-icon {
  color: var(--color-primary);
}

.title-icon {
  color: var(--color-text-tertiary);
  font-size: 16px;
  transition: color 0.2s ease;
}

.title-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.title-count {
  color: var(--color-text-tertiary);
  font-size: 12px;
  background: var(--color-bg-tertiary);
  padding: 2px 8px;
  border-radius: 2px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.action-btn.primary:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.tree-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 8px 0;
}

.module-tree {
  background: transparent;
}

.module-tree :deep(.el-tree-node__content) {
  height: 36px;
  margin: 2px 8px;
  padding: 0 8px;
  border-radius: 2px;
  transition: all 0.2s ease;
}

.module-tree :deep(.el-tree-node__content:hover) {
  background-color: var(--color-bg-tertiary);
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
  transition: color 0.2s ease;
}

.node-icon.is-folder {
  color: var(--color-warning);
}

.node-label {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-primary);
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
