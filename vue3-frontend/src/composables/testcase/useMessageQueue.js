/**
 * 消息队列 Composable — 批量缓冲 + 异步渲染
 *
 * 用于流式输出场景，将高频消息写入缓冲到队列，
 * 通过 nextTick 批量渲染，避免高频 DOM 更新阻塞。
 */
import { nextTick } from 'vue'

export function useMessageQueue(messages, scrollToBottom) {
  const queue = []
  let processing = false

  const process = async () => {
    if (processing) return
    processing = true
    while (queue.length > 0) {
      const msg = queue.shift()
      messages.value.push(msg)
      await nextTick()
      scrollToBottom?.()
      await new Promise(resolve => setTimeout(resolve, 10))
    }
    processing = false
  }

  const add = (msg) => {
    queue.push(msg)
    process()
  }

  const update = (finder, updater) => {
    const index = messages.value.findIndex(finder)
    if (index !== -1) {
      const existing = messages.value[index]
      const val = typeof updater === 'function' ? updater(existing) : updater
      messages.value[index] = { ...existing, ...val }
    }
  }

  return { add, update }
}
