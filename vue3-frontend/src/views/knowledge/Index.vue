<template>
  <div class="knowledge-wrapper">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="28"><Loading /></el-icon>
      <span>加载中</span>
    </div>

    <!-- 未关联知识库 -->
    <div v-else-if="!knowledgeBase" class="unlinked-state">
      <div class="unlinked-icon">
        <el-icon :size="48"><Collection /></el-icon>
      </div>
      <h2>项目知识库</h2>
      <p>关联知识库后可管理项目文档和知识内容</p>
      <div class="unlinked-actions">
        <el-button type="primary" size="large" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建知识库
        </el-button>
        <el-button size="large" @click="showLinkDialog">
          <el-icon><Connection /></el-icon>
          关联已有
        </el-button>
      </div>
    </div>

    <!-- 已关联知识库 -->
    <div v-else class="linked-state">
      <!-- 顶部信息条 -->
      <div class="kb-header-bar">
        <div class="kb-info">
          <el-icon :size="20"><Collection /></el-icon>
          <span class="kb-name">{{ knowledgeBase.name }}</span>
          <span class="kb-meta">{{ knowledgeBase.knowledgeCount || 0 }} 文档 · {{ knowledgeBase.chunkCount || 0 }} 片段</span>
        </div>
        <div class="kb-header-actions">
          <el-button text @click="refreshData" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button text type="danger" @click="handleUnlink">
            <el-icon><SwitchButton /></el-icon>
            解除关联
          </el-button>
        </div>
      </div>

      <!-- 操作区 -->
      <div class="kb-toolbar">
        <div class="toolbar-left">
          <el-upload
            ref="uploadRef"
            :show-file-list="false"
            :http-request="handleFileUpload"
            accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.xls,.ppt,.pptx"
            multiple
          >
            <el-button type="primary" :loading="uploading">
              <el-icon><Upload /></el-icon>
              上传
            </el-button>
          </el-upload>
          <el-button @click="showAddUrlDialog">
            <el-icon><Link /></el-icon>
            URL
          </el-button>
          <el-button @click="showAddManualDialog">
            <el-icon><EditPen /></el-icon>
            新建
          </el-button>
          <el-button v-if="selectedDocs.length > 0" type="danger" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            删除 ({{ selectedDocs.length }})
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-input v-model="searchKeyword" placeholder="搜索文档" :prefix-icon="Search" clearable style="width: 200px" @input="debounceSearch" />
          <el-select v-model="typeFilter" placeholder="类型" clearable style="width: 100px" @change="handleFilterChange">
            <el-option label="文件" value="file" />
            <el-option label="链接" value="url" />
            <el-option label="文档" value="manual" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 100px" @change="handleFilterChange">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
      </div>

      <!-- 上传进度条 -->
      <div v-if="uploading" class="upload-progress-bar">
        <el-progress :percentage="uploadProgress" :stroke-width="4" />
        <span class="upload-text">正在上传 {{ uploadFileName }}...</span>
      </div>

      <!-- 文档表格 -->
      <div class="kb-table-wrapper" v-loading="tableLoading">
        <table class="kb-table">
          <thead>
            <tr>
              <th style="width: 40px">
                <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll" />
              </th>
              <th style="width: 40%">文档</th>
              <th style="width: 15%">类型</th>
              <th style="width: 15%">状态</th>
              <th style="width: 15%">时间</th>
              <th style="width: 15%">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="documents.length === 0">
              <td colspan="6" class="empty-row">
                <el-icon :size="32"><Document /></el-icon>
                <p>暂无文档</p>
                <span>点击上方按钮添加文档</span>
              </td>
            </tr>
            <tr v-for="doc in documents" :key="doc.id">
              <td>
                <el-checkbox v-model="doc._selected" @change="handleSelectChange" />
              </td>
              <td>
                <div class="doc-cell">
                  <span class="doc-icon" :class="doc.type">
                    <el-icon v-if="doc.type === 'file'"><Document /></el-icon>
                    <el-icon v-else-if="doc.type === 'url'"><Link /></el-icon>
                    <el-icon v-else><EditPen /></el-icon>
                  </span>
                  <span class="doc-name" :title="doc.title || doc.file_name">{{ doc.title || doc.file_name || '未命名' }}</span>
                </div>
              </td>
              <td>
                <span class="type-badge" :class="doc.type">{{ getTypeLabel(doc.type) }}</span>
              </td>
              <td>
                <span class="status-badge" :class="doc.parse_status">{{ getStatusLabel(doc.parse_status) }}</span>
              </td>
              <td>{{ formatDate(doc.created_at) }}</td>
              <td>
                <div class="action-cell">
                  <span class="action-link" @click="handlePreview(doc)">预览</span>
                  <span v-if="doc.parse_status === 'failed'" class="action-link" @click="handleReparse(doc)">重解析</span>
                  <span class="action-link danger" @click="handleDelete(doc)">删除</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="kb-pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建知识库" width="400px" :close-on-click-modal="false">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="可选" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 关联知识库对话框 -->
    <el-dialog v-model="linkDialogVisible" title="关联知识库" width="500px" :close-on-click-modal="false">
      <el-input v-model="kbSearchKeyword" placeholder="搜索知识库" :prefix-icon="Search" clearable style="margin-bottom: 12px" />
      <div class="kb-select-list" v-loading="kbListLoading">
        <div v-for="kb in filteredKbList" :key="kb.id" :class="['kb-select-item', { chosen: selectedKb?.id === kb.id }]" @click="selectedKb = kb">
          <span class="kb-select-name">{{ kb.name }}</span>
          <span class="kb-select-count">{{ kb.knowledge_count || 0 }} 文档</span>
          <el-icon v-if="selectedKb?.id === kb.id"><Check /></el-icon>
        </div>
        <div v-if="!filteredKbList.length && !kbListLoading" class="kb-select-empty">暂无可关联的知识库</div>
      </div>
      <template #footer>
        <el-button @click="linkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="linkLoading" :disabled="!selectedKb" @click="handleLink">关联</el-button>
      </template>
    </el-dialog>

    <!-- 添加URL对话框 -->
    <el-dialog v-model="addUrlDialogVisible" title="添加URL" width="450px" :close-on-click-modal="false">
      <el-form :model="urlForm" :rules="urlRules" ref="urlFormRef" label-position="top">
        <el-form-item label="URL地址" prop="url">
          <el-input v-model="urlForm.url" placeholder="请输入网页链接，如 https://example.com" />
        </el-form-item>
      </el-form>
      <div class="dialog-tip">
        <el-icon><InfoFilled /></el-icon>
        系统将自动抓取并解析网页内容
      </div>
      <template #footer>
        <el-button @click="addUrlDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addUrlLoading" @click="handleAddUrl">添加</el-button>
      </template>
    </el-dialog>

    <!-- 手动创建对话框 -->
    <el-dialog v-model="addManualDialogVisible" title="新建文档" width="600px" :close-on-click-modal="false">
      <el-form :model="manualForm" :rules="manualRules" ref="manualFormRef" label-position="top">
        <el-form-item label="标题" prop="title">
          <el-input v-model="manualForm.title" placeholder="请输入文档标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="manualForm.content" type="textarea" :rows="10" placeholder="支持 Markdown 格式" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addManualDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addManualLoading" @click="handleAddManual">创建</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialogVisible" :title="previewDoc?.title || previewDoc?.file_name || '文档预览'" width="800px" class="preview-dialog">
      <DocumentPreview
        :file-url="previewBlobUrl"
        :file-type="previewFileType"
        :text-content="previewTextContent"
        :loading="previewLoading"
        @download="handleDownloadPreview"
      />
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onActivated, onDeactivated } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Collection, Plus, Connection, SwitchButton, Upload, Link, EditPen,
  Search, Loading, Document, Check, Refresh, Delete, InfoFilled, Download
} from '@element-plus/icons-vue'
import {
  getProjectKnowledgeBase, linkKnowledgeBase, unlinkKnowledgeBase, createProjectKnowledgeBase
} from '@/api/modules/projectKnowledgeBase.js'
import {
  listKnowledgeBases, listKnowledge, uploadFileKnowledge,
  createUrlKnowledge, createManualKnowledge, deleteKnowledge, reparseKnowledge, previewKnowledge, downloadKnowledge
} from '@/api/modules/knowledge.js'
import DocumentPreview from '@/components/common/DocumentPreview.vue'

