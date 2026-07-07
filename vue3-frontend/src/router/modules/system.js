import { ROUTE_NAMES } from '../constants'

export default [
  {
    path: '/system',
    name: 'system',
    redirect: '/system/users',
    meta: {
      title: '系统管理',
      requiresAuth: true
    }
  },
  {
    path: '/system/users',
    name: ROUTE_NAMES.SYSTEM_USERS,
    component: () => import('@/views/system/User.vue'),
    meta: {
      title: '用户管理',
      requiresAuth: true,
      roles: ['admin']
    }
  },
  {
    path: '/system/roles',
    name: ROUTE_NAMES.SYSTEM_ROLES,
    component: () => import('@/views/system/Role.vue'),
    meta: {
      title: '角色管理',
      requiresAuth: true,
      roles: ['admin']
    }
  },
  {
    path: '/system/permissions',
    name: ROUTE_NAMES.SYSTEM_PERMISSIONS,
    component: () => import('@/views/system/Permission.vue'),
    meta: {
      title: '权限管理',
      requiresAuth: true,
      roles: ['admin']
    }
  },
  {
    path: '/system/permission-matrix',
    name: 'permission-matrix',
    component: () => import('@/views/system/PermissionMatrix.vue'),
    meta: {
      title: '权限矩阵',
      requiresAuth: true,
      roles: ['admin']
    }
  }
]
