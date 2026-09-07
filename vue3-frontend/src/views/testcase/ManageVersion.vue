<template>
  <div class="manage-page">
    <div class="page-header">
      <div class="header-left">
        <span class="back-link" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </span>
        <span class="title">版本管理</span>
        <span class="repo-badge">{{ repoName || '加载中...' }}</span>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>
        新建版本
      </el-button>
    </div>

    <div class="page-content">
      <div v-if="loading" class="loading-box">
        <div class="spinner"></div>
      </div>

      <div v-else-if="list.length === 0" class="empty-box">
        <el-icon :size="48"><PriceTag /></el-icon>
        <p>暂无版本</p>
        <el-button type="primary" @click="openDialog()">新建版本</el-button>
      </div>

      <div v-else class="data-list">
        <div class="list-head">
          <span class="col-name">名称</span>
          <span class="col-status">状态</span>
          <span class="col-desc">描述</span>
          <span class="col-time">创建时间</span>
          <span class="col-action">操作</span>
        </div>
        <div class="list-body">
          <div v-for="item in list" :key="item.id" class="list-row" :class="{ archived: item.status === 'archived' }">
            <span class="col-name">
              <el-icon class="icon-tag"><PriceTag /></el-icon>
              {{ item.name }}
            </span>
            <span class="col-status">
              <el-tag v-if="item.is_default" type="success" size="small">默认</el-tag>
              <el-tag v-else-if="item.status === 'archived'" type="info" size="small">已归档</el-tag>
              <el-tag v-else type="primary" size="small" effect="plain">活跃</el-tag>
            </span>
            <span class="col-desc">{{ item.description || '-' }}</span>
            <span class="col-time">{{ formatDate(item.created_at) }}</span>
            <span class="col-action">
              <a @click="openDialog(item)">编辑</a>
              <a v-if="!item.is_default" @click="setDefault(item)">设为默认</a>
              <a v-if="item.status === 'active'" class="warning" @click="archive(item)">归档</a>
              <a v-else class="success" @click="activate(item)">激活</a>
              <a v-if="!item.is_default" class="danger" @click="deleteItem(item)">删除</a>
            </span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑版本' : '新建版本'" width="440px" destroy-on-close>
      <el-form :model="form" label-width="70px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="请输入版本名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft, PriceTag } from '@element-plus/icons-vue'
import { versionApi, repositoryApi } from '@/api/modules/testcase'
import { useProjectStore } from '@/stores/modules/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const repoId = computed(() => route.query.repo)
const repoName = ref('')

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ name: '', description: '' })

const fetchData = async () => {
  if (!repoId.value) return
  loading.value = true
  try {
    const res = await versionApi.getVersions({ repository: repoId.value })
    list.value = res?.results || res || []
  } catch (e) {

  } finally {
    loading.value = false
  }
}

const fetchRepoInfo = async () => {
  if (!repoId.value) return
  try {
    const res = await repositoryApi.getRepository(repoId.value)
    repoName.value = res?.name || ''
  } catch (e) {

  }
}

const openDialog = (item = null) => {
  editing.value = item
  form.name = item?.name || ''
  form.description = item?.description || ''
  dialogVisible.value = true
}

const setDefault = async (item) => {
  try {
    await versionApi.setDefaultVersion(item.id)
    ElMessage.success('已设为默认')
    fetchData()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const archive = async (item) => {
  try {
    await versionApi.updateVersion(item.id, { status: 'archived' })
    ElMessage.success('已归档')
    fetchData()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const activate = async (item) => {
  try {
    await versionApi.updateVersion(item.id, { status: 'active' })
    ElMessage.success('已激活')
    fetchData()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const deleteItem = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除「${item.name}」？`, '提示', { type: 'warning' })
    await versionApi.deleteVersion(item.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

const submit = async () => {
  if (!form.name.trim()) return ElMessage.warning('请输入名称')
  submitting.value = true
  try {
    if (editing.value) {
      await versionApi.updateVersion(editing.value.id, { name: form.name.trim(), description: form.description })
      ElMessage.success('更新成功')
    } else {
      await versionApi.createVersion({
        name: form.name.trim(),
        description: form.description,
        repository: repoId.value,
        is_default: list.value.length === 0
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const formatDate = (str) => {
  if (!str) return '-'
  const d = new Date(str)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  fetchData()
  fetchRepoInfo()
})
</script>

<style scoped>
.manage-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f6f8;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  cursor: pointer;
  font-size: 14px;
}

.back-link:hover {
  color: #1890ff;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.repo-badge {
  padding: 4px 12px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
}

.page-content {
  flex: 1;
  padding: 0;
  overflow: auto;
}

.loading-box {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e6e6e6;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  background: #fff;
  border-radius: 0;
  color: #bfbfbf;
}

.empty-box p {
  margin: 16px 0;
  color: #8c8c8c;
}

.data-list {
  background: #fff;
  border-radius: 0;
  overflow: hidden;
}

.list-head {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  background: #fafafa;
  border-bottom: 1px solid #e6e6e6;
  font-size: 13px;
  color: #8c8c8c;
  font-weight: 500;
}

.list-body {
  display: flex;
  flex-direction: column;
}

.list-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  transition: background 0.2s;
}

.list-row:last-child {
  border-bottom: none;
}

.list-row:hover {
  background: #fafafa;
}

.list-row.archived {
  opacity: 0.6;
}

.col-name {
  flex: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.icon-tag {
  color: #1890ff;
  flex-shrink: 0;
}

.col-status {
  width: 80px;
}

.col-desc {
  flex: 3;
  color: #8c8c8c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 16px;
}

.col-time {
  width: 110px;
  color: #8c8c8c;
}

.col-action {
  width: 200px;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.col-action a {
  color: #1890ff;
  cursor: pointer;
}

.col-action a:hover {
  color: #40a9ff;
}

.col-action a.warning {
  color: #faad14;
}

.col-action a.success {
  color: #52c41a;
}

.col-action a.danger {
  color: #ff4d4f;
}
</style>