const route = useRoute()
const projectCode = computed(() => route.params.code || route.params.id)

// 缓存数据 - 使用模块级变量，跨组件实例共享
const cacheData = {
  knowledgeBase: new Map(),
  documents: new Map(),
  total: new Map(),
  lastProjectCode: null,
  cacheTime: new Map(),
  CACHE_TTL: 5 * 60 * 1000 // 5分钟缓存过期
}

const loading = ref(false)
const refreshing = ref(false)
const knowledgeBase = ref(null)
const documents = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const tableLoading = ref(false)

// 选择相关
const selectedDocs = ref([])
const selectAll = ref(false)
const isIndeterminate = ref(false)

// 上传相关
const uploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadFileName = ref('')

// 对话框
const createDialogVisible = ref(false)
const linkDialogVisible = ref(false)
const addUrlDialogVisible = ref(false)
const addManualDialogVisible = ref(false)
const previewDialogVisible = ref(false)

// 表单引用
const createFormRef = ref(null)
const urlFormRef = ref(null)
const manualFormRef = ref(null)

// 表单数据
const createForm = ref({ name: '', description: '' })
const urlForm = ref({ url: '' })
const manualForm = ref({ title: '', content: '' })

// 表单验证规则
const createRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }]
}
const urlRules = {
  url: [
    { required: true, message: '请输入URL地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ]
}
const manualRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

// 加载状态
const createLoading = ref(false)
const linkLoading = ref(false)
const addUrlLoading = ref(false)
const addManualLoading = ref(false)
const previewLoading = ref(false)

// 预览相关
const previewDoc = ref(null)
const previewBlobUrl = ref('')
const previewFileType = ref('')
const previewTextContent = ref('')

const kbList = ref([])
const kbListLoading = ref(false)
const kbSearchKeyword = ref('')
const selectedKb = ref(null)

// 搜索防抖定时器
let searchTimer = null

const filteredKbList = computed(() => {
  if (!kbSearchKeyword.value) return kbList.value
  return kbList.value.filter(kb => kb.name.toLowerCase().includes(kbSearchKeyword.value.toLowerCase()))
})

// 检查缓存是否过期
const isCacheValid = (code) => {
  const cacheTime = cacheData.cacheTime.get(code)
  if (!cacheTime) return false
  return Date.now() - cacheTime < cacheData.CACHE_TTL
}

const fetchKnowledgeBase = async (force = false) => {
  const code = projectCode.value
  if (!code) return

  // 检查缓存
  if (!force && cacheData.lastProjectCode === code && isCacheValid(code)) {
    const cachedKb = cacheData.knowledgeBase.get(code)
    const cachedDocs = cacheData.documents.get(code)
    const cachedTotal = cacheData.total.get(code)
    if (cachedKb !== undefined) {
      knowledgeBase.value = cachedKb
      documents.value = cachedDocs || []
      total.value = cachedTotal || 0
      updateSelectState()
      return
    }
  }

  loading.value = true
  try {
    const res = await getProjectKnowledgeBase(code)
    if (res.data) {
      knowledgeBase.value = res.data
      cacheData.knowledgeBase.set(code, res.data)
      cacheData.lastProjectCode = code
      cacheData.cacheTime.set(code, Date.now())
      await fetchDocuments(force)
    } else {
      knowledgeBase.value = null
      documents.value = []
      total.value = 0
      cacheData.knowledgeBase.set(code, null)
      cacheData.documents.set(code, [])
      cacheData.total.set(code, 0)
      cacheData.lastProjectCode = code
      cacheData.cacheTime.set(code, Date.now())
    }
  } catch (e) {
    ElMessage.error(e.message || '获取知识库失败')
  } finally {
    loading.value = false
  }
}

const fetchDocuments = async (force = false) => {
  const kbId = knowledgeBase.value?.id
  if (!kbId) return

  const code = projectCode.value

  // 如果不强制刷新且有有效缓存，使用缓存
  if (!force && isCacheValid(code)) {
    const cachedDocs = cacheData.documents.get(code)
    const cachedTotal = cacheData.total.get(code)
    if (cachedDocs) {
      documents.value = cachedDocs
      total.value = cachedTotal || 0
      updateSelectState()
      return
    }
  }

  tableLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    // 添加搜索和筛选参数
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (typeFilter.value) params.type = typeFilter.value
    if (statusFilter.value) params.status = statusFilter.value

    const res = await listKnowledge(kbId, params)
    documents.value = (res.data || []).map(doc => ({ ...doc, _selected: false }))
    total.value = res.total || 0

    // 更新缓存
    cacheData.documents.set(code, documents.value)
    cacheData.total.set(code, total.value)
    cacheData.cacheTime.set(code, Date.now())

    updateSelectState()
  } catch (e) {
    ElMessage.error(e.message || '获取文档列表失败')
  } finally {
    tableLoading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await fetchKnowledgeBase(true)
    ElMessage.success('刷新成功')
  } finally {
    refreshing.value = false
  }
}

// 更新选择状态
const updateSelectState = () => {
  const selected = documents.value.filter(d => d._selected)
  selectedDocs.value = selected
  selectAll.value = selected.length === documents.value.length && documents.value.length > 0
  isIndeterminate.value = selected.length > 0 && selected.length < documents.value.length
}

const handleSelectAll = (val) => {
  documents.value.forEach(doc => doc._selected = val)
  updateSelectState()
}

const handleSelectChange = () => {
  updateSelectState()
}

// 使用自定义上传方法
const handleFileUpload = async (options) => {
  const { file } = options
  if (!knowledgeBase.value?.id) {
    ElMessage.error('请先关联知识库')
    return false
  }

  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadFileName.value = file.name

  try {
    await uploadFileKnowledge(knowledgeBase.value.id, file)
    ElMessage.success('上传成功')
    await fetchDocuments(true)
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
  return false
}

const showCreateDialog = () => {
  createForm.value = { name: '', description: '' }
  createDialogVisible.value = true
}

const handleCreate = async () => {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  createLoading.value = true
  try {
    // 传递用户输入的名称和描述
    await createProjectKnowledgeBase(projectCode.value, {
      name: createForm.value.name,
      description: createForm.value.description
    })
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    await fetchKnowledgeBase(true)
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    createLoading.value = false
  }
}

const showLinkDialog = async () => {
  linkDialogVisible.value = true
  kbListLoading.value = true
  selectedKb.value = null
  try {
    const res = await listKnowledgeBases()
    kbList.value = res.data || []
  } catch {
    ElMessage.error('获取知识库列表失败')
  } finally {
    kbListLoading.value = false
  }
}

const handleLink = async () => {
  if (!selectedKb.value) return
  linkLoading.value = true
  try {
    await linkKnowledgeBase(projectCode.value, {
      knowledgeBaseId: selectedKb.value.id,
      knowledgeBaseName: selectedKb.value.name
    })
    ElMessage.success('关联成功')
    linkDialogVisible.value = false
    await fetchKnowledgeBase(true)
  } catch (e) {
    ElMessage.error(e.message || '关联失败')
  } finally {
    linkLoading.value = false
  }
}

const handleUnlink = async () => {
  try {
    await ElMessageBox.confirm('确定解除关联？知识库数据不会被删除。', '提示', { type: 'warning' })
    await unlinkKnowledgeBase(projectCode.value)
    ElMessage.success('已解除关联')
    // 清除缓存
    const code = projectCode.value
    cacheData.knowledgeBase.delete(code)
    cacheData.documents.delete(code)
    cacheData.total.delete(code)
    cacheData.cacheTime.delete(code)
    knowledgeBase.value = null
    documents.value = []
    total.value = 0
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '解除关联失败')
    }
  }
}

