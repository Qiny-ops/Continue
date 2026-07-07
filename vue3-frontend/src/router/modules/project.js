import { ROUTE_NAMES } from '../constants'

export default [
  {
    path: '/projects',
    name: ROUTE_NAMES.PROJECTS,
    component: () => import('@/views/projects/List.vue'),
    meta: {
      title: '项目管理',
      requiresAuth: true,
      keepAlive: true,
      module: 'projects'
    }
  },

  {
    path: '/projects/create',
    name: ROUTE_NAMES.PROJECT_CREATE,
    component: () => import('@/views/projects/Create.vue'),
    meta: {
      title: '创建项目',
      requiresAuth: true,
      keepAlive: true,
      module: 'projects'
    }
  },

  {
    path: '/p/:code/',
    name: ROUTE_NAMES.PROJECT_DETAIL,
    component: () => import('@/views/projects/Detail.vue'),
    props: true,
    meta: {
      title: '项目详情',
      requiresAuth: true,
      keepAlive: true,
      module: 'projects'
    },
    children: [
      {
        path: '',
        name: ROUTE_NAMES.PROJECT_OVERVIEW,
        component: () => import('@/views/projects/components/ProjectOverview.vue'),
        meta: {
          title: '项目概览',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 't/manage-repo',
        name: ROUTE_NAMES.MANAGE_REPO,
        component: () => import('@/views/testcase/ManageRepo.vue'),
        meta: {
          title: '管理用例库',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 't/manage-version',
        name: ROUTE_NAMES.MANAGE_VERSION,
        component: () => import('@/views/testcase/ManageVersion.vue'),
        meta: {
          title: '管理版本',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 'testcases',
        name: ROUTE_NAMES.PROJECT_TESTCASES,
        component: () => import('@/views/projects/Detail.vue'),
        meta: {
          title: '测试用例',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 'apitest',
        name: ROUTE_NAMES.PROJECT_APITEST,
        component: () => import('@/views/apitest/Index.vue'),
        meta: {
          title: '接口测试',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 'apitest/environments',
        name: ROUTE_NAMES.PROJECT_APITEST_ENVIRONMENTS,
        component: () => import('@/views/apitest/Environment.vue'),
        meta: {
          title: '测试环境',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 'knowledge',
        name: ROUTE_NAMES.PROJECT_KNOWLEDGE,
        component: () => import('@/views/knowledge/Index.vue'),
        meta: {
          title: '知识库',
          requiresAuth: true,
          keepAlive: true
        }
      },

      {
        path: 'members',
        name: ROUTE_NAMES.PROJECT_MEMBERS,
        redirect: (to) => {
          return { path: `/p/${to.params.code}/settings`, query: { tab: 'members' } }
        },
        meta: {
          title: '成员管理',
          requiresAuth: true
        }
      },

      {
        path: 'settings',
        name: ROUTE_NAMES.PROJECT_SETTINGS,
        component: () => import('@/views/projects/Detail.vue'),
        meta: {
          title: '项目设置',
          requiresAuth: true,
          keepAlive: true
        }
      }
    ]
  }
]
