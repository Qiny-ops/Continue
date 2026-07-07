/**
 * 测试用例管理常量定义
 * 统一数据模型和枚举值
 */

// 测试用例优先级
export const PRIORITY_OPTIONS = [
  { value: 'p0', label: 'P0', color: '#f56c6c', type: 'danger' },
  { value: 'p1', label: 'P1', color: '#e6a23c', type: 'warning' },
  { value: 'p2', label: 'P2', color: '#409eff', type: 'info' },
  { value: 'p3', label: 'P3', color: '#909399', type: '' }
]

// 自动化状态
export const AUTOMATION_STATUS_OPTIONS = [
  { value: 'not_analyzed', label: '未分析', type: 'info' },
  { value: 'not_automated', label: '未自动化', type: 'warning' },
  { value: 'automated', label: '已自动化', type: 'success' }
]

// 评审状态
export const REVIEW_STATUS_OPTIONS = [
  { value: 'pending', label: '待评审', type: 'warning', color: '#856404' },
  { value: 'revision_pending', label: '修改后待重审', type: 'primary', color: '#7c3aed' },
  { value: 'approved', label: '已通过', type: 'success', color: '#155724' },
  { value: 'rejected', label: '已驳回', type: 'danger', color: '#721c24' }
]

// 执行结果
export const EXECUTION_RESULT_OPTIONS = [
  { value: 'pass', label: '通过', type: 'success', icon: 'CircleCheck' },
  { value: 'fail', label: '失败', type: 'danger', icon: 'CircleClose' },
  { value: 'block', label: '阻塞', type: 'warning', icon: 'Warning' },
  { value: 'skip', label: '跳过', type: 'info', icon: 'Remove' }
]

// 测试用例类型
export const TEST_CASE_TYPES = [
  { value: 'functional', label: '功能测试', icon: 'SetUp' },
  { value: 'api', label: '接口测试', icon: 'Connection' },
  { value: 'performance', label: '性能测试', icon: 'TrendCharts' },
  { value: 'ui', label: 'UI测试', icon: 'Picture' },
  { value: 'compatibility', label: '兼容性测试', icon: 'Monitor' },
  { value: 'security', label: '安全测试', icon: 'Lock' }
]

// 版本状态
export const VERSION_STATUS_OPTIONS = [
  { value: 'active', label: '活跃', type: 'success' },
  { value: 'archived', label: '已归档', type: 'info' }
]

// 默认表单数据
export const DEFAULT_TEST_CASE_FORM = {
  id: null,
  title: '',
  module: null,
  version: null,
  priority: 'p2',
  type: 'functional',
  automation_status: 'not_analyzed',
  automation_case_id: '',
  estimated_hours: null,
  tags: [],
  requirement: '',
  precondition: '',
  steps: '',
  expected_result: '',
  remark: ''
}

// 默认筛选条件
export const DEFAULT_FILTERS = {
  searchQuery: '',
  priority: '',
  automation_status: '',
  type: '',
  created_by: ''
}

// 帮助函数
export const getPriorityOption = (value) => 
  PRIORITY_OPTIONS.find(opt => opt.value === value) || PRIORITY_OPTIONS[2]

export const getAutomationStatusOption = (value) => 
  AUTOMATION_STATUS_OPTIONS.find(opt => opt.value === value) || AUTOMATION_STATUS_OPTIONS[0]

export const getReviewStatusOption = (value) => 
  REVIEW_STATUS_OPTIONS.find(opt => opt.value === value) || REVIEW_STATUS_OPTIONS[0]

export const getExecutionResultOption = (value) => 
  EXECUTION_RESULT_OPTIONS.find(opt => opt.value === value) || EXECUTION_RESULT_OPTIONS[0]

export const getTestCaseTypeOption = (value) => 
  TEST_CASE_TYPES.find(opt => opt.value === value) || TEST_CASE_TYPES[0]
