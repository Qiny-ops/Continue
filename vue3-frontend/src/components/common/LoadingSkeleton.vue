<template>
  <div class="loading-skeleton">
    <!-- 卡片骨架屏 -->
    <template v-if="type === 'card'">
      <div class="skeleton-card" :style="{ width: cardWidth }">
        <div class="skeleton-header">
          <div class="skeleton-avatar" />
          <div class="skeleton-title" />
        </div>
        <div class="skeleton-body">
          <div class="skeleton-line" style="width: 80%" />
          <div class="skeleton-line" style="width: 60%" />
        </div>
        <div class="skeleton-footer">
          <div class="skeleton-tag" />
          <div class="skeleton-tag" />
        </div>
      </div>
    </template>

    <!-- 表格行骨架屏 -->
    <template v-else-if="type === 'table-row'">
      <div class="skeleton-table-row">
        <div class="skeleton-cell" v-for="i in columns" :key="i" :style="getCellStyle(i)" />
      </div>
    </template>

    <!-- 列表项骨架屏 -->
    <template v-else-if="type === 'list-item'">
      <div class="skeleton-list-item">
        <div class="skeleton-avatar" />
        <div class="skeleton-content">
          <div class="skeleton-line" style="width: 70%" />
          <div class="skeleton-line short" style="width: 40%" />
        </div>
      </div>
    </template>

    <!-- 多卡片骨架屏 -->
    <template v-else-if="type === 'multiple'">
      <div class="skeleton-multiple">
        <div v-for="i in count" :key="i" class="skeleton-card" :style="{ width: cardWidth }">
          <div class="skeleton-header">
            <div class="skeleton-avatar" />
            <div class="skeleton-title" />
          </div>
          <div class="skeleton-body">
            <div class="skeleton-line" style="width: 80%" />
            <div class="skeleton-line" style="width: 60%" />
          </div>
          <div class="skeleton-footer">
            <div class="skeleton-tag" />
            <div class="skeleton-tag" />
          </div>
        </div>
      </div>
    </template>

    <!-- 文本骨架屏 -->
    <template v-else-if="type === 'text'">
      <div class="skeleton-text">
        <div class="skeleton-line" :style="{ width: textWidth }" />
      </div>
    </template>

    <!-- 默认骨架屏 -->
    <template v-else>
      <div class="skeleton-default">
        <div class="skeleton-line" />
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * LoadingSkeleton - 统一的骨架屏组件
 * @property {string} type - 骨架屏类型: card | table-row | list-item | multiple | text
 * @property {number} count - 数量（用于 multiple 类型）
 * @property {number} columns - 列数（用于 table-row 类型）
 * @property {string} cardWidth - 卡片宽度
 * @property {string} textWidth - 文本宽度
 */
defineProps({
  type: {
    type: String,
    default: 'text',
    validator: (value) => ['card', 'table-row', 'list-item', 'multiple', 'text'].includes(value)
  },
  count: {
    type: Number,
    default: 3
  },
  columns: {
    type: Number,
    default: 5
  },
  cardWidth: {
    type: String,
    default: '280px'
  },
  textWidth: {
    type: String,
    default: '100%'
  }
})

const getCellStyle = (index) => {
  const widths = ['40%', '20%', '15%', '15%', '10%']
  return { width: widths[(index - 1) % widths.length] }
}
</script>

<style scoped>
.loading-skeleton {
  width: 100%;
}

/* 骨架屏动画 */
.skeleton-card,
.skeleton-avatar,
.skeleton-title,
.skeleton-line,
.skeleton-tag,
.skeleton-cell,
.skeleton-content {
  background: var(--color-bg-tertiary);
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 2px;
}

@keyframes skeleton-loading {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

/* 卡片骨架屏 */
.skeleton-card {
  padding: 16px;
  border-radius: 2px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  flex-shrink: 0;
}

.skeleton-title {
  flex: 1;
  height: 20px;
}

.skeleton-body {
  margin-bottom: 16px;
}

.skeleton-line {
  height: 14px;
  margin-bottom: 8px;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-line:last-child {
  margin-bottom: 0;
}

.skeleton-footer {
  display: flex;
  gap: 8px;
}

.skeleton-tag {
  width: 60px;
  height: 24px;
  border-radius: 2px;
}

/* 表格行骨架屏 */
.skeleton-table-row {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  gap: 16px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.skeleton-cell {
  height: 16px;
}

/* 列表项骨架屏 */
.skeleton-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.skeleton-content {
  flex: 1;
}

/* 多卡片骨架屏 */
.skeleton-multiple {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

/* 文本骨架屏 */
.skeleton-text {
  width: 100%;
}

/* 默认骨架屏 */
.skeleton-default {
  width: 100%;
}
</style>
