<template>
  <div class="skeleton-container">
    <!-- 项目卡片骨架屏 -->
    <div v-if="type === 'card'" class="project-card-item skeleton-card">
      <div class="card-top">
        <div class="skeleton-avatar" />
        <div class="skeleton-content">
          <div class="skeleton-line" />
          <div class="skeleton-line skeleton-line-short" />
        </div>
        <div class="skeleton-circle" />
      </div>
      <div class="card-bottom">
        <div class="skeleton-links">
          <div class="skeleton-circle skeleton-circle-small" />
          <div class="skeleton-circle skeleton-circle-small" />
          <div class="skeleton-circle skeleton-circle-small" />
        </div>
        <div class="skeleton-circle" />
      </div>
    </div>

    <!-- 表格行骨架屏 -->
    <div v-else-if="type === 'table'" class="table-row skeleton-row">
      <div class="row-content">
        <div class="column-header" style="flex-grow: 1; min-width: 150px">
          <div class="column-title">
            <div class="project-link">
              <div class="skeleton-avatar skeleton-avatar-small" />
              <div class="project-info">
                <div class="project-identifier">
                  <div class="skeleton-line" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="column-header" style="width: 272px; flex-shrink: 0">
          <div class="skeleton-links">
            <div class="skeleton-circle skeleton-circle-small" />
            <div class="skeleton-circle skeleton-circle-small" />
            <div class="skeleton-circle skeleton-circle-small" />
          </div>
        </div>
        <div class="column-header" style="width: 148px; flex-shrink: 0">
          <div class="project-owner">
            <div class="owner-wrapper">
              <div class="skeleton-avatar skeleton-avatar-small" />
              <div class="skeleton-circle skeleton-circle-small" />
            </div>
          </div>
        </div>
        <div class="column-header" style="width: 44px; flex-shrink: 0">
          <div class="skeleton-circle" />
        </div>
        <div class="column-header" style="width: 44px; flex-shrink: 0">
          <div class="skeleton-circle" />
        </div>
      </div>
    </div>

    <!-- 多个骨架屏 -->
    <div v-else-if="type === 'multiple'" class="multiple-skeletons">
      <div 
        v-for="i in count" 
        :key="`skeleton-${i}`"
        class="project-card-item skeleton-card"
      >
        <div class="card-top">
          <div class="skeleton-avatar" />
          <div class="skeleton-content">
            <div class="skeleton-line" />
            <div class="skeleton-line skeleton-line-short" />
          </div>
          <div class="skeleton-circle" />
        </div>
        <div class="card-bottom">
          <div class="skeleton-links">
            <div class="skeleton-circle skeleton-circle-small" />
            <div class="skeleton-circle skeleton-circle-small" />
            <div class="skeleton-circle skeleton-circle-small" />
          </div>
          <div class="skeleton-circle" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'card',
    validator: (value) => ['card', 'table', 'multiple'].includes(value)
  },
  count: {
    type: Number,
    default: 3
  }
})
</script>

<style scoped>
.skeleton-container {
  padding: 16px 0;
}

.skeleton-card {
  opacity: 0.7;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  background: var(--color-bg-tertiary);
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-avatar-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-content {
  flex: 1;
  margin: 0 12px;
}

.skeleton-line {
  height: 16px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  margin-bottom: 8px;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-line-short {
  width: 70%;
}

.skeleton-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-circle-small {
  width: 20px;
  height: 20px;
}

.skeleton-links {
  display: flex;
  gap: 8px;
}

.skeleton-row {
  opacity: 0.7;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.multiple-skeletons {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

/* 项目卡片样式 */
.project-card-item {
  margin-right: 16px;
  margin-bottom: 16px;
  width: 256px;
  min-width: 256px;
  padding: 0 16px;
  background: #fff;
  box-shadow:
    0 0 0 1px rgba(218, 223, 230, 0.5),
    0 0 3px 0 rgba(0, 0, 0, 0.12);
  border-radius: 2px;
  cursor: pointer;
}

.card-top {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 0;
}

.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--color-bg-tertiary);
}

/* 表格样式 */
.table-row {
  width: 100%;
  height: 56px;
  padding: 0 24px;
  box-sizing: border-box;
}

.row-content {
  box-shadow: 0 1px 0 0 var(--color-bg-tertiary);
  width: 100%;
  height: 100%;
  display: flex;
  align-items: stretch;
}

.column-header {
  color: rgba(32, 45, 64, 0.6);
  font-size: 12px;
  box-sizing: border-box;
  padding-right: 12px;
  display: flex;
  align-items: center;
}

.project-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  width: 100%;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-identifier {
  display: flex;
  align-items: center;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>