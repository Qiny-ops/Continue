/**
 * SSE 流式请求工具
 * 统一管理 token 获取、AbortController、buffer 解析、错误处理
 */
import { getToken } from '@/api/axios'

/**
 * 创建 SSE 流式请求
 * @param {Object} options
 * @param {string} options.url - 请求 URL
 * @param {Object} options.data - POST 请求体
 * @param {Object} options.callbacks - 事件回调
 * @param {Function} [options.callbacks.onEvent] - 通用事件回调 (eventName, data)
 * @param {Function} [options.callbacks.onError] - 错误回调
 * @param {Function} [options.callbacks.onComplete] - 流结束回调
 * @returns {{ abort: Function }} 控制器对象
 */
export function createSSEStream({ url, data, callbacks = {} }) {
  const { onEvent, onError, onComplete } = callbacks
  const token = getToken() || ''
  const controller = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data),
    signal: controller.signal
  }).then(response => {
    if (!response.ok) {
      // 尝试读取错误响应体
      return response.text().then(text => {
        let errorMsg = `HTTP error! status: ${response.status}`
        try {
          const errorData = JSON.parse(text)
          errorMsg = errorData.detail || errorData.error || errorData.message || errorMsg
        } catch { /* ignore parse failure */ }
        throw new Error(errorMsg)
      })
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const processBuffer = () => {
      // 按双换行分割 SSE 事件块
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() || ''

      for (const block of blocks) {
        if (!block.trim()) continue

        // 跳过 SSE 注释行
        const lines = block.split('\n').filter(line => !line.startsWith(':'))

        let eventName = 'unknown'
        let dataStr = ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventName = line.substring(6).trim()
          } else if (line.startsWith('data:')) {
            dataStr = line.substring(5).trim()
          }
        }

        if (dataStr) {
          try {
            const parsed = JSON.parse(dataStr)
            onEvent?.(eventName, parsed)
          } catch {
            // 忽略不完整数据块
          }
        }
      }
    }

    const readChunk = () => {
      reader.read().then(({ done, value }) => {
        if (done) {
          if (buffer.trim()) processBuffer()
          onComplete?.()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        processBuffer()
        readChunk()
      }).catch(err => {
        if (err.name === 'AbortError') return
        onError?.({ error: err.message || '读取流失败' })
      })
    }

    readChunk()
  }).catch(err => {
    if (err.name === 'AbortError') return
    onError?.({ error: err.message || '请求失败' })
  })

  return {
    abort() { controller.abort() }
  }
}
