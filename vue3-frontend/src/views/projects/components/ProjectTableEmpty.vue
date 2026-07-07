<template>
  <div class="table-empty">
    <div class="empty-content">
      <div class="empty-icon"></div>
      <span class="empty-text">{{ message }}</span>
    </div>
    <div class="bottom-create">
      <div class="create-btn" @click="$emit('action')">
        <div class="add-icon"></div>
        创建项目
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  columns: {
    type: Array,
    default: () => []
  },
  message: {
    type: String,
    default: '暂无数据'
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  showAction: {
    type: Boolean,
    default: true
  },
  actionText: {
    type: String,
    default: '创建项目'
  }
})

defineEmits(['action'])
</script>

<style scoped>
.table-empty {
  width: 100%;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px 40px;
  gap: 16px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect x='30' y='50' width='140' height='100' rx='8' fill='%23f1f5f9' stroke='%23e2e8f0' stroke-width='2'/%3E%3Crect x='50' y='30' width='100' height='20' rx='4' fill='%23e2e8f0'/%3E%3Crect x='50' y='80' width='80' height='8' rx='2' fill='%23cbd5e1'/%3E%3Crect x='50' y='100' width='60' height='8' rx='2' fill='%23cbd5e1'/%3E%3Crect x='50' y='120' width='40' height='8' rx='2' fill='%23cbd5e1'/%3E%3C/svg%3E") center/contain no-repeat;
  opacity: 0.8;
}

.empty-text {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.bottom-create {
  padding: 4px 8px;
  border-top: 1px solid var(--color-border-primary);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 8px 12px;
  background: transparent;
  color: var(--color-text-secondary);
  border: 2px dashed var(--color-border-primary);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.create-btn:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary-hover);
  color: var(--color-primary-hover);
}

.create-btn:active {
  background: var(--color-primary-light);
}

.add-icon {
  width: 18px;
  height: 18px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230066cc'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  transition: transform 0.25s ease;
}

.create-btn:hover .add-icon {
  transform: rotate(90deg);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230052a3'%3E%3Cpath d='M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z'/%3E%3C/svg%3E");
}
</style>