const showAddUrlDialog = () => {
  urlForm.value = { url: '' }
  addUrlDialogVisible.value = true
}

const handleAddUrl = async () => {
  const valid = await urlFormRef.value?.validate().catch(() => false)
  if (!valid) return

  addUrlLoading.value = true
  try {
    await createUrlKnowledge(knowledgeBase.value.id, urlForm.value.url)
    ElMessage.success('添加成功')
    addUrlDialogVisible.value = false
    await fetchDocuments(true)
  } catch (e) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    addUrlLoading.value = false
  }
}

const showAddManualDialog = () => {
  manualForm.value = { title: '', content: '' }
  addManualDialogVisible.value = true
}

const handleAddManual = async () => {
  const valid = await manualFormRef.value?.validate().catch(() => false)
  if (!valid) return

  addManualLoading.value = true
  try {
    await createManualKnowledge(knowledgeBase.value.id, manualForm.value)
    ElMessage.success('创建成功')
    addManualDialogVisible.value = false
    await fetchDocuments(true)
  } catch (e) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    addManualLoading.value = false
  }
}

// 防抖搜索
const debounceSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    fetchDocuments(true)
  }, 300)
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchDocuments(true)
}

const handlePageChange = () => {
  fetchDocuments(true)
}

// 获取文件类型
const getFileType = (doc) => {
  // 从文件名获取扩展名
  const fileName = doc.file_name || doc.title || ''
  const ext = fileName.split('.').pop()?.toLowerCase()

  // 常见文件类型映射
  const typeMap = {
    'pdf': 'pdf',
    'doc': 'doc',
    'docx': 'docx',
    'xls': 'xls',
    'xlsx': 'xlsx',
    'txt': 'txt',
    'md': 'md',
    'json': 'json',
    'xml': 'xml',
    'html': 'html',
    'css': 'css',
    'js': 'js',
    'ts': 'ts',
    'py': 'py',
    'java': 'java',
    'go': 'go',
    'sql': 'sql',
    'yaml': 'yaml',
    'yml': 'yml'
  }

  return typeMap[ext] || ext || ''
}

