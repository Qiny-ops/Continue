<!-- 登录页面组件 -->
<template>
  <div class="auth-page">
    <!-- 装饰性几何图形 -->
    <div class="decor-shape shape-1"></div>
    <div class="decor-shape shape-2"></div>
    <div class="decor-shape shape-3"></div>

    <div class="auth-container">
      <!-- Logo区域 -->
      <div class="auth-header">
        <a href="/" class="logo-link">
          <img
            src="/logo.png"
            alt="TestFlow Logo"
            class="logo-image"
          />
        </a>
      </div>

      <!-- 登录表单 -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <h2 class="form-heading">登录账户</h2>

        <!-- 用户名/邮箱 -->
        <div class="form-group">
          <el-input
            v-model="form.username"
            placeholder="用户名或邮箱"
            autocomplete="username"
            :prefix-icon="User"
          />
        </div>

        <!-- 密码 -->
        <div class="form-group">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            autocomplete="current-password"
            :prefix-icon="Lock"
            show-password
          />
        </div>

        <!-- 记住我 -->
        <div class="remember-section">
          <el-checkbox v-model="form.remember">30天内免登录</el-checkbox>
          <router-link to="/forgot-password" class="forgot-link">重置密码</router-link>
        </div>


        <!-- 登录按钮 -->
        <el-button
          type="primary"
          native-type="submit"
          class="submit-btn"
          :loading="loading"
          :icon="loading ? Loading : ArrowRight"
        >
          {{ loading ? '登录中...' : '登录' }}
        </el-button>

        <!-- 注册入口 -->
        <p class="signup-text">
          还没有账户？<router-link to="/register" class="signup-link">免费注册</router-link>
        </p>
      </form>

      <!-- 页脚 -->
      <div class="auth-footer">
        <span>登录即表示同意</span>
        <a href="#">服务条款</a>
        <span>和</span>
        <a href="#">隐私政策</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { User, Lock, Loading, ArrowRight } from '@element-plus/icons-vue';
import { useUserStore } from '@/stores/modules/user';

const router = useRouter();
const userStore = useUserStore();

// 表单数据
const form = ref({
  username: '',
  password: '',
  remember: false
});

// 状态管理
const loading = ref(false);

// 登录处理
const handleLogin = async () => {
  loading.value = true;

  try {
    const loginData = await userStore.login(form.value);
    
    if (!loginData?.id && !loginData?.username) {
      await userStore.fetchUserInfo();
    }

    ElMessage({
      message: '登录成功',
      type: 'success',
      center: true
    });

    router.push('/projects');
  } catch {
    ElMessage({
      message: '登录失败，请检查用户名和密码',
      type: 'error',
      center: true
    });
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
@import '@/styles/auth.css';
</style>
