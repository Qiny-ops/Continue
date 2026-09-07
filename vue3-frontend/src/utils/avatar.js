/**
 * 根据头像相对路径生成完整 URL，用于 media 资源（不走 /api 前缀）
 * 从 VITE_API_BASE_URL（通常为 http://host:8000/api）推导根 URL
 */
const getAvatarUrl = (avatar) => {
  if (!avatar) return ''
  if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
    return avatar
  }
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  const baseUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  let path = avatar
  if (!path.startsWith('/media/')) {
    path = `/media${path.startsWith('/') ? '' : '/'}${path}`
  }
  return `${baseUrl}${path}`
}

export { getAvatarUrl }
