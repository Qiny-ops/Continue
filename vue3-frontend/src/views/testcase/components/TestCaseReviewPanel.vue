<template>
  <div class="review-panel">
    <!-- 顶部筛选 -->
    <div class="review-header">
      <el-select v-model="filterStatus" placeholder="评审状态" @change="fetchReviews">
        <el-option label="待评审" value="pending" />
        <el-option label="修改后待重审" value="revision_pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
      </el-select>
    </div>

    <!-- 内容区域 -->
    <div class="review-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
      </div>

      <!-- 空状态 -->
      <div v-else-if="cases.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="40" r="36" stroke="currentColor" stroke-width="2" stroke-dasharray="4 3" />
            <path d="M28 32h24M28 40h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            <circle cx="48" cy="48" r="8" fill="currentColor" opacity="0.2" />
            <path d="M45 48l3 3 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h3>暂无{{ getStatusFilterText() }}用例</h3>
        <p>{{ filterStatus === 'pending' ? '新建的用例会自动进入评审流程' : '切换筛选条件查看其他用例' }}</p>
      </div>

      <!-- 用例列表 -->
      <div v-else class="case-list">
        <div v-for="item in cases" :key="item.id" class="case-item" @click="handleView(item)">
          <div class="case-main">
            <div class="case-status" :class="item.review_status">
              <el-icon v-if="item.review_status === 'pending' || item.review_status === 'revision_pending'"><Clock /></el-icon>
              <el-icon v-else-if="item.review_status === 'approved'"><CircleCheck /></el-icon>
              <el-icon v-else><CircleClose /></el-icon>
            </div>
            <div class="case-info">
              <div class="case-title">
                {{ item.title }}
                <el-tag v-if="getRevisionNumber(item) > 1" size="small" type="info" class="revision-tag">
                  第{{ getRevisionNumber(item) }}轮
                </el-tag>
              </div>
              <div class="case-meta">
                <span class="priority" :class="item.priority">{{ getPriorityText(item.priority) }}</span>
                <span>{{ item.module_name || '未分类' }}</span>
                <span>{{ item.created_by_name }}</span>
              </div>
            </div>
          </div>
          <el-tag :type="getTagType(item.review_status)" size="small">
            {{ getStatusText(item.review_status) }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-bar">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchReviews"
      />
    </div>

    <!-- 用例详情对话框 -->
    <el-dialog v-model="detailVisible" title="用例评审" width="720px" top="5vh">
      <div v-if="currentCase" class="case-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="detail-header">
            <h3>{{ currentCase.title }}</h3>
            <el-tag :type="getTagType(currentCase.review_status)" size="small">
              {{ getStatusText(currentCase.review_status) }}
            </el-tag>
          </div>
          <div class="detail-meta">
            <span><label>优先级：</label>{{ getPriorityText(currentCase.priority) }}</span>
            <span><label>模块：</label>{{ currentCase.module_name || '未分类' }}</span>
            <span><label>创建人：</label>{{ currentCase.created_by_name }}</span>
          </div>
        </div>

        <!-- 前置条件 -->
        <div v-if="currentCase.precondition" class="detail-section">
          <h4>前置条件</h4>
          <p>{{ currentCase.precondition }}</p>
        </div>

        <!-- 测试步骤 -->
        <div class="detail-section">
          <h4>测试步骤</h4>
          <p v-if="currentCase.steps" class="steps-text">{{ currentCase.steps }}</p>
          <p v-else class="no-data">暂无测试步骤</p>
        </div>

        <!-- 预期结果 -->
        <div class="detail-section">
          <h4>预期结果</h4>
          <p v-if="currentCase.expected_result" class="expected-text">{{ currentCase.expected_result }}</p>
          <p v-else class="no-data">暂无预期结果</p>
        </div>

        <!-- 评审历史 -->
        <div class="detail-section">
          <h4>评审历史</h4>
          <div v-if="reviewHistory.length" class="review-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="review in reviewHistory"
                :key="review.id"
                :type="getTimelineType(review.status)"
                :timestamp="formatDate(review.created_at)"
                placement="top"
              >
                <div class="timeline-content">
                  <div class="timeline-header">
                    <span class="review-round">第 {{ review.revision_number }} 轮</span>
                    <el-tag :type="getTagType(review.status)" size="small">
                      {{ getStatusText(review.status) }}
                    </el-tag>
                    <span v-if="review.reviewer_name" class="reviewer-name">
                      {{ review.reviewer_name }}
                    </span>
                  </div>
                  <div v-if="review.comment" class="review-comment">
                    {{ review.comment }}
                  </div>
                  <div v-if="review.revision_note" class="revision-note">
                    <el-icon><EditPen /></el-icon>
                    修改说明：{{ review.revision_note }}
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
          <div v-else class="no-data">暂无评审记录</div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <!-- 待评审状态 -->
          <template v-if="currentCase?.review_status === 'pending' || currentCase?.review_status === 'revision_pending'">
            <el-button @click="detailVisible = false">关闭</el-button>
            <el-button type="danger" @click="showRejectDialog">驳回</el-button>
            <el-button type="success" :loading="submitting" @click="handleApprove">通过</el-button>
          </template>
          <!-- 已驳回状态 - 创建者可修改并重新提交 -->
          <template v-else-if="currentCase?.review_status === 'rejected'">
            <el-button @click="detailVisible = false">关闭</el-button>
            <el-button type="primary" @click="handleEditAndResubmit">修改并重新提交</el-button>
          </template>
          <!-- 已通过状态 -->
          <template v-else>
            <el-button @click="detailVisible = false">关闭</el-button>
          </template>
        </div>
      </template>
    </el-dialog>

    <!-- 驳回原因对话框 -->
    <el-dialog v-model="rejectDialogVisible" title="驳回原因" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入驳回原因" />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="confirmReject">确定驳回</el-button>
      </template>
    </el-dialog>

    <!-- 修改并重新提交对话框 -->
    <el-dialog v-model="resubmitDialogVisible" title="修改并重新提交评审" width="500px">
      <div class="resubmit-form">
        <div class="form-item">
          <label>修改说明</label>
          <el-input
            v-model="resubmitNote"
            type="textarea"
            :rows="3"
            placeholder="请描述您对用例做了哪些修改（可选）"
          />
        </div>
        <div class="form-tip">
          <el-icon><InfoFilled /></el-icon>
          提交后，用例将进入"修改后待重审"状态，等待评审人再次评审
        </div>
      </div>
      <template #footer>
        <el-button @click="resubmitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="confirmResubmit">确认提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, CircleCheck, CircleClose, EditPen, InfoFilled } from '@element-plus/icons-vue'
import { testCaseApi, reviewApi } from '@/api/modules/testcase'

const props = defineProps({
  projectId: { type: [String, Number], default: null }
})

const emit = defineEmits(['edit-case'])

const loading = ref(false)
const submitting = ref(false)
const cases = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('pending')
const detailVisible = ref(false)
const rejectDialogVisible = ref(false)
const resubmitDialogVisible = ref(false)
const rejectReason = ref('')
const resubmitNote = ref('')
const currentCase = ref(null)
const reviewHistory = ref([])

const PRIORITY_TEXT = { p0: 'P0', p1: 'P1', p2: 'P2', p3: 'P3' }
const getPriorityText = (p) => PRIORITY_TEXT[p] || 'P2'
const getTagType = (s) => ({ pending: 'warning', revision_pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info')
const getStatusText = (s) => ({ pending: '待评审', revision_pending: '待重审', approved: '已通过', rejected: '已驳回' }[s] || s)
const getTimelineType = (s) => ({ approved: 'success', rejected: 'danger', pending: 'warning' }[s] || 'info')

const getStatusFilterText = () => {
  const texts = {
    pending: '待评审',
    revision_pending: '待重审',
    approved: '已通过',
    rejected: '已驳回'
  }
  return texts[filterStatus.value] || ''
}

const getRevisionNumber = (item) => {
  // 从评审记录中获取最新轮次
  return item.latest_revision_number || 1
}

const formatDate = (str) => {
  if (!str) return ''
  const d = new Date(str)
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fetchReviews = async () => {
  if (!props.projectId) return
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      review_status: filterStatus.value
    }
    const res = await testCaseApi.getTestCasesByProject(props.projectId, params)
    cases.value = res?.results || []
    total.value = res?.count || 0
  } catch (e) {

  } finally {
    loading.value = false
  }
}

const handleView = async (item) => {
  currentCase.value = item
  detailVisible.value = true

  // 获取用例详情
  try {
    const res = await testCaseApi.getTestCase(item.id)
    currentCase.value = res || item
  } catch (e) {

  }

  // 获取评审历史
  try {
    const res = await reviewApi.getReviewHistory(item.id)
    reviewHistory.value = res || []
    // 更新轮次信息
    if (reviewHistory.value.length > 0) {
      currentCase.value.latest_revision_number = reviewHistory.value[reviewHistory.value.length - 1].revision_number
    }
  } catch {
    reviewHistory.value = []
  }
}

const handleApprove = async () => {
  submitting.value = true
  try {
    await reviewApi.approveReview(currentCase.value.id, '评审通过')
    ElMessage.success('评审通过')
    detailVisible.value = false
    fetchReviews()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const showRejectDialog = () => {
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  submitting.value = true
  try {
    await reviewApi.rejectReview(currentCase.value.id, rejectReason.value)
    ElMessage.success('已驳回')
    rejectDialogVisible.value = false
    detailVisible.value = false
    fetchReviews()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const handleEditAndResubmit = () => {
  resubmitNote.value = ''
  resubmitDialogVisible.value = true
}

const confirmResubmit = async () => {
  submitting.value = true
  try {
    await reviewApi.resubmitReview(currentCase.value.id, resubmitNote.value)
    ElMessage.success('已重新提交评审')
    resubmitDialogVisible.value = false
    detailVisible.value = false
    // 通知父组件打开编辑对话框
    emit('edit-case', currentCase.value)
    fetchReviews()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

watch(() => props.projectId, () => fetchReviews(), { immediate: true })
</script>

<style scoped>
.review-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.review-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.review-header .el-select { width: 160px; }

.review-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
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

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: var(--color-primary);
  opacity: 0.5;
  margin-bottom: 16px;
}

.empty-icon svg { width: 100%; height: 100%; }

.empty-state h3 {
  font-size: 16px;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.case-list { display: flex; flex-direction: column; gap: 12px; }

.case-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--color-border-secondary);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
}

.case-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-color: var(--color-primary);
}

.case-main { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }

.case-status {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.case-status.pending { background: #fef3cd; color: #856404; }
.case-status.revision_pending { background: #e0e7ff; color: #4f46e5; }
.case-status.approved { background: #d4edda; color: #155724; }
.case-status.rejected { background: #f8d7da; color: #721c24; }

.case-info { flex: 1; min-width: 0; }

.case-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
}

.revision-tag {
  flex-shrink: 0;
}

.case-meta {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.case-meta .priority {
  padding: 1px 6px;
  border-radius: 2px;
  font-weight: 500;
}

.case-meta .priority.p0 { background: #fde8e8; color: #e53e3e; }
.case-meta .priority.p1 { background: #fef3cd; color: #856404; }
.case-meta .priority.p2 { background: #e0e7ff; color: #4f46e5; }
.case-meta .priority.p3 { background: #f1f5f9; color: #64748b; }

.pagination-bar {
  padding: 12px 20px;
  border-top: 1px solid var(--color-border-secondary);
  text-align: right;
}

/* 用例详情样式 */
.case-detail { padding: 0 8px; max-height: 60vh; overflow-y: auto; }

.detail-section { margin-bottom: 20px; }

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-header h3 {
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}

.detail-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.detail-meta label { color: var(--color-text-tertiary); }

.detail-section h4 {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border-secondary);
}

.detail-section p {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

.steps-text {
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  background: var(--color-bg-secondary);
  padding: 8px 12px;
  border-radius: 2px;
}

.expected-text {
  font-size: 13px;
  color: var(--color-success);
  line-height: 1.6;
  white-space: pre-wrap;
  background: var(--color-bg-secondary);
  padding: 8px 12px;
  border-radius: 2px;
}

.no-data {
  font-size: 13px;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: 20px;
}

/* 评审历史时间线 */
.review-timeline {
  margin-top: 8px;
}

.timeline-content {
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.review-round {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
  padding: 2px 6px;
  border-radius: 2px;
}

.reviewer-name {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-left: auto;
}

.review-comment {
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.5;
}

.revision-note {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border-secondary);
  font-size: 13px;
  color: var(--color-primary);
}

.revision-note .el-icon {
  margin-top: 2px;
}

/* 重新提交表单 */
.resubmit-form {
  padding: 0 4px;
}

.resubmit-form .form-item {
  margin-bottom: 12px;
}

.resubmit-form label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
