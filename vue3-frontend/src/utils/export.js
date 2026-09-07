/**
 * 导出工具函数
 * 支持导出测试用例为 Excel 和 CSV 格式
 * xlsx 使用动态导入，避免 4.7MB 首屏加载
 */

/**
 * 导出测试用例为 Excel 文件
 */
export async function exportToExcel(testCases, filename = '测试用例') {
  if (!testCases || testCases.length === 0) {
    throw new Error('没有可导出的测试用例')
  }

  const XLSX = await import('xlsx')

  const data = testCases.map((tc, index) => ({
    '序号': index + 1,
    '用例ID': tc.id || '',
    '用例标题': tc.title || '',
    '所属模块': tc.module_name || tc.module?.name || '',
    '优先级': tc.priority?.toUpperCase() || 'P2',
    '前置条件': tc.precondition || '',
    '测试步骤': tc.steps || '',
    '预期结果': tc.expected_result || '',
    '关联需求': tc.requirement_title || tc.requirement || '',
    '自动化状态': getAutomationStatusText(tc.automation_status),
    '审核状态': getReviewStatusText(tc.review_status),
    '创建人': tc.created_by_name || tc.created_by?.username || '',
    '创建时间': formatDate(tc.created_at),
    '更新时间': formatDate(tc.updated_at)
  }))

  const worksheet = XLSX.utils.json_to_sheet(data)

  worksheet['!cols'] = [
    { wch: 6 }, { wch: 10 }, { wch: 40 }, { wch: 20 }, { wch: 8 },
    { wch: 30 }, { wch: 50 }, { wch: 30 }, { wch: 20 }, { wch: 12 },
    { wch: 10 }, { wch: 10 }, { wch: 18 }, { wch: 18 }
  ]

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '测试用例')
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

/**
 * 导出测试用例为 CSV 文件
 */
export function exportToCSV(testCases, filename = '测试用例') {
  if (!testCases || testCases.length === 0) {
    throw new Error('没有可导出的测试用例')
  }

  const headers = [
    '序号', '用例ID', '用例标题', '所属模块', '优先级',
    '前置条件', '测试步骤', '预期结果', '关联需求',
    '自动化状态', '审核状态', '创建人', '创建时间', '更新时间'
  ]

  const rows = testCases.map((tc, index) => [
    index + 1,
    tc.id || '',
    escapeCSVField(tc.title || ''),
    escapeCSVField(tc.module_name || tc.module?.name || ''),
    tc.priority?.toUpperCase() || 'P2',
    escapeCSVField(tc.precondition || ''),
    escapeCSVField(tc.steps || ''),
    escapeCSVField(tc.expected_result || ''),
    escapeCSVField(tc.requirement_title || tc.requirement || ''),
    getAutomationStatusText(tc.automation_status),
    getReviewStatusText(tc.review_status),
    tc.created_by_name || tc.created_by?.username || '',
    formatDate(tc.created_at),
    formatDate(tc.updated_at)
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')

  const BOM = '﻿'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8' })

  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${filename}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

function getAutomationStatusText(status) {
  const map = { 'not_analyzed': '未分析', 'not_automated': '未自动化', 'automated': '已自动化' }
  return map[status] || '未分析'
}

function getReviewStatusText(status) {
  const map = { 'pending': '待审核', 'approved': '已通过', 'rejected': '已驳回' }
  return map[status] || '待审核'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  }).replace(/\//g, '-')
}

function escapeCSVField(field) {
  if (field === null || field === undefined) return ''
  const str = String(field)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export default { exportToExcel, exportToCSV }
