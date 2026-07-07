<template>
  <div class="project-table-header">
    <div
      v-for="col in columns"
      :key="col.prop"
      class="column-header"
      :style="getColumnStyle(col)"
    >
      {{ col.label }}
    </div>
  </div>
</template>

<script setup>
/**
 * ProjectTableHeader - 项目表格头部组件
 * @property {Array} columns - 列配置数组
 */
defineProps({
  columns: {
    type: Array,
    required: true
  }
})

const getColumnStyle = (col) => {
  if (col.flexGrow) {
    return { flexGrow: col.flexGrow, minWidth: `${col.minWidth}px` }
  }
  return { width: `${col.width}px`, flexShrink: 0 }
}
</script>

<style scoped>
.project-table-header {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  position: sticky;
  z-index: 10;
  background: #fff;
  box-sizing: border-box;
  top: 0;
  padding: 0 24px;
}

.column-header {
  color: rgba(32, 45, 64, 0.6);
  font-size: 12px;
  box-sizing: border-box;
  padding-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.column-header:first-child {
  justify-content: flex-start;
}
</style>
