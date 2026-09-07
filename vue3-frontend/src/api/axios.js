import axios from 'axios'
import { ERROR_MESSAGES, HTTP_STATUS_MESSAGES } from './errorHandler.js'

let _getToken = null
let _onAuthError = null
let _onAuthRedirect = null
let isRedirecting = false

export function setTokenGetter(getter) {
  _getToken = getter
}

export function setOnAuthError(handler) {
  _onAuthError = handler
}

export function setOnAuthRedirect(handler) {
  _onAuthRedirect = handler
}

export function getToken() {
  return _getToken ? _getToken() : null
}

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  (config) => {
    if (_getToken) {
      const token = _getToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    const normalizedError = createNormalizedError(error, 'REQUEST_ERROR', '请求发送失败')
    return Promise.reject(normalizedError)
  }
)

function getErrorType(status) {
  const typeMap = {
    400: 'CLIENT_ERROR',
    401: 'AUTH_ERROR',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    405: 'CLIENT_ERROR',
    408: 'TIMEOUT',
    409: 'CLIENT_ERROR',
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

function getErrorMessage(status, data) {
  if (data && data.message) {
    return data.message
  }

  if (HTTP_STATUS_MESSAGES[status]) {
    return HTTP_STATUS_MESSAGES[status]
  }

  if (status >= 500) {
    return ERROR_MESSAGES.SERVER_ERROR
  }

  return ERROR_MESSAGES.CLIENT_ERROR
}

function createNormalizedError(originalError, type, message, status = null, data = null) {
  return {
    type,
    message,
    status,
    data,
    originalError,
    timestamp: new Date().toISOString()
  }
}

instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const normalizedError = createNormalizedError(
        error,
        'TIMEOUT',
        ERROR_MESSAGES.TIMEOUT,
        null,
        null
      )
      return Promise.reject(normalizedError)
    }

    if (!error.response && error.request) {
      if (error.message === 'Network Error') {
        const normalizedError = createNormalizedError(
          error,
          'NETWORK_ERROR',
          ERROR_MESSAGES.NETWORK_ERROR,
          null,
          null
        )
        return Promise.reject(normalizedError)
      }

      const normalizedError = createNormalizedError(
        error,
        'NO_RESPONSE',
        ERROR_MESSAGES.NO_RESPONSE,
        null,
        null
      )
      return Promise.reject(normalizedError)
    }

    if (error.response) {
      const { status, data } = error.response
      const type = getErrorType(status)
      let message = getErrorMessage(status, data)

      if (status === 401) {
        if (!isRedirecting) {
          isRedirecting = true
          if (_getToken) {
            const token = _getToken()
            if (token) {
              if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                // 通过回调统一清理状态，避免直接操作 localStorage
                if (_onAuthError) {
                  _onAuthError()
                } else {
                  localStorage.removeItem('user-store')
                }
                // 使用回调跳转（router.push 代替整页刷新 window.location.href）
                if (_onAuthRedirect) {
                  _onAuthRedirect('/login')
                } else {
                  window.location.href = '/login'
                }
              }
            }
          }
          setTimeout(() => {
            isRedirecting = false
          }, 1000)
        }
      }

      if (status === 429) {
        const retryAfter = error.response.headers['retry-after']
        if (retryAfter) {
          message = `请求过于频繁，请在 ${retryAfter} 秒后重试`
          data.retryAfter = parseInt(retryAfter, 10)
        }
      }

      const normalizedError = createNormalizedError(error, type, message, status, data)
      return Promise.reject(normalizedError)
    }

    const normalizedError = createNormalizedError(
      error,
      'UNKNOWN',
      error.message || ERROR_MESSAGES.UNKNOWN,
      null,
      null
    )
    return Promise.reject(normalizedError)
  }
)

export default instance
