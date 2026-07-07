export class ApiError extends Error {
  constructor(message, code = null, status = null, data = null, type = 'UNKNOWN') {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.data = data
    this.type = type
    this.timestamp = new Date().toISOString()
  }

  isNetworkError() {
    return this.type === 'NETWORK_ERROR' || this.status === null
  }

  isAuthError() {
    return this.type === 'AUTH_ERROR' || this.status === 401
  }

  isForbidden() {
    return this.type === 'FORBIDDEN' || this.status === 403
  }

  isNotFound() {
    return this.type === 'NOT_FOUND' || this.status === 404
  }

  isValidationError() {
    return this.type === 'VALIDATION_ERROR' || this.status === 400 || this.status === 422
  }

  isServerError() {
    return this.type === 'SERVER_ERROR' || this.status >= 500
  }

  isTimeout() {
    return this.type === 'TIMEOUT'
  }

  isRateLimited() {
    return this.type === 'RATE_LIMIT' || this.status === 429
  }
}

export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查您的网络设置',
  TIMEOUT: '请求超时，请稍后重试',
  NO_RESPONSE: '服务器无响应，请稍后再试',
  AUTH_ERROR: '身份验证失败，请重新登录',
  FORBIDDEN: '您没有权限执行此操作',
  NOT_FOUND: '请求的资源不存在',
  RATE_LIMIT: '请求过于频繁，请稍后再试',
  SERVER_ERROR: '服务器繁忙，请稍后再试',
  CLIENT_ERROR: '请求参数错误',
  VALIDATION_ERROR: '数据验证失败',
  UNKNOWN: '操作失败，请稍后重试'
}

export const HTTP_STATUS_MESSAGES = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有权限访问此资源',
  404: '请求的资源不存在',
  405: '请求方法不允许',
  408: '请求超时',
  409: '资源冲突',
  422: '数据验证失败',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  501: '服务器不支持该功能',
  502: '网关错误',
  503: '服务暂时不可用',
  504: '网关超时'
}

export function getDisplayMessage(error) {
  if (!error) {
    return ERROR_MESSAGES.UNKNOWN
  }

  if (error.displayMessage) {
    return error.displayMessage
  }

  if (error.type && ERROR_MESSAGES[error.type]) {
    return ERROR_MESSAGES[error.type]
  }

  if (error.status && HTTP_STATUS_MESSAGES[error.status]) {
    return HTTP_STATUS_MESSAGES[error.status]
  }

  if (error.message) {
    return error.message
  }

  return ERROR_MESSAGES.UNKNOWN
}

export function handleApiError(error, _showToast = true) {
  const normalizedError = normalizeError(error)
  const displayMessage = getDisplayMessage(normalizedError)

  return {
    ...normalizedError,
    displayMessage
  }
}

export function normalizeError(error) {
  if (error instanceof ApiError) {
    return error
  }

  if (error.type && error.message) {
    return new ApiError(
      error.message,
      error.code || null,
      error.status || null,
      error.data || null,
      error.type
    )
  }

  const { response, message, code } = error

  let errorMessage = message || ERROR_MESSAGES.UNKNOWN
  let errorType = 'UNKNOWN'
  let status = null
  let data = null

  if (response) {
    status = response.status
    data = response.data

    if (response.data?.message) {
      errorMessage = response.data.message
    } else if (HTTP_STATUS_MESSAGES[status]) {
      errorMessage = HTTP_STATUS_MESSAGES[status]
    }

    errorType = getErrorTypeFromStatus(status)
  } else if (message) {
    if (message.includes('timeout') || error.code === 'ECONNABORTED') {
      errorType = 'TIMEOUT'
      errorMessage = ERROR_MESSAGES.TIMEOUT
    } else if (message.includes('Network Error')) {
      errorType = 'NETWORK_ERROR'
      errorMessage = ERROR_MESSAGES.NETWORK_ERROR
    }
  }

  return new ApiError(
    errorMessage,
    code || response?.data?.code || null,
    status,
    data,
    errorType
  )
}

function getErrorTypeFromStatus(status) {
  const typeMap = {
    400: 'CLIENT_ERROR',
    401: 'AUTH_ERROR',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    408: 'TIMEOUT',
    422: 'VALIDATION_ERROR',
    429: 'RATE_LIMIT'
  }

  if (typeMap[status]) {
    return typeMap[status]
  }

  if (status >= 500) {
    return 'SERVER_ERROR'
  }

  if (status >= 400) {
    return 'CLIENT_ERROR'
  }

  return 'UNKNOWN'
}

export function isRetryableError(error) {
  const normalizedError = normalizeError(error)

  return (
    normalizedError.isNetworkError() ||
    normalizedError.isTimeout() ||
    normalizedError.isServerError() ||
    normalizedError.status === 429
  )
}

export function getRetryDelay(error) {
  const normalizedError = normalizeError(error)

  if (normalizedError.status === 429 && normalizedError.data?.retryAfter) {
    return normalizedError.data.retryAfter * 1000
  }

  if (normalizedError.isServerError()) {
    return 2000
  }

  if (normalizedError.isTimeout()) {
    return 1000
  }

  if (normalizedError.isNetworkError()) {
    return 3000
  }

  return 1000
}

export function createErrorFromResponse(response) {
  const { status, data } = response
  const type = getErrorTypeFromStatus(status)
  const message = data?.message || HTTP_STATUS_MESSAGES[status] || ERROR_MESSAGES[type]

  return new ApiError(message, data?.code || null, status, data, type)
}

export const wrapApiCall = async (fn, _context = 'API') => {
  try {
    return await fn()
  } catch (error) {
    const handledError = handleApiError(error, true)
    throw handledError
  }
}

export function withRetry(fn, options = {}) {
  const {
    maxRetries = 3,
    shouldRetry = isRetryableError,
    getDelay = getRetryDelay,
    onRetry = () => {}
  } = options

  return async (...args) => {
    let lastError

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn(...args)
      } catch (error) {
        lastError = error

        if (attempt === maxRetries || !shouldRetry(error)) {
          throw error
        }

        const delay = getDelay(error)
        onRetry(attempt + 1, error, delay)

        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }

    throw lastError
  }
}

export default {
  ApiError,
  ERROR_MESSAGES,
  HTTP_STATUS_MESSAGES,
  handleApiError,
  normalizeError,
  getDisplayMessage,
  isRetryableError,
  getRetryDelay,
  createErrorFromResponse,
  wrapApiCall,
  withRetry
}
