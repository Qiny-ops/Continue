<template>
  <el-dialog
    :model-value="visible"
    title="管理版本"
    width="640px"
    destroy-on-close
    :close-on-click-modal="false"
    class="manage-dialog"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="dialog-content">
      <!-- 新建输入 -->
      <div class="create-row">
        <el-input
          v-model="newVersionName"
          placeholder="输入版本名称"
          maxlength="100"
          @keyup.enter="handleCreate"
        />
        <el-button type="primary" :loading="creating" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建
        </el-button>
      </div>

      <!-- 列表 -->
      <div class="list-container">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner" />
        </div>

        <div v-else-if="list.length === 0" class="empty-state">
          <p>暂无版本</p>
        </div>

        <div v-else class="version-list">
          <div
            v-for="item in list"
            :key="item.id"
            class="version-item"
          >
            <div class="item-main">
              <el-icon class="item-icon"><PriceTag /></el-icon>
              <div class="item-info">
                <div class="item-name">{{ item.name }}</div>
                <div class="item-meta">
                  <span>{{ item.status === 'active' ? '活跃' : '已归档' }}</span>
                  <span>{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
            </div>
            <div class="item-actions">
              <el-tag v-if="item.is_default" type="success" size="small">默认</el-tag>
              <el-button
                v-else
                type="primary"
                link
                size="small"
                @click="handleSetDefault(item)"
              >
                设为默认
              </el-button>
              <el-button
                v-if="item.status === 'active'"
                type="warning"
                link
                size="small"
                @click="handleArchive(item)"
              >
                归档
              </el-button>
              <el-button
                v-else
                type="success"
                link
                size="small"
                @click="handleActivate(item)"
              >
                激活
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                :disabled="item.is_default"
                @click="handleDelete(item)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, PriceTag } from '@element-plus/icons-vue'
import { versionApi } from '@/api/modules/testcase'

const props = defineProps({
  visible: Boolean,
  repoId: { type: [String, Number], default: null }
})

const emit = defineEmits(['update:visible', 'refresh'])

const loading = ref(false)
const creating = ref(false)
const list = ref([])
const newVersionName = ref('')

const fetchList = async () => {
  if (!props.repoId) return
  loading.value = true
  try {
    const res = await versionApi.getVersions({ repository: props.repoId })
    list.value = res?.results || res || []
  } catch (e) {

  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!newVersionName.value.trim()) {
    ElMessage.warning('请输入版本名称')
    return
  }
  creating.value = true
  try {
    await versionApi.createVersion({
      name: newVersionName.value.trim(),
      repository: props.repoId,
      is_default: list.value.length === 0
    })
    ElMessage.success('创建成功')
    newVersionName.value = ''
    fetchList()
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    creating.value = false
  }
}

const handleSetDefault = async (item) => {
  try {
    await versionApi.setDefaultVersion(item.id)
    ElMessage.success('已设为默认')
    fetchList()
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const handleArchive = async (item) => {
  try {
    await versionApi.updateVersion(item.id, { status: 'archived' })
    ElMessage.success('已归档')
    fetchList()
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const handleActivate = async (item) => {
  try {
    await versionApi.updateVersion(item.id, { status: 'active' })
    ElMessage.success('已激活')
    fetchList()
    emit('refresh')
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm(`确定要删除版本"${item.name}"吗？删除后不可恢复。`, '提示', { type: 'warning' })
    await versionApi.deleteVersion(item.id)
    ElMessage.success('删除成功')
    fetchList()
    emit('refresh')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const formatDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

watch(() => props.visible, (v) => {
  if (v) fetchList()
})
</script>

<style scoped>
.manage-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.dialog-content {
  padding: 16px 20px;
}

.create-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.create-row .el-input {
  flex: 1;
}

.list-container {
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--color-border-secondary);
  border-radius: 2px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border-primary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-tertiary);
}

.version-list {
  display: flex;
  flex-direction: column;
}

.version-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.version-item:last-child {
  border-bottom: none;
}

.version-item:hover {
  background: var(--color-bg-secondary);
}

.item-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.item-icon {
  font-size: 20px;
  color: var(--color-primary);
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  gap: 16px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>