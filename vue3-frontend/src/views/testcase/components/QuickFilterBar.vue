<template>
  <div class="quick-filter-bar">
    <div class="filter-tags">
      <div
        v-for="filter in filters"
        :key="filter.key"
        class="filter-tag"
        :class="{ active: activeFilter === filter.key }"
        @click="handleClick(filter.key)"
      >
        <span class="tag-label">{{ filter.label }}</span>
        <span class="tag-count">{{ filter.count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  filters: {
    type: Array,
    default: () => []
  },
  activeFilter: {
    type: String,
    default: 'all'
  }
})

const emit = defineEmits(['change'])

const handleClick = (key) => {
  emit('change', key)
}
</script>

<style scoped>
.quick-filter-bar {
  margin-top: 12px;
}

.filter-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.filter-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filter-tag.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.tag-label {
  font-weight: 500;
}

.tag-count {
  padding: 2px 6px;
  background: var(--color-bg-secondary);
  border-radius: 2px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.filter-tag.active .tag-count {
  background: var(--color-primary);
  color: #fff;
}
</style>
