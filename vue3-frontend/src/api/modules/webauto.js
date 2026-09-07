import axios from '@/api/axios.js'
import { createSSEStream } from '@/utils/sse.js'

const BASE_URL = '/webauto'

/**
 * Web 自动化用例执行 API
 * 调用 Django 代理的 web-automation-service（端口 8003）流式端点。
 *
 * execute 请求体：case_id / environment_id(可选，取环境 base_url 作起始 URL) / start_url / action_list / site_hint / kb_id
 * plan    请求体：同 execute（不含 action_list，仅预览编排）
 */
const webAutoApi = {
  /**
   * 执行 Web 自动化用例（SSE 流式）
   * @param {Object} payload { case_id, start_url, action_list?, site_hint?, kb_id? }
   * @param {(event: Object) => void} onMessage 事件回调（event.type / event.data）
   * @param {(err: Error) => void} onError
   * @param {() => void} onComplete
   * @returns {{ abort: Function }}
   */
  executeCaseStream(payload, onMessage, onError, onComplete) {
    const url = `${axios.defaults.baseURL}${BASE_URL}/execute/`
    return createSSEStream({
      url,
      data: payload,
      callbacks: {
        onEvent: (_eventName, parsed) => onMessage?.(parsed),
        onError: (err) => onError?.(new Error(err.error || '执行失败')),
        onComplete: () => onComplete?.()
      }
    })
  },

  /**
   * 规划 action_list（SSE 流式，预览/编辑用，不实际执行）
   */
  planCaseStream(payload, onMessage, onError, onComplete) {
    const url = `${axios.defaults.baseURL}${BASE_URL}/plan/`
    return createSSEStream({
      url,
      data: payload,
      callbacks: {
        onEvent: (_eventName, parsed) => onMessage?.(parsed),
        onError: (err) => onError?.(new Error(err.error || '规划失败')),
        onComplete: () => onComplete?.()
      }
    })
  },

  /**
   * 获取 Web 自动化执行记录
   * @param {Object} params { test_case?, result? }
   */
  async getRuns(params = {}) {
    const response = await axios.get(`${BASE_URL}/runs/`, { params })
    return response
  }
}

export default webAutoApi
