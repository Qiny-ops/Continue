<!-- 注册页面组件 -->
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

      <!-- 注册表单 -->
      <form class="auth-form" @submit.prevent="handleRegister">
        <h2 class="form-heading">创建账户</h2>

        <!-- 用户名 -->
        <div class="form-group">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            autocomplete="username"
            :prefix-icon="User"
          />
        </div>

        <!-- 邮箱 -->
        <div class="form-group">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="邮箱"
            autocomplete="email"
            :prefix-icon="Message"
          />
        </div>

        <!-- 密码 -->
        <div class="form-group">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            autocomplete="new-password"
            :prefix-icon="Lock"
            show-password
          />
        </div>

        <!-- 确认密码 -->
        <div class="form-group">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            autocomplete="new-password"
            :prefix-icon="Check"
            show-password
          />
        </div>

        <!-- 注册按钮 -->
        <el-button
          type="primary"
          native-type="submit"
          class="submit-btn"
          :loading="loading"
          :icon="loading ? Loading : ArrowRight"
        >
          {{ loading ? '注册中...' : '注册' }}
        </el-button>

        <!-- 登录入口 -->
        <p class="login-text">
          已有账户？<router-link to="/login" class="login-link">立即登录</router-link>
        </p>
      </form>

      <!-- 页脚 -->
      <div class="auth-footer">
        <span>注册即表示同意</span>
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
import { User, Lock, Message, Check, Loading, ArrowRight } from '@element-plus/icons-vue';
import authApi from '@/api/modules/auth';

// 路由实例
const router = useRouter();

// 表单数据
const form = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

// 状态管理
const loading = ref(false);

// 注册处理
const handleRegister = async () => {
  // 表单验证
  if (!form.value.username) {
    ElMessage({
      message: '请输入用户名',
      type: 'error',
      center: true
    });
    return;
  }

  if (!form.value.email) {
    ElMessage({
      message: '请输入邮箱',
      type: 'error',
      center: true
    });
    return;
  }

  if (!form.value.password) {
    ElMessage({
      message: '请输入密码',
      type: 'error',
      center: true
    });
    return;
  }

  if (form.value.password !== form.value.confirmPassword) {
    ElMessage({
      message: '两次输入的密码不一致',
      type: 'error',
      center: true
    });
    return;
  }

  loading.value = true;

  try {
    // 调用注册API
    const response = await authApi.register(form.value);

    // 检查响应数据
    if (response.code === 200 && response.data) {
      // 显示成功消息
      ElMessage({
        message: '注册成功，请登录',
        type: 'success',
        center: true
      });

      // 跳转到登录页
      router.push('/login');
    } else {
      ElMessage({
        message: '注册失败，请稍后重试',
        type: 'error',
        center: true
      });
    }
  } catch {
    ElMessage({
      message: '注册失败，请稍后重试',
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
