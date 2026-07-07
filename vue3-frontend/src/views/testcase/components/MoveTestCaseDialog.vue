<template>
  <el-dialog
    v-model="visible"
    title="移动用例"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="move-dialog-content">
      <p class="move-tip">
        已选择 <strong>{{ testCases.length }}</strong> 个用例，请选择目标模块：
      </p>
      <el-tree
        :data="moduleTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        highlight-current
        @node-click="handleNodeClick"
        class="module-tree"
      />
    </div>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :disabled="!selectedTarget" @click="handleConfirm">
        确认移动
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  testCases: {
    type: Array,
    default: () => []
  },
  moduleTree: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'confirm'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const selectedTarget = ref(null)

const handleNodeClick = (data) => {
  selectedTarget.value = data.id
}

const handleConfirm = () => {
  emit('confirm', selectedTarget.value)
  selectedTarget.value = null
}
</script>

<style scoped>
.move-dialog-content {
  padding: 10px 0;
}

.move-tip {
  margin-bottom: 16px;
  color: var(--color-text-secondary);
}

.module-tree {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  padding: 8px;
}
</style>
