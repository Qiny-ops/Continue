<template>
  <div class="not-found-page">
    <div class="not-found-container">
      <!-- 404数字 -->
      <div class="error-code">404</div>

      <!-- 描述信息 -->
      <h2 class="error-title">页面不存在</h2>
      <p class="error-message">您访问的页面可能已被移除、名称已更改或暂时不可用</p>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="goHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <el-icon><Back /></el-icon>
          返回上页
        </el-button>
      </div>

      <!-- 快捷入口 -->
      <div class="quick-links">
        <span class="quick-label">您也可以尝试：</span>
        <router-link to="/projects">项目列表</router-link>
        <router-link to="/knowledge">知识库</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { HomeFilled, Back } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/projects')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.not-found-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  padding: 24px;
}

.not-found-container {
  text-align: center;
  max-width: 480px;
}

.error-code {
  font-size: 96px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: 24px;
  letter-spacing: -2px;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 12px;
}

.error-message {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 32px;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 24px;
}

.action-buttons .el-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.quick-links {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.quick-label {
  margin-right: 8px;
}

.quick-links a {
  color: var(--color-primary);
  text-decoration: none;
  margin-right: 16px;
}

.quick-links a:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .error-code {
    font-size: 72px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>