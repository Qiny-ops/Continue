import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/modules/user'
import { setupPermissionDirectives } from './directives/permission'
import { setTokenGetter, setOnAuthError } from './api/axios'

// 引入全局样式
import './styles/variables.css'
import './styles/common.css'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

setTokenGetter(() => useUserStore().token)
setOnAuthError(() => useUserStore().reset())

setupPermissionDirectives(app)

app.provide('locale', zhCn)

app.mount('#app')
