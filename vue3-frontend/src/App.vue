<!-- 主应用组件 -->
<template>
  <el-config-provider :locale="locale">
    <div id="app">
      <!-- 初始化加载状态 -->
      <div v-if="!isReady" class="app-loading">
        <div class="loading-spinner"></div>
      </div>

      <template v-else>
        <!-- 登录、注册等认证页面不使用布局 -->
        <router-view v-if="isAuthRoute" />

        <!-- 主应用使用布局 -->
        <MainLayout v-else>
          <router-view v-slot="{ Component }">
            <keep-alive :include="cachedRoutes">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </MainLayout>
      </template>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed, inject, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const router = useRouter()
const locale = inject('locale')

const isReady = ref(false)

const isAuthRoute = computed(() => {
  if (!route.matched.length) return false

  const meta = route.meta
  if (meta.requiresAuth === false) return true

  const standaloneRoutes = ['/demo/', '/login', '/register', '/forgot-password']
  return standaloneRoutes.some(prefix => route.path.startsWith(prefix))
})

const cachedRoutes = computed(() => {
  return route.matched
    .filter(r => r.meta.keepAlive)
    .map(r => r.name?.toString() || '')
    .filter(Boolean)
})

onMounted(async () => {
  await router.isReady()
  isReady.value = true
})
</script>

<style>
#app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: var(--color-bg-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-primary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  overflow-x: hidden;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-tertiary);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb {
  background: var(--color-text-placeholder);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* 深色主题 */
html.dark {
  color-scheme: dark;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
