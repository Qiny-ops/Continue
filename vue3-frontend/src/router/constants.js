export const ROUTE_NAMES = {
  LOGIN: 'login',
  REGISTER: 'register',
  FORGOT_PASSWORD: 'forgotPassword',
  PROFILE: 'profile',
  PROJECTS: 'projects',
  PROJECT_CREATE: 'project-create',
  PROJECT_DETAIL: 'project-detail',
  PROJECT_OVERVIEW: 'project-overview',
  PROJECT_TESTCASES: 'project-testcases',
  PROJECT_KNOWLEDGE: 'project-knowledge',
  PROJECT_APITEST: 'project-apitest',
  PROJECT_APITEST_ENVIRONMENTS: 'project-apitest-environments',
  // PROJECT_TESTPLANS: 'project-testplans', // TODO: 待实现
  // PROJECT_BUGS: 'project-bugs', // TODO: 待实现
  // PROJECT_REPORTS: 'project-reports', // TODO: 待实现
  PROJECT_MEMBERS: 'project-members',
  PROJECT_SETTINGS: 'project-settings',
  MANAGE_REPO: 'manage-repo',
  MANAGE_VERSION: 'manage-version',
  SYSTEM_USERS: 'system-users',
  SYSTEM_ROLES: 'system-roles',
  SYSTEM_PERMISSIONS: 'system-permissions',
  NOT_FOUND: 'not-found'
}

export const SPECIAL_ROUTES = [
  'login',
  'register',
  'forgot-password',
  'reset-password',
  'profile',
  'projects',
  'system',
  'p'  // 项目详情路由前缀
]

export const WHITE_LIST = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password'
]

// 项目路由前缀
export const PROJECT_ROUTE_PREFIX = '/p'