// 预览文档
const handlePreview = async (doc) => {
  previewDoc.value = doc
  previewDialogVisible.value = true
  previewLoading.value = true
  previewBlobUrl.value = ''
  previewTextContent.value = ''

  // 获取文件类型
  const fileType = getFileType(doc)
  previewFileType.value = fileType

  try {
    const res = await previewKnowledge(doc.id)
    const blob = res.data || res
    const contentType = res.headers?.['content-type'] || 'application/octet-stream'

    // 检查是否是文本类型响应
    const isTextResponse = contentType.includes('text/plain') || contentType.includes('text/markdown')

    if (isTextResponse) {
      // 文本响应，直接读取为文本显示
      const reader = new FileReader()
      reader.onload = (e) => {
        previewTextContent.value = e.target?.result || ''
        previewFileType.value = 'txt' // 强制使用文本预览
        previewLoading.value = false
      }
      reader.onerror = () => {
        ElMessage.error('读取文件内容失败')
        previewLoading.value = false
      }
      reader.readAsText(blob)
    } else if (fileType === 'pdf') {
      // PDF 文件创建 Blob URL
      previewBlobUrl.value = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }))
      previewLoading.value = false
    } else if (fileType === 'docx' || fileType === 'doc') {
      // Word 文件
      previewBlobUrl.value = URL.createObjectURL(new Blob([blob], { type: contentType }))
      previewLoading.value = false
    } else if (fileType === 'xlsx' || fileType === 'xls') {
      // Excel 文件
      previewBlobUrl.value = URL.createObjectURL(new Blob([blob], { type: contentType }))
      previewLoading.value = false
    } else {
      // 其他文件类型，尝试作为文本读取
      const reader = new FileReader()
      reader.onload = (e) => {
        previewTextContent.value = e.target?.result || ''
        previewFileType.value = 'txt'
        previewLoading.value = false
      }
      reader.onerror = () => {
        // 无法作为文本读取，显示不支持预览
        previewFileType.value = 'unsupported'
        previewLoading.value = false
      }
      reader.readAsText(blob)
    }
  } catch {
    ElMessage.error('获取预览内容失败')
    previewLoading.value = false
  }
}

