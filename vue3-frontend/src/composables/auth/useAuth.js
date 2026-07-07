import { ref } from 'vue'
import { useUserStore } from '@/stores/modules/user'
import router from '@/router'

export function useAuth() {
  const userStore = useUserStore()
  const error = ref(null)
  const isLoading = ref(false)

  const login = async (credentials) => {
    try {
      isLoading.value = true
      error.value = null
      await userStore.login(credentials)
      router.push('/')
    } catch (err) {
      error.value = err.message || '登录失败'
    } finally {
      isLoading.value = false
    }
  }

  return {
    error,
    isLoading,
    login
  }
}