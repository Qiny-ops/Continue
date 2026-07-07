// ==================== 项目权限 ====================
// 与后端 Testbackend/apps/core/permissions.py PROJECT_PERMISSIONS 保持一致

export const PERMISSIONS = {
  PROJECT_MANAGE: 'project_manage',
  MEMBER_MANAGE: 'member_manage',
  TESTCASE_MANAGE: 'testcase_manage',
  TESTCASE_VIEW: 'testcase_view',
  APITEST_MANAGE: 'apitest_manage',
  APITEST_VIEW: 'apitest_view',
  APITEST_EXECUTE: 'apitest_execute',
  KNOWLEDGE_MANAGE: 'knowledge_manage',
  KNOWLEDGE_VIEW: 'knowledge_view',
  TEST_EXECUTE: 'test_execute',
  REPORT_VIEW: 'report_view',
  SETTINGS_MANAGE: 'settings_manage'
}

export const PERMISSION_NAMES = {
  [PERMISSIONS.PROJECT_MANAGE]: '项目管理',
  [PERMISSIONS.MEMBER_MANAGE]: '成员管理',
  [PERMISSIONS.TESTCASE_MANAGE]: '测试用例管理',
  [PERMISSIONS.TESTCASE_VIEW]: '测试用例查看',
  [PERMISSIONS.APITEST_MANAGE]: '接口测试管理',
  [PERMISSIONS.APITEST_VIEW]: '接口测试查看',
  [PERMISSIONS.APITEST_EXECUTE]: '接口测试执行',
  [PERMISSIONS.KNOWLEDGE_MANAGE]: '知识库管理',
  [PERMISSIONS.KNOWLEDGE_VIEW]: '知识库查看',
  [PERMISSIONS.TEST_EXECUTE]: '测试执行',
  [PERMISSIONS.REPORT_VIEW]: '报告查看',
  [PERMISSIONS.SETTINGS_MANAGE]: '设置管理'
}

// ==================== 系统权限 ====================
// 与后端 Testbackend/apps/core/permissions.py SYSTEM_PERMISSIONS 保持一致

export const SYSTEM_PERMISSIONS = {
  SYSTEM_ADMIN: 'system_admin',
  SYSTEM_SETTINGS: 'system_settings',
  USER_MANAGE: 'user_manage',
  USER_VIEW: 'user_view',
  ROLE_MANAGE: 'role_manage',
  ROLE_VIEW: 'role_view',
  PROJECT_CREATE: 'project_create',
  PROJECT_VIEW_ALL: 'project_view_all',
  PROJECT_DELETE_ANY: 'project_delete_any',
  REPORT_GLOBAL: 'report_global',
  REPORT_EXPORT: 'report_export',
}

export const SYSTEM_PERMISSION_NAMES = {
  [SYSTEM_PERMISSIONS.SYSTEM_ADMIN]: '系统管理',
  [SYSTEM_PERMISSIONS.SYSTEM_SETTINGS]: '系统设置',
  [SYSTEM_PERMISSIONS.USER_MANAGE]: '用户管理',
  [SYSTEM_PERMISSIONS.USER_VIEW]: '用户查看',
  [SYSTEM_PERMISSIONS.ROLE_MANAGE]: '角色管理',
  [SYSTEM_PERMISSIONS.ROLE_VIEW]: '角色查看',
  [SYSTEM_PERMISSIONS.PROJECT_CREATE]: '创建项目',
  [SYSTEM_PERMISSIONS.PROJECT_VIEW_ALL]: '查看所有项目',
  [SYSTEM_PERMISSIONS.PROJECT_DELETE_ANY]: '删除任意项目',
  [SYSTEM_PERMISSIONS.REPORT_GLOBAL]: '全局报表',
  [SYSTEM_PERMISSIONS.REPORT_EXPORT]: '报表导出',
}

// ==================== 角色相关 ====================

export const ROLE_KEYS = {
  ADMIN: 'admin',
  DEVELOPER: 'developer',
  TESTER: 'tester',
  VIEWER: 'viewer'
}

export const ROLE_NAMES = {
  [ROLE_KEYS.ADMIN]: '管理员',
  [ROLE_KEYS.DEVELOPER]: '开发人员',
  [ROLE_KEYS.TESTER]: '测试人员',
  [ROLE_KEYS.VIEWER]: '观察者'
}

export const ROLE_COLORS = {
  admin: '#ef4444',
  developer: '#3b82f6',
  tester: '#22c55e',
  viewer: '#6b7280',
  [ROLE_KEYS.ADMIN]: '#ef4444',
  [ROLE_KEYS.DEVELOPER]: '#3b82f6',
  [ROLE_KEYS.TESTER]: '#22c55e',
  [ROLE_KEYS.VIEWER]: '#6b7280'
}

// 系统角色默认权限映射（与后端 SYSTEM_ROLE_DEFAULTS 一致）
export const SYSTEM_ROLE_DEFAULTS = {
  admin: Object.values(SYSTEM_PERMISSIONS), // 系统管理员拥有所有系统权限
  user: [SYSTEM_PERMISSIONS.PROJECT_CREATE], // 普通用户只能创建项目
}

// 项目角色默认权限映射（与后端 get_default_permissions 一致）
// admin 拥有所有项目权限
export const DEFAULT_ROLE_PERMISSIONS = {
  [ROLE_KEYS.ADMIN]: Object.values(PERMISSIONS),
  [ROLE_KEYS.DEVELOPER]: [
    PERMISSIONS.TESTCASE_VIEW,
    PERMISSIONS.APITEST_VIEW,
    PERMISSIONS.APITEST_EXECUTE,
    PERMISSIONS.KNOWLEDGE_VIEW,
    PERMISSIONS.REPORT_VIEW
  ],
  [ROLE_KEYS.TESTER]: [
    PERMISSIONS.TESTCASE_MANAGE,
    PERMISSIONS.TESTCASE_VIEW,
    PERMISSIONS.TEST_EXECUTE,
    PERMISSIONS.APITEST_EXECUTE,
    PERMISSIONS.KNOWLEDGE_VIEW,
    PERMISSIONS.REPORT_VIEW
  ],
  [ROLE_KEYS.VIEWER]: [
    PERMISSIONS.TESTCASE_VIEW,
    PERMISSIONS.KNOWLEDGE_VIEW,
    PERMISSIONS.REPORT_VIEW
  ]
}

export const SYSTEM_ROLES = {
  ADMIN: 'admin'
}
