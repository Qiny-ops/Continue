<template>
  <div class="user-info" ref="containerRef">
    <div class="user-trigger" @click="toggleOpen" :class="{ 'is-open': isOpen }">
      <el-avatar
        :size="32"
        :src="userInfo.avatar"
        :icon="UserFilled"
        class="user-avatar"
      >
        {{ userInfo.initials }}
      </el-avatar>
      <span class="user-name">{{ userInfo.name }}</span>
      <el-icon class="arrow"><ArrowDown /></el-icon>
    </div>

    <Transition name="dropdown">
      <div v-if="isOpen" class="dropdown-menu">
        <div class="menu-item" @click="goTo('/profile')">
          <el-icon><User /></el-icon> 个人信息
        </div>
        <div class="menu-item" @click="goTo('/settings')">
          <el-icon><Setting /></el-icon> 账户设置
        </div>
        <div class="divider"></div>
        <div class="menu-item logout" @click="logout">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { User, Setting, SwitchButton, ArrowDown, UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/modules/user'
import { getAvatarUrl } from '@/utils/avatar'
import { storeToRefs } from 'pinia'

const router = useRouter()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const isOpen = ref(false)
const containerRef = ref(null)

const userInfo = computed(() => {
  const u = user.value || {}
  const name = u.name || u.username || '用户'
  return {
    name,
    avatar: getAvatarUrl(u.avatar),
    initials: name.charAt(0).toUpperCase()
  }
})

const toggleOpen = () => isOpen.value = !isOpen.value
const close = () => isOpen.value = false

const goTo = (path) => {
  close()
  router.push(path)
}

const logout = async () => {
  close()
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
    await userStore.logout()
    router.replace('/login')
  } catch {
    // 用户取消操作
  }
}

const onClickOutside = (e) => {
  if (containerRef.value && !containerRef.value.contains(e.target)) close()
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.user-info {
  position: relative;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px 4px 4px;
  border-radius: 20px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-trigger:hover,
.user-trigger.is-open {
  background: var(--color-bg-secondary);
}

.user-avatar {
  flex-shrink: 0;
  background-color: var(--el-color-primary);
  color: #fff;
  font-weight: 500;
}

.user-name {
  font-size: 14px;
  color: #333;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  font-size: 12px;
  color: #999;
  transition: transform 0.2s;
}

.user-trigger.is-open .arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  border: 1px solid var(--color-border-primary);
  min-width: 140px;
  padding: 4px 0;
  z-index: 100;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.menu-item:hover {
  background: var(--color-bg-secondary);
  color: var(--color-primary);
}

.menu-item.logout {
  color: var(--color-danger);
}

.menu-item.logout:hover {
  background: var(--color-danger-light);
}

.divider {
  height: 1px;
  background: var(--color-border-primary);
  margin: 4px 0;
}
</style>
