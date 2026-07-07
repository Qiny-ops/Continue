<!-- 忘记密码页面组件 -->
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

      <!-- 忘记密码表单 -->
      <form class="auth-form" @submit.prevent="handleForgotPassword">
        <h2 class="form-heading">重置密码</h2>
        <p class="form-subheading">请输入您的邮箱地址，我们将发送重置密码的链接</p>

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

        <!-- 重置密码按钮 -->
        <el-button
          type="primary"
          native-type="submit"
          class="submit-btn"
          :loading="loading"
          :icon="loading ? Loading : Promotion"
        >
          {{ loading ? '发送中...' : '发送重置链接' }}
        </el-button>

        <!-- 登录入口 -->
        <p class="login-text">
          想起密码了？<router-link to="/login" class="login-link">立即登录</router-link>
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
import { Message, Loading, Promotion } from '@element-plus/icons-vue';
import authApi from '@/api/modules/auth';

// 路由实例
const router = useRouter();

// 表单数据
const form = ref({
  email: ''
});

// 状态管理
const loading = ref(false);

// 忘记密码处理
const handleForgotPassword = async () => {
  // 表单验证
  if (!form.value.email) {
    ElMessage({
      message: '请输入邮箱地址',
      type: 'error',
      center: true
    });
    return;
  }

  loading.value = true;

  try {
    // 调用忘记密码API
    const response = await authApi.forgotPassword(form.value);

    // 检查响应数据
    if (response.code === 200) {
      // 显示成功消息
      ElMessage({
        message: '重置链接已发送，请查收邮箱',
        type: 'success',
        center: true
      });

      // 跳转到登录页
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } else {
      ElMessage({
        message: '发送失败，请稍后重试',
        type: 'error',
        center: true
      });
    }
  } catch {
    ElMessage({
      message: '发送失败，请稍后重试',
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
