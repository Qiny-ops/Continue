const getAvatarUrl = (avatar) => {
  if (!avatar) return ''
  if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
    return avatar
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  let path = avatar
  if (!path.startsWith('/media/')) {
    path = `/media${path.startsWith('/') ? '' : '/'}${path}`
  }
  return `${baseUrl}${path}`
}

export { getAvatarUrl }
