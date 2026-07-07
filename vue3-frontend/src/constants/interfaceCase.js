export const CASE_STATUS = [
  { value: 1, label: '未执行', type: 'info' },
  { value: 2, label: '通过', type: 'success' },
  { value: 3, label: '失败', type: 'danger' },
  { value: 4, label: '跳过', type: 'warning' },
  { value: 5, label: '阻塞', type: 'warning' }
]

export const ASSERTION_TYPES = [
  { value: 'status_code', label: '状态码' },
  { value: 'response_time', label: '响应时间' },
  { value: 'json_path', label: 'JSON路径' },
  { value: 'header', label: '响应头' },
  { value: 'body_contains', label: '响应体包含' },
  { value: 'json_schema', label: 'JSON Schema' }
]

export const COMPARISON_OPERATORS = [
  { value: 'eq', label: '等于' },
  { value: 'ne', label: '不等于' },
  { value: 'gt', label: '大于' },
  { value: 'gte', label: '大于等于' },
  { value: 'lt', label: '小于' },
  { value: 'lte', label: '小于等于' },
  { value: 'contains', label: '包含' },
  { value: 'not_contains', label: '不包含' },
  { value: 'regex', label: '正则匹配' },
  { value: 'exists', label: '存在' },
  { value: 'not_exists', label: '不存在' }
]

export const CASE_PRIORITY = [
  { value: 'p0', label: 'P0', desc: '核心功能', class: 'critical' },
  { value: 'p1', label: 'P1', desc: '重要功能', class: 'high' },
  { value: 'p2', label: 'P2', desc: '一般功能', class: 'medium' },
  { value: 'p3', label: 'P3', desc: '次要功能', class: 'low' }
]

export const getCaseStatusLabel = (status) => {
  const statusObj = CASE_STATUS.find(s => s.value === status)
  return statusObj?.label || '未知'
}

export const getCaseStatusType = (status) => {
  const statusObj = CASE_STATUS.find(s => s.value === status)
  return statusObj?.type || 'info'
}

export const getPriorityLabel = (priority) => {
  const priorityObj = CASE_PRIORITY.find(p => p.value === priority)
  return priorityObj?.label || 'P2'
}

export const getPriorityClass = (priority) => {
  const priorityObj = CASE_PRIORITY.find(p => p.value === priority)
  return priorityObj?.class || 'medium'
}
