<template>
  <div class="manage-page">
    <div class="page-header">
      <div class="header-left">
        <span class="title">环境管理</span>
      </div>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>
        新建环境
      </el-button>
    </div>

    <div class="page-content">
      <div v-if="loading" class="loading-box">
        <div class="spinner"></div>
      </div>

      <div v-else-if="list.length === 0" class="empty-box">
        <el-icon :size="48"><Monitor /></el-icon>
        <p>暂无测试环境</p>
        <el-button type="primary" @click="openDialog()">新建环境</el-button>
      </div>

      <div v-else class="data-list">
        <div class="list-head">
          <span class="col-name">环境名称</span>
          <span class="col-type">类型</span>
          <span class="col-target">用途</span>
          <span class="col-url">Base URL</span>
          <span class="col-default">默认</span>
          <span class="col-action">操作</span>
        </div>
        <div class="list-body">
          <div v-for="item in list" :key="item.id" class="list-row">
            <span class="col-name">
              <el-icon class="icon-env"><Monitor /></el-icon>
              {{ item.name }}
            </span>
            <span class="col-type">{{ getEnvTypeLabel(item.env_type) }}</span>
            <span class="col-target">
              <el-tag :type="item.target_type === 'web' ? 'warning' : 'info'" size="small" effect="light">
                {{ getTargetTypeLabel(item.target_type) }}
              </el-tag>
            </span>
            <span class="col-url">{{ item.base_url || '-' }}</span>
            <span class="col-default">
              <el-tag v-if="item.is_default" type="success" size="small">默认</el-tag>
            </span>
            <span class="col-action">
              <a v-if="!item.is_default" @click="setDefault(item)">设为默认</a>
              <a @click="openDialog(item)">编辑</a>
              <a v-if="!item.is_default" class="danger" @click="deleteItem(item)">删除</a>
            </span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑环境' : '新建环境'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="环境名称" required>
          <el-input v-model="form.name" placeholder="如: 测试环境" />
        </el-form-item>
        <el-form-item label="环境类型">
          <el-select v-model="form.env_type" style="width: 100%">
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="test" />
            <el-option label="预发布环境" value="staging" />
            <el-option label="生产环境" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="用途">
          <el-select v-model="form.target_type" style="width: 100%">
            <el-option label="接口测试" value="api" />
            <el-option label="Web 自动化" value="web" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL" required>
          <el-input v-model="form.base_url" placeholder="如: http://api.example.com" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="环境描述（可选）" />
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
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Monitor } from '@element-plus/icons-vue'
import { environmentApi } from '@/api/modules/apitest'

const route = useRoute()
const projectId = computed(() => route.params.code || route.params.id)

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ name: '', env_type: 'test', target_type: 'api', base_url: '', description: '' })

const ENV_TYPE_LABELS = {
  dev: '开发环境',
  test: '测试环境',
  staging: '预发布',
  prod: '生产环境'
}

const TARGET_TYPE_LABELS = {
  api: '接口测试',
  web: 'Web 自动化'
}

const getEnvTypeLabel = (type) => ENV_TYPE_LABELS[type] || type
const getTargetTypeLabel = (type) => TARGET_TYPE_LABELS[type] || type

const fetchData = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await environmentApi.getEnvironments({ project: projectId.value })
    list.value = res?.results || res || []
  } catch (e) {

  } finally {
    loading.value = false
  }
}

const openDialog = (item = null) => {
  editing.value = item
  form.name = item?.name || ''
  form.env_type = item?.env_type || 'test'
  form.target_type = item?.target_type || 'api'
  form.base_url = item?.base_url || ''
  form.description = item?.description || ''
  dialogVisible.value = true
}

const setDefault = async (item) => {
  try {
    await environmentApi.setDefault(item.id)
    ElMessage.success('已设为默认')
    fetchData()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const deleteItem = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除「${item.name}」？`, '提示', { type: 'warning' })
    await environmentApi.deleteEnvironment(item.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

const submit = async () => {
  if (!form.name.trim()) return ElMessage.warning('请输入环境名称')
  if (!form.base_url.trim()) return ElMessage.warning('请输入 Base URL')
  submitting.value = true
  try {
    const data = {
      name: form.name.trim(),
      env_type: form.env_type,
      target_type: form.target_type,
      base_url: form.base_url.trim(),
      description: form.description,
      project: projectId.value
    }
    if (editing.value) {
      await environmentApi.updateEnvironment(editing.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await environmentApi.createEnvironment(data)
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

onMounted(() => fetchData())
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

.col-name {
  flex: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.icon-env {
  color: #1890ff;
  flex-shrink: 0;
}

.col-type {
  width: 100px;
  color: #8c8c8c;
}

.col-target {
  width: 110px;
}

.col-url {
  flex: 3;
  color: #8c8c8c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 16px;
}

.col-default {
  width: 80px;
  text-align: center;
}

.col-action {
  width: 160px;
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

.col-action a.danger {
  color: #ff4d4f;
}

.col-action a.danger:hover {
  color: #ff7875;
}
</style>
