/**
 * 批量操作 Composable
 *
 * 封装批量模式切换、选中管理与批量执行/移动/复制/删除逻辑，
 * 从 ProjectTestCases.vue 中提取以缩减上帝组件体量。
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export function useBatchOperation(refreshTestCases, testCases, options = {}) {
  const batchMode = ref(false)
  const selectedCases = ref([])

  /** 处理表格选中变化 */
  const handleSelectionChange = (selection) => {
    selectedCases.value = selection
  }

  /** 校验是否已选中 */
  const _hasSelection = (action) => {
    if (selectedCases.value.length === 0) {
      ElMessage.warning(`请先选择要${action}的用例`)
      return false
    }
    return true
  }

  const handleBatchExecute = () => {
    if (!_hasSelection('执行')) return false
    if (options.onExecute) {
      // 自定义批量执行（如调用 Web 自动化微服务），传入选中用例副本
      options.onExecute(selectedCases.value.map(c => ({ ...c })))
    } else {
      ElMessage.success(`批量执行 ${selectedCases.value.length} 个用例`)
    }
    return true
  }

  const handleBatchMove = () => {
    if (!_hasSelection('移动')) return false
    ElMessage.info('批量移动功能开发中')
    return false
  }

  const handleBatchCopy = async () => {
    if (!_hasSelection('复制')) return false
    try {
      const ids = selectedCases.value.map(c => c.id)
      const response = await testCases.batchCopy?.(ids)
      const copiedCount = response?.data?.copied_count || selectedCases.value.length
      ElMessage.success(`成功复制 ${copiedCount} 个用例`)
      await refreshTestCases()
      return true
    } catch (err) {
      ElMessage.error(err.message || '批量复制失败')
      return false
    }
  }

  const handleBatchDelete = async () => {
    if (!_hasSelection('删除')) return false
    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedCases.value.length} 个用例吗？`,
        '警告', { type: 'warning' }
      )
      const ids = selectedCases.value.map(c => c.id)
      const response = await testCases.batchDelete?.(ids)
      const deletedCount = response?.data?.deleted_count || selectedCases.value.length
      ElMessage.success(`成功删除 ${deletedCount} 个用例`)
      await refreshTestCases()
      return true
    } catch (err) {
      if (err !== 'cancel') {
        ElMessage.error(err.message || '批量删除失败')
      }
      return false
    }
  }

  const toggleBatchMode = () => {
    batchMode.value = !batchMode.value
    if (!batchMode.value) {
      selectedCases.value = []
    }
  }

  const handleBatchAction = async (action) => {
    if (!_hasSelection('执行')) return
    const handlers = { execute: handleBatchExecute, move: handleBatchMove, copy: handleBatchCopy, delete: handleBatchDelete }
    const success = await handlers[action]?.()
    if (success) {
      batchMode.value = false
      selectedCases.value = []
    }
  }

  return {
    batchMode,
    selectedCases,
    handleSelectionChange,
    handleBatchExecute,
    handleBatchMove,
    handleBatchCopy,
    handleBatchDelete,
    toggleBatchMode,
    handleBatchAction
  }
}
