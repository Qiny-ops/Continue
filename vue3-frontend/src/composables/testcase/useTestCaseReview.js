/**
 * 测试用例评审流程 Composable
 *
 * 封装评审对话框的全部状态与方法（查看/通过/驳回/编辑重审），
 * 从 ProjectTestCases.vue 中提取以缩减上帝组件体量。
 */
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { testCaseApi, reviewApi } from '@/api/modules/testcase'

export function useTestCaseReview(refreshTestCases) {
  // ---- 对话框状态 ----
  const reviewVisible = ref(false)
  const rejectVisible = ref(false)
  const reviewSubmitting = ref(false)
  const reviewCase = ref(null)
  const rejectReason = ref('')
  const reviewComments = ref([])

  // ---- 编辑模式 ----
  const reviewEditMode = ref(false)
  const reviewEditForm = reactive({
    title: '',
    module: null,
    priority: 'p2',
    precondition: '',
    steps: '',
    expected_result: '',
    requirement: '',
    revision_note: ''
  })

  // ---- 工具函数 ----
  const formatReviewDate = (dateStr) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleString('zh-CN')
    } catch {
      return dateStr
    }
  }

  // ---- 方法 ----

  /** 打开评审详情 */
  const handleReview = async (row) => {
    try {
      const res = await testCaseApi.getTestCase(row.id)
      reviewCase.value = res || row
      try {
        const reviewRes = await reviewApi.getReviewHistory(row.id)
        reviewComments.value = reviewRes || []
      } catch {
        reviewComments.value = []
      }
      reviewVisible.value = true
    } catch (err) {
      ElMessage.error(err.message || '获取用例详情失败')
    }
  }

  /** 评审通过 */
  const handleApprove = async () => {
    reviewSubmitting.value = true
    try {
      await reviewApi.approveReview(reviewCase.value.id, '评审通过')
      ElMessage.success('评审通过')
      reviewVisible.value = false
      await refreshTestCases()
    } catch (err) {
      ElMessage.error(err.message || '操作失败')
    } finally {
      reviewSubmitting.value = false
    }
  }

  /** 显示驳回对话框 */
  const showRejectDialog = () => {
    rejectReason.value = ''
    rejectVisible.value = true
  }

  /** 确认驳回 */
  const confirmReject = async () => {
    if (!rejectReason.value.trim()) {
      ElMessage.warning('请输入驳回原因')
      return
    }
    reviewSubmitting.value = true
    try {
      await reviewApi.rejectReview(reviewCase.value.id, rejectReason.value)
      ElMessage.success('已驳回')
      rejectVisible.value = false
      reviewVisible.value = false
      await refreshTestCases()
    } catch (err) {
      ElMessage.error(err.message || '操作失败')
    } finally {
      reviewSubmitting.value = false
    }
  }

  /** 进入评审对话框的编辑模式 */
  const enterReviewEditMode = () => {
    if (!reviewCase.value) return
    reviewEditMode.value = true
    const c = reviewCase.value
    reviewEditForm.title = c.title || ''
    reviewEditForm.module = c.module || null
    reviewEditForm.priority = c.priority || 'p2'
    reviewEditForm.precondition = c.precondition || ''
    reviewEditForm.steps = c.steps || ''
    reviewEditForm.expected_result = c.expected_result || ''
    reviewEditForm.requirement = c.requirement || ''
    reviewEditForm.revision_note = ''
  }

  /** 取消编辑模式 */
  const cancelReviewEdit = () => {
    reviewEditMode.value = false
  }

  /** 保存编辑并重新提交评审 */
  const saveAndResubmit = async () => {
    if (!reviewEditForm.title.trim()) {
      ElMessage.warning('请填写用例标题')
      return
    }
    if (!reviewEditForm.steps.trim()) {
      ElMessage.warning('请填写测试步骤')
      return
    }
    reviewSubmitting.value = true
    try {
      await testCaseApi.updateTestCase(reviewCase.value.id, {
        title: reviewEditForm.title,
        module: reviewEditForm.module,
        version: reviewCase.value.version,
        priority: reviewEditForm.priority,
        precondition: reviewEditForm.precondition,
        steps: reviewEditForm.steps,
        expected_result: reviewEditForm.expected_result,
        requirement: reviewEditForm.requirement
      })
      await reviewApi.resubmitReview(reviewCase.value.id, reviewEditForm.revision_note)
      ElMessage.success('已保存并重新提交评审')
      reviewVisible.value = false
      reviewEditMode.value = false
      await refreshTestCases()
    } catch (err) {
      ElMessage.error(err.message || '操作失败')
    } finally {
      reviewSubmitting.value = false
    }
  }

  /** 评审对话框关闭时重置编辑模式 */
  const handleReviewDialogClose = () => {
    reviewEditMode.value = false
  }

  return {
    // 状态
    reviewVisible,
    rejectVisible,
    reviewSubmitting,
    reviewCase,
    rejectReason,
    reviewComments,
    reviewEditMode,
    reviewEditForm,
    // 工具
    formatReviewDate,
    // 方法
    handleReview,
    handleApprove,
    showRejectDialog,
    confirmReject,
    enterReviewEditMode,
    cancelReviewEdit,
    saveAndResubmit,
    handleReviewDialogClose
  }
}
