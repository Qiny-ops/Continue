import {
  PRIORITY_OPTIONS,
  AUTOMATION_STATUS_OPTIONS,
  REVIEW_STATUS_OPTIONS,
  EXECUTION_RESULT_OPTIONS,
  TEST_CASE_TYPES
} from '@/constants/testcase'

/**
 * 测试用例格式化工具组合式函数
 * 提供统一的格式化方法
 */
export function useTestCaseFormatters() {
  // 优先级
  const getPriorityLabel = (value) => {
    const option = PRIORITY_OPTIONS.find(opt => opt.value === value)
    return option?.label || value?.toUpperCase() || 'P2'
  }

  const getPriorityType = (value) => {
    const option = PRIORITY_OPTIONS.find(opt => opt.value === value)
    return option?.type || 'info'
  }

  const getPriorityColor = (value) => {
    const option = PRIORITY_OPTIONS.find(opt => opt.value === value)
    return option?.color || '#909399'
  }

  // 自动化状态
  const getAutomationStatusLabel = (value) => {
    const option = AUTOMATION_STATUS_OPTIONS.find(opt => opt.value === value)
    return option?.label || '未分析'
  }

  const getAutomationStatusType = (value) => {
    const option = AUTOMATION_STATUS_OPTIONS.find(opt => opt.value === value)
    return option?.type || 'info'
  }

  // 评审状态
  const getReviewStatusLabel = (value) => {
    const option = REVIEW_STATUS_OPTIONS.find(opt => opt.value === value)
    return option?.label || '待评审'
  }

  const getReviewStatusType = (value) => {
    const option = REVIEW_STATUS_OPTIONS.find(opt => opt.value === value)
    return option?.type || 'info'
  }

  // 执行结果
  const getExecutionResultLabel = (value) => {
    const option = EXECUTION_RESULT_OPTIONS.find(opt => opt.value === value)
    return option?.label || value
  }

  const getExecutionResultType = (value) => {
    const option = EXECUTION_RESULT_OPTIONS.find(opt => opt.value === value)
    return option?.type || 'info'
  }

  const getExecutionResultIcon = (value) => {
    const option = EXECUTION_RESULT_OPTIONS.find(opt => opt.value === value)
    return option?.icon || 'CircleCheck'
  }

  // 测试用例类型
  const getTestCaseTypeLabel = (value) => {
    const option = TEST_CASE_TYPES.find(opt => opt.value === value)
    return option?.label || '功能测试'
  }

  const getTestCaseTypeIcon = (value) => {
    const option = TEST_CASE_TYPES.find(opt => opt.value === value)
    return option?.icon || 'SetUp'
  }

  // 日期格式化
  const formatDate = (dateStr, format = 'datetime') => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'

    const options = {
      date: { year: 'numeric', month: '2-digit', day: '2-digit' },
      datetime: { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' },
      time: { hour: '2-digit', minute: '2-digit' }
    }

    return date.toLocaleString('zh-CN', options[format] || options.datetime).replace(/\//g, '-')
  }

  // 相对时间
  const getRelativeTime = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 30) return `${days}天前`
    return formatDate(dateStr, 'date')
  }

  // 工时格式化
  const formatHours = (hours) => {
    if (hours === null || hours === undefined) return '-'
    return `${hours}h`
  }

  return {
    // 优先级
    getPriorityLabel,
    getPriorityType,
    getPriorityColor,
    // 自动化状态
    getAutomationStatusLabel,
    getAutomationStatusType,
    // 评审状态
    getReviewStatusLabel,
    getReviewStatusType,
    // 执行结果
    getExecutionResultLabel,
    getExecutionResultType,
    getExecutionResultIcon,
    // 用例类型
    getTestCaseTypeLabel,
    getTestCaseTypeIcon,
    // 通用格式化
    formatDate,
    getRelativeTime,
    formatHours
  }
}
