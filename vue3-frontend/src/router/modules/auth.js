import { ROUTE_NAMES } from '../constants'

export default [
  {
    path: '/login',
    name: ROUTE_NAMES.LOGIN,
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: ROUTE_NAMES.REGISTER,
    component: () => import('@/views/auth/Register.vue'),
    meta: {
      title: '注册',
      requiresAuth: false
    }
  },
  {
    path: '/forgot-password',
    name: ROUTE_NAMES.FORGOT_PASSWORD,
    component: () => import('@/views/auth/ForgotPassword.vue'),
    meta: {
      title: '重置密码',
      requiresAuth: false
    }
  },
  {
    path: '/profile',
    name: ROUTE_NAMES.PROFILE,
    component: () => import('@/views/auth/Profile.vue'),
    meta: {
      title: '个人信息',
      requiresAuth: true
    }
  }
]