// 下载预览文件
const handleDownloadPreview = async () => {
  if (!previewDoc.value) return

  try {
    const res = await downloadKnowledge(previewDoc.value.id)
    const blob = res.data || res
    const url = URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = previewDoc.value.file_name || previewDoc.value.title || 'download'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

// 关闭预览对话框时释放 Blob URL
watch(previewDialogVisible, (visible) => {
  if (!visible && previewBlobUrl.value) {
    URL.revokeObjectURL(previewBlobUrl.value)
    previewBlobUrl.value = ''
    previewTextContent.value = ''
    previewFileType.value = ''
  }
})

const handleReparse = async (doc) => {
  try {
    await reparseKnowledge(doc.id)
    ElMessage.success('已提交重新解析')
    await fetchDocuments(true)
  } catch (e) {
    ElMessage.error(e.message || '重新解析失败')
  }
}

const handleDelete = async (doc) => {
  try {
    await ElMessageBox.confirm(`确定删除文档「${doc.title || doc.file_name || '未命名'}」？`, '提示', { type: 'warning' })
    await deleteKnowledge(doc.id)
    ElMessage.success('删除成功')
    await fetchDocuments(true)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedDocs.value.length === 0) return

  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedDocs.value.length} 个文档？`, '批量删除', { type: 'warning' })

    const ids = selectedDocs.value.map(d => d.id)
    for (const id of ids) {
      await deleteKnowledge(id)
    }

    ElMessage.success(`成功删除 ${ids.length} 个文档`)
    await fetchDocuments(true)
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const formatDate = (d) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const getTypeLabel = (t) => ({ file: '文件', url: '链接', manual: '文档' }[t] || t)

const getStatusLabel = (s) => ({ pending: '待处理', processing: '处理中', completed: '完成', failed: '失败' }[s] || s)

// 生命周期
onMounted(() => {
  const code = projectCode.value
  if (code && cacheData.lastProjectCode !== code) {
    fetchKnowledgeBase()
  } else if (code && isCacheValid(code)) {
    // 使用缓存
    const cachedKb = cacheData.knowledgeBase.get(code)
    const cachedDocs = cacheData.documents.get(code)
    const cachedTotal = cacheData.total.get(code)
    if (cachedKb !== undefined) {
      knowledgeBase.value = cachedKb
      documents.value = cachedDocs || []
      total.value = cachedTotal || 0
      updateSelectState()
    }
  }
})

watch(projectCode, (newCode, oldCode) => {
  if (newCode && newCode !== oldCode) {
    if (cacheData.lastProjectCode === newCode && isCacheValid(newCode)) {
      // 使用缓存
      const cachedKb = cacheData.knowledgeBase.get(newCode)
      const cachedDocs = cacheData.documents.get(newCode)
      const cachedTotal = cacheData.total.get(newCode)
      if (cachedKb !== undefined) {
        knowledgeBase.value = cachedKb
        documents.value = cachedDocs || []
        total.value = cachedTotal || 0
        updateSelectState()
      }
    } else {
      fetchKnowledgeBase()
    }
  }
})

onActivated(() => {
  const code = projectCode.value
  if (code && cacheData.lastProjectCode === code && isCacheValid(code)) {
    const cachedKb = cacheData.knowledgeBase.get(code)
    const cachedDocs = cacheData.documents.get(code)
    const cachedTotal = cacheData.total.get(code)
    if (cachedKb !== undefined) {
      knowledgeBase.value = cachedKb
      documents.value = cachedDocs || []
      total.value = cachedTotal || 0
      updateSelectState()
    }
  } else if (code) {
    fetchKnowledgeBase()
  }
})

onDeactivated(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped>
.knowledge-wrapper {
  height: 100%;
  background: #fff;
  display: flex;
  flex-direction: column;
}

/* 加载状态 */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--color-text-tertiary);
}

/* 未关联状态 */
.unlinked-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.unlinked-icon {
  width: 80px;
  height: 80px;
  background: var(--color-bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--color-text-tertiary);
}

.unlinked-state h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.unlinked-state p {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin: 0 0 24px;
}

.unlinked-actions {
  display: flex;
  gap: 12px;
}

/* 已关联状态 */
.linked-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

/* 顶部信息条 */
.kb-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.kb-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
}

.kb-name {
  font-weight: 500;
}

.kb-meta {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.kb-header-actions {
  display: flex;
  gap: 8px;
}

/* 工具栏 */
.kb-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border-primary);
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

/* 上传进度条 */
.upload-progress-bar {
  padding: 8px 20px;
  background: var(--color-primary-light);
  border-bottom: 1px solid var(--color-primary-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-progress-bar .el-progress {
  flex: 1;
  max-width: 200px;
}

.upload-text {
  font-size: 12px;
  color: var(--color-primary);
}

/* 表格 */
.kb-table-wrapper {
  flex: 1;
  overflow: auto;
}

.kb-table {
  width: 100%;
  border-collapse: collapse;
}

.kb-table th {
  padding: 10px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-primary);
}

.kb-table td {
  padding: 12px 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-bg-secondary);
}

.kb-table tr:hover td {
  background: var(--color-bg-secondary);
}

.empty-row {
  text-align: center;
  padding: 40px;
  color: var(--color-text-tertiary);
}

.empty-row p {
  margin: 8px 0 4px;
  font-size: 14px;
}

.empty-row span {
  font-size: 12px;
}

.doc-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  border-radius: 2px;
}

.doc-icon.file { background: var(--color-primary); }
.doc-icon.url { background: var(--color-success); }
.doc-icon.manual { background: var(--color-warning); }

.doc-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.type-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 2px;
}

.type-badge.file { background: var(--color-primary-light); color: var(--color-primary); }
.type-badge.url { background: var(--color-success-light); color: var(--color-success); }
.type-badge.manual { background: var(--color-warning-light); color: var(--color-warning); }

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 2px;
}

.status-badge.pending { background: var(--color-bg-tertiary); color: var(--color-text-tertiary); }
.status-badge.processing { background: var(--color-warning-light); color: var(--color-warning); }
.status-badge.completed { background: var(--color-success-light); color: var(--color-success); }
.status-badge.failed { background: var(--color-danger-light); color: var(--color-danger); }

.action-cell {
  display: flex;
  gap: 12px;
}

.action-link {
  color: var(--color-primary);
  cursor: pointer;
  font-size: 13px;
}

.action-link:hover {
  text-decoration: underline;
}

.action-link.danger {
  color: var(--color-danger);
}

/* 分页 */
.kb-pagination {
  padding: 12px 20px;
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--color-border-primary);
}

/* 选择列表 */
.kb-select-list {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--color-border-primary);
  border-radius: 2px;
}

.kb-select-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-bg-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.kb-select-item:last-child { border-bottom: none; }
.kb-select-item:hover { background: var(--color-bg-secondary); }
.kb-select-item.chosen { background: var(--color-primary-light); }

.kb-select-name {
  flex: 1;
  font-size: 13px;
}

.kb-select-count {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-right: 8px;
}

.kb-select-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-tertiary);
}

/* 对话框提示 */
.dialog-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-top: 12px;
}

/* 预览对话框 */
.preview-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
  height: 60vh;
  overflow-x: auto;
  overflow-y: hidden;
}

.preview-dialog :deep(.el-dialog) {
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

@media (max-width: 768px) {
  .kb-toolbar {
    flex-direction: column;
    gap: 12px;
  }

  .toolbar-left, .toolbar-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .toolbar-right .el-input {
    width: 100%;
  }

  .kb-table th:nth-child(4),
  .kb-table td:nth-child(4) {
    display: none;
  }
}
</style>
